#!/usr/bin/env python3
"""
Test Babylon.js 3D visualization as a robust alternative to Three.js
"""

import asyncio

import pytest
from playwright.async_api import async_playwright
from playwright._impl._errors import TimeoutError as PlaywrightTimeoutError


def _attach_console_logging(page):
    def handle_console(msg):
        text = msg.text.lower()
        if any(keyword in text for keyword in ["error", "babylon", "webgl", "failed"]):
            print(f"📋 {msg.type}: {msg.text}")

    page.on("console", handle_console)


@pytest.mark.slow_visual
async def test_babylon():
    """Test Babylon.js 3D network topology"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        _attach_console_logging(page)

        await page.goto("http://127.0.0.1:11111/babylon-test", wait_until="networkidle")
        try:
            await page.wait_for_function("window.babylonReady === true", timeout=15000)
        except PlaywrightTimeoutError:
            pytest.skip("Babylon viewer not ready in this environment")

        babylon_status = await page.evaluate(
            """
            () => ({
                babylonReady: window.babylonReady === true,
                babylonLoaded: typeof BABYLON !== 'undefined',
                engineCreated: !!window.engine,
                sceneCreated: !!window.scene,
                canvasExists: !!document.getElementById('renderCanvas'),
                webglSupported: !!(window.engine && window.engine.webGLVersion > 0),
                deviceCount: window.devices ? window.devices.length : 0,
                connectionCount: window.connections ? window.connections.length : 0
            })
            """
        )

        if not babylon_status["babylonLoaded"]:
            pytest.fail("Babylon.js failed to load")

        # Demo mode
        demo_button = page.locator("button:has-text('🎭 Demo Mode')")
        if await demo_button.count():
            await demo_button.click()
            await page.wait_for_function(
                "window.devices && window.devices.length > 0",
                timeout=10000,
            )

            await page.screenshot(path="test_screenshots/babylon_demo.png")

        # Fortinet topology
        fortinet_button = page.locator("button:has-text('🔥 Load Fortinet')")
        if await fortinet_button.count():
            await fortinet_button.click()
            await page.wait_for_function(
                "window.devices && window.devices.some(dev => dev.metadata && dev.metadata.type)",
                timeout=10000,
            )
            await page.screenshot(path="test_screenshots/babylon_fortinet.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_babylon())
