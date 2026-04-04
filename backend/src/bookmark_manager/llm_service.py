import json
import logging
import re

import httpx
from openai import AsyncOpenAI

from bookmark_manager.settings import settings

logger = logging.getLogger(__name__)


async def fetch_page_metadata(url: str) -> dict:
    """Fetch basic metadata from a web page."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
            response.raise_for_status()
            content = response.text

            metadata: dict = {"url": url, "content": ""}

            title_match = re.search(
                r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']*)["\']',
                content,
            )
            desc_match = re.search(
                r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']',
                content,
            )
            image_match = re.search(
                r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']*)["\']',
                content,
            )

            if title_match:
                metadata["og_title"] = title_match.group(1)
            if desc_match:
                metadata["og_description"] = desc_match.group(1)
            if image_match:
                metadata["og_image"] = image_match.group(1)

            # Extract title tag
            title_tag = re.search(
                r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL
            )
            if title_tag:
                metadata["title"] = title_tag.group(1).strip()

            # Get first 3000 chars of text content for analysis
            text_content = re.sub(r'<[^>]+>', ' ', content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            metadata["content"] = text_content[:3000]

            return metadata
    except Exception as e:
        logger.error(f"Error fetching page {url}: {e}")
        return {"url": url, "content": "", "title": "", "og_description": ""}


async def analyze_with_llm(metadata: dict) -> dict:
    """Analyze page content using LLM via qwen-code-api OpenAI-compatible endpoint."""
    client = AsyncOpenAI(
        api_key=settings.llm_api_key or "not-needed",
        base_url=settings.llm_api_base_url,
    )

    content_summary = metadata.get("content", "") or metadata.get("og_description", "") or "No content available"
    title = metadata.get("og_title", "") or metadata.get("title", "") or metadata.get("url", "")

    prompt = f"""Analyze this web page content and return a JSON object with the following structure:
{{
  "title": "concise title of the page",
  "summary": "2-3 sentence summary of the content",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "category": "one of: tech, science, education, entertainment, news, business, health, sports, other"
}}

Page Title: {title}
Content: {content_summary[:2000]}
URL: {metadata.get('url', '')}

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

        # Remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
        if content.endswith("```"):
            content = content.rsplit("\n", 1)[0]
        content = content.strip()

        result = json.loads(content)

        # Validate structure
        required_keys = ["title", "summary", "tags", "category"]
        for key in required_keys:
            if key not in result:
                raise ValueError(f"Missing key in LLM response: {key}")

        # Ensure tags is a list
        if isinstance(result["tags"], str):
            result["tags"] = [t.strip() for t in result["tags"].split(",")]

        # Limit to 5 tags
        result["tags"] = result["tags"][:5]

        return result

    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        # Fallback: return basic info from metadata
        return {
            "title": metadata.get("title", "") or metadata.get("og_title", "") or metadata.get("url", "Untitled"),
            "summary": metadata.get("og_description", "") or "Content analysis unavailable",
            "tags": ["uncategorized"],
            "category": "other",
        }
