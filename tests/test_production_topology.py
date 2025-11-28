#!/usr/bin/env python3
"""
Production-ready topology smoke test covering enhanced 2D and 3D visualizations.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright


@pytest.mark.slow_visual
async def test_production_topology():
    """Ensure enhanced 2D and 3D topology views render without errors."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Enhanced 2D topology
        await page.goto("http://127.0.0.1:11111/2d-topology-enhanced", wait_until="networkidle")
        await page.screenshot(path="test_screenshots/topology_2d.png")

        # Babylon 3D topology
        await page.goto("http://127.0.0.1:11111/babylon-test", wait_until="networkidle")
        await page.wait_for_function("window.scene && window.scene.activeCamera", timeout=10000)
        await page.screenshot(path="test_screenshots/topology_3d.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_production_topology())
