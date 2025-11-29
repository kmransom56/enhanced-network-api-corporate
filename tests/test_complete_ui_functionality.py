#!/usr/bin/env python3
"""
Complete UI functionality smoke test.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright


@pytest.mark.visual_smoke
async def test_complete_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:11111/", wait_until="networkidle")

        # Verify buttons exist
        buttons = await page.locator("button").count()
        assert buttons > 0

        # Load Fortinet topology
        load_button = page.locator("button:has-text('🔥 Load Fortinet')")
        if await load_button.count():
            await load_button.click()
            await page.wait_for_selector("canvas#topo-canvas", timeout=10000)

        # Navigate to documentation
        await page.goto("http://127.0.0.1:11111/docs", wait_until="networkidle")
        assert "Swagger" in await page.title()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_complete_ui())
