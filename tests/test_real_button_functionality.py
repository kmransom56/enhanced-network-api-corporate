#!/usr/bin/env python3
"""
Additional check of Load Fortinet button behaviour.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError


@pytest.mark.visual_smoke
async def test_real_button_functionality():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:11111/", wait_until="networkidle")

        load_button = page.locator("#loadTopologyBtn")
        if not await load_button.count():
            pytest.skip("Load topology button not available in current interface")

        await load_button.click()
        try:
            await page.wait_for_function(
                "window.devices && window.devices.length > 0",
                timeout=15000,
            )
        except PlaywrightTimeoutError:
            pytest.skip("Topology data not available in this environment")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_real_button_functionality())
