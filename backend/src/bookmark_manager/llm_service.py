import json
import logging
import re

import httpx
from openai import AsyncOpenAI

from bookmark_manager.settings import settings

logger = logging.getLogger(__name__)


async def generate_embedding(text: str) -> list[float] | None:
    """Generate embedding for text using OpenAI-compatible API."""
    client = AsyncOpenAI(
        api_key=settings.llm_api_key or "not-needed",
        base_url=settings.llm_api_base_url,
    )

    try:
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        return None


async def fetch_page_metadata(url: str) -> dict:
    """Fetch basic metadata from a web page."""
    try:
        async with httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=True,
            verify=False,
        ) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()
            content = response.text

            metadata: dict = {
                "url": url,
                "title": "",
                "headings": [],
                "text": "",
                "images": [],
                "videos": [],
            }

            title_tag = re.search(
                r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL
            )
            if title_tag:
                metadata["title"] = title_tag.group(1).strip()

            headings = []
            for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                pattern = rf"<{tag}[^>]*>(.*?)</{tag}>"
                for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                    heading_text = re.sub(r"<[^>]+>", " ", match.group(1))
                    heading_text = re.sub(r"\s+", " ", heading_text).strip()
                    if heading_text:
                        headings.append(heading_text)
            metadata["headings"] = headings[:20]

            text_only = re.sub(
                r"<script[^>]*>.*?</script>",
                "",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            text_only = re.sub(
                r"<style[^>]*>.*?</style>",
                "",
                text_only,
                flags=re.IGNORECASE | re.DOTALL,
            )
            text_only = re.sub(r"<[^>]+>", " ", text_only)
            text_only = re.sub(r"\s+", " ", text_only).strip()
            metadata["text"] = text_only[:8000]

            image_urls = []
            for match in re.finditer(
                r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE
            ):
                src = match.group(1)
                if src and not src.startswith("data:"):
                    image_urls.append(src)
            for match in re.finditer(
                r'<img[^>]+srcset=["\']([^"\']+)["\']', content, re.IGNORECASE
            ):
                srcset = match.group(1)
                first_src = srcset.split()[0] if srcset.split() else None
                if first_src and not first_src.startswith("data:"):
                    image_urls.append(first_src)
            metadata["images"] = image_urls[:10]

            video_urls = []
            for match in re.finditer(
                r'<video[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE
            ):
                src = match.group(1)
                if src:
                    video_urls.append(src)
            for match in re.finditer(
                r'<source[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE
            ):
                src = match.group(1)
                if src and any(ext in src for ext in [".mp4", ".webm", ".ogg"]):
                    video_urls.append(src)
            for match in re.finditer(
                r'<iframe[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE
            ):
                src = match.group(1)
                if src and ("youtube" in src or "vimeo" in src or "player" in src):
                    video_urls.append(src)
            metadata["videos"] = video_urls[:5]

            return metadata
    except Exception as e:
        logger.error(f"Error fetching page {url}: {e}")
        return {
            "url": url,
            "title": "",
            "headings": [],
            "text": "",
            "images": [],
            "videos": [],
        }


async def search_bookmarks_with_llm(search_query: str, bookmarks: list[dict]) -> list[int]:
    """Use LLM to determine which bookmarks are relevant to the search query.
    
    Args:
        search_query: The user's natural language search query
        bookmarks: List of bookmark dicts with keys: id, url, title, summary, categories
    
    Returns:
        List of bookmark IDs that the LLM determines are relevant to the search query
    """
    logger.info(f"LLM search for query: {search_query}")
    
    client = AsyncOpenAI(
        api_key=settings.llm_api_key or "not-needed",
        base_url=settings.llm_api_base_url,
    )
    
    # Format bookmarks for the prompt
    bookmarks_text = ""
    for i, bm in enumerate(bookmarks):
        categories_str = ", ".join(bm.get("categories", [])) if bm.get("categories") else "No categories"
        bookmarks_text += f"""Bookmark ID: {bm['id']}
Title: {bm.get('title', 'Untitled')}
URL: {bm.get('url', '')}
Summary: {bm.get('summary', 'No summary')}
Categories: {categories_str}
---
"""
    
    prompt = f"""You are a smart bookmark manager assistant. A user has searched for something, and you need to select which of their bookmarks are relevant to this search.

SEARCH QUERY: "{search_query}"

USER'S BOOKMARKS:
{bookmarks_text}

INSTRUCTIONS:
1. Analyze the search query and all bookmarks carefully.
2. Consider the title, summary, categories, and URL of each bookmark.
3. Select ONLY the bookmarks that are truly relevant to the search query.
4. Return EXACTLY this JSON structure (no other text, no markdown):
{{
  "relevant_bookmark_ids": [list of bookmark IDs that are relevant]
}}

IMPORTANT:
- Return ONLY valid JSON with the key "relevant_bookmark_ids"
- The value must be a list of integers (bookmark IDs)
- If no bookmarks are relevant, return an empty list: []
- Do NOT include bookmark IDs that don't exist in the provided list
- Be selective - only include genuinely relevant bookmarks

Return ONLY the JSON, no markdown formatting or explanation."""

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        logger.info(f"LLM search response: {content[:300]}")
        
        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        content = content.strip()
        
        result = json.loads(content)
        
        # Validate structure
        if "relevant_bookmark_ids" not in result:
            raise ValueError("Missing 'relevant_bookmark_ids' in response")
        
        bookmark_ids = result["relevant_bookmark_ids"]
        if not isinstance(bookmark_ids, list):
            raise ValueError("'relevant_bookmark_ids' must be a list")
        
        # Ensure all IDs are integers
        bookmark_ids = [int(id) for id in bookmark_ids]
        
        logger.info(f"LLM selected {len(bookmark_ids)} bookmarks for query: {search_query}")
        
        return bookmark_ids
        
    except Exception as e:
        logger.error(f"LLM search failed: {e}")
        raise


async def analyze_with_llm(metadata: dict) -> dict:
    """Analyze page content using LLM via qwen-code-api OpenAI-compatible endpoint."""
    logger.info(f"Analyzing URL: {metadata.get('url', '')}")

    client = AsyncOpenAI(
        api_key=settings.llm_api_key or "not-needed",
        base_url=settings.llm_api_base_url,
    )

    logger.info(f"Calling LLM with model: {settings.llm_model}")

    title = metadata.get("title", "") or metadata.get("url", "")
    text = metadata.get("text", "") or "No content available"
    headings = metadata.get("headings", [])
    images = metadata.get("images", [])
    videos = metadata.get("videos", [])

    headings_text = (
        "\n".join([f"- {h}" for h in headings]) if headings else "No headings found"
    )
    images_text = "\n".join(images) if images else "No images found"
    videos_text = "\n".join(videos) if videos else "No videos found"

    prompt = f"""Analyze this web page thoroughly and return EXACTLY this JSON structure (no other text):
{{
  "title": "short title",
  "summary": "2-3 sentence summary",
  "categories": ["category1", "category2", "category3", "category4", "category5"]
}}

IMPORTANT: You are analyzing this page exactly as a regular human user would see it. A regular user sees:
1. The visible TEXT content on the page
2. The IMAGES displayed on the page (the image URLs shown below)
3. The VIDEOS displayed on the page (the video URLs shown below)

Your categories MUST be based on what a regular user would perceive - the text, images, AND videos that are visible on this page. Consider all three types of content when deciding categories.

IMPORTANT for categories: You MUST return 1-5 specific, meaningful categories based on the ACTUAL content visible to a user (text, images, videos). You may use ANY appropriate categories not just the examples given. Do NOT use broad/generic categories like "General", "Other", "Technology", "Web", "Internet", "Information". Instead, use specific topics like: "Python Programming", "Machine Learning", "React Hooks", "API Development", "Database Design", "DevOps", "Cloud Computing", "JavaScript Frameworks", "Data Science", "Open Source", "Version Control", "Software Architecture", "Frontend Development", "Backend Development", "System Design", "Security", "Performance Optimization", etc. Each category should be a distinct, descriptive term that specifically relates to the page content.

Page Title: {title}

Headings:
{headings_text}

Content (visible text that a user would read):
{text[:6000]}

Images visible to a user (image URLs displayed on page):
{images_text}

Videos visible to a user (video URLs displayed on page):
{videos_text}

URL: {metadata.get("url", "")}

Return ONLY valid JSON, no markdown formatting."""

    try:
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")

        logger.info(f"LLM response for {metadata.get('url', '')}: {content[:300]}")

        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        content = content.strip()

        result = json.loads(content)

        # Validate structure
        required_keys = ["title", "summary", "categories"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing key in LLM response: {key}")

        # Handle categories (1-5 required)
        categories = result.get("categories", [])
        if isinstance(categories, str):
            categories = [c.strip() for c in categories.split(",")]
        categories = [
            c.strip()
            for c in categories
            if c.strip()
            and c.lower()
            not in (
                "general",
                "other",
                "uncategorized",
                "none",
                "technology",
                "web",
                "internet",
                "online",
                "resource",
            )
        ]
        # Ensure we have at least 1 category
        if len(categories) == 0:
            categories = ["Web Resource"]
        categories = categories[:5]
        result["categories"] = categories

        return result

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        url_lower = metadata.get("url", "").lower()
        fallback_categories = []

        if "python" in url_lower or "docs.python.org" in url_lower:
            fallback_categories = [
                "Python Programming",
                "Official Documentation",
                "Programming Language",
                "Educational Resource",
                "API Reference",
            ]
        elif "github" in url_lower or "gitlab" in url_lower:
            fallback_categories = [
                "Software Development",
                "Version Control",
                "Open Source",
                "Code Hosting",
                "Repository Management",
            ]
        elif "stackoverflow" in url_lower:
            fallback_categories = [
                "Programming Q&A",
                "Developer Community",
                "Technical Support",
                "Code Solutions",
                "Software Development",
            ]
        elif "medium" in url_lower or "blog" in url_lower:
            fallback_categories = [
                "Tech Blog",
                "Software Engineering",
                "Technology Article",
                "Developer Insights",
                "Programming",
            ]
        elif "news" in url_lower or "article" in url_lower:
            fallback_categories = [
                "Tech News",
                "Industry Update",
                "Software Development",
                "Technology Article",
                "Information",
            ]
        elif "youtube" in url_lower or "video" in url_lower:
            fallback_categories = [
                "Video Content",
                "Educational Video",
                "Technology",
                "Media",
                "Entertainment",
            ]
        elif "docs" in url_lower or "documentation" in url_lower:
            fallback_categories = [
                "Technical Documentation",
                "API Reference",
                "Developer Guide",
                "Software Documentation",
                "Educational Resource",
            ]
        else:
            fallback_categories = [
                "Software Development",
                "Web Resource",
                "Programming",
                "Technology",
                "Information",
            ]

        return {
            "title": metadata.get("title", "") or metadata.get("url", "Untitled"),
            "summary": metadata.get("text", "")[:200] or "Content analysis unavailable",
            "categories": fallback_categories[:5],
        }
