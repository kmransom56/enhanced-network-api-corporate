#!/usr/bin/env python3
"""
Playwright UI smoke tests for the Enhanced Network API application.
"""

import asyncio
import json

import pytest

from playwright.async_api import async_playwright


@pytest.mark.visual_smoke
async def test_ui_interactions():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:11111/", wait_until="networkidle")
        await page.screenshot(path="test_screenshots/main_page.png")

        # Health check
        await page.goto("http://127.0.0.1:11111/health", wait_until="networkidle")
        health_text = await page.text_content("body")
        assert "status" in health_text.lower()

        # Raw topology
        await page.goto("http://127.0.0.1:11111/api/topology/raw", wait_until="networkidle")
        topology_text = await page.text_content("body")
        topology_data = json.loads(topology_text)
        if 'devices' not in topology_data:
            pytest.skip(topology_data.get('detail', 'Topology unavailable'))

        # Scene topology
        await page.goto("http://127.0.0.1:11111/api/topology/scene", wait_until="networkidle")
        scene_data = json.loads(await page.text_content("body"))
        assert "nodes" in scene_data

        # API docs
        await page.goto("http://127.0.0.1:11111/docs", wait_until="networkidle")
        await page.screenshot(path="test_screenshots/api_docs.png")
        assert "Swagger" in await page.title()

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_ui_interactions())
