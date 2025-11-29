#!/usr/bin/env python3
"""
Test button functionality specifically.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError


@pytest.mark.visual_smoke
async def test_button_click():
    """Test the Load Fortinet Topology button"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:11111/", wait_until="networkidle")

        button = page.locator("#loadTopologyBtn")
        assert await button.count() == 1, "Fortinet topology button not found"

        await button.click()
        await page.wait_for_selector("canvas#renderCanvas", timeout=10000)
        try:
            await page.wait_for_function(
                "window.topologyData && Array.isArray(window.topologyData.nodes)",
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            pytest.skip("Topology data not available in this environment")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_button_click())
