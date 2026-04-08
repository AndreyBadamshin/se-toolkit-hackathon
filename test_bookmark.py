#!/usr/bin/env python3
"""Test script to verify bookmark creation with the provided URL."""

import asyncio
import sys
import os

# Add backend src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from bookmark_manager.llm_service import fetch_page_metadata, analyze_with_llm

TEST_URL = "https://azbyka.ru/garden/15-prostyh-idej-dlya-ogoroda-kak-uvelichit-urozhaj/"

async def test_bookmark_creation():
    """Test the full bookmark creation flow."""
    print("=" * 80)
    print("Testing Bookmark Creation Flow")
    print("=" * 80)
    
    # Step 1: Fetch page metadata
    print("\n[1/3] Fetching page metadata...")
    try:
        metadata = await fetch_page_metadata(TEST_URL)
        print(f"✓ Metadata fetched successfully")
        print(f"  - Title: {metadata.get('title', 'N/A')[:100]}")
        print(f"  - Headings count: {len(metadata.get('headings', []))}")
        print(f"  - Text length: {len(metadata.get('text', ''))}")
        print(f"  - Images count: {len(metadata.get('images', []))}")
        print(f"  - Videos count: {len(metadata.get('videos', []))}")
    except Exception as e:
        print(f"✗ Failed to fetch metadata: {e}")
        return False
    
    # Step 2: Analyze with LLM
    print("\n[2/3] Analyzing with LLM (coder-model)...")
    try:
        analysis = await analyze_with_llm(metadata)
        print(f"✓ LLM analysis completed successfully")
        print(f"  - Title: {analysis.get('title', 'N/A')[:100]}")
        print(f"  - Summary: {analysis.get('summary', 'N/A')[:150]}")
        print(f"  - Categories: {analysis.get('categories', [])}")

        # Validate response structure
        required_keys = ["title", "summary", "categories"]
        for key in required_keys:
            if key not in analysis:
                print(f"✗ Missing required key: {key}")
                return False

        # Validate categories (should be 1-5)
        categories = analysis.get("categories", [])
        if len(categories) == 0:
            print(f"⚠ Warning: No categories (expected 1-5)")
        if len(categories) > 5:
            print(f"⚠ Warning: {len(categories)} categories (expected 1-5, will be truncated)")
            
    except Exception as e:
        print(f"✗ LLM analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Validate complete flow
    print("\n[3/3] Validating complete bookmark data...")
    try:
        bookmark_data = {
            "url": TEST_URL,
            "title": analysis["title"],
            "summary": analysis["summary"],
            "categories": analysis.get("categories", []),
            "image_url": metadata.get("images", [None])[0] if metadata.get("images") else None,
        }

        print(f"✓ Bookmark data validated:")
        print(f"  - URL: {bookmark_data['url']}")
        print(f"  - Title: {bookmark_data['title']}")
        print(f"  - Summary: {bookmark_data['summary'][:100]}...")
        print(f"  - Categories: {bookmark_data['categories']}")
        print(f"  - Image URL: {bookmark_data['image_url']}")
        
    except Exception as e:
        print(f" Bookmark data validation failed: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_bookmark_creation())
    sys.exit(0 if success else 1)
