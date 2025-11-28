#!/usr/bin/env python3
"""
Simple test to check what's actually visible.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright


@pytest.mark.visual_smoke
async def simple_visibility_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:11111/", wait_until="networkidle")
        await page.screenshot(path="test_screenshots/simple_visibility.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(simple_visibility_test())
