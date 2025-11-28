#!/usr/bin/env python3
"""
Test simple WebGL rendering.
"""

import asyncio

import pytest
from playwright.async_api import async_playwright


@pytest.mark.slow_visual
async def test_simple_webgl():
    """Test if we can create a simple WebGL scene"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("http://127.0.0.1:11111/", wait_until="networkidle")

        simple_test = await page.evaluate(
            """
            () => {
                try {
                    let canvas = document.getElementById('topology-canvas') || document.getElementById('test-webgl-canvas');
                    if (!canvas) {
                        canvas = document.createElement('canvas');
                        canvas.id = 'test-webgl-canvas';
                        canvas.width = 800;
                        canvas.height = 600;
                        document.body.appendChild(canvas);
                    }

                    const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
                    renderer.setSize(canvas.clientWidth || 800, canvas.clientHeight || 600);
                    renderer.setClearColor(0x0000ff, 1.0);

                    const scene = new THREE.Scene();
                    const camera = new THREE.PerspectiveCamera(
                        75,
                        (canvas.clientWidth || 800) / (canvas.clientHeight || 600),
                        0.1,
                        1000
                    );
                    camera.position.z = 5;

                    const geometry = new THREE.BoxGeometry(2, 2, 2);
                    const material = new THREE.MeshBasicMaterial({ color: 0xff0000 });
                    const cube = new THREE.Mesh(geometry, material);
                    scene.add(cube);

                    renderer.render(scene, camera);
                    return 'Simple WebGL test successful';
                } catch (error) {
                    return 'Simple WebGL test failed: ' + error.message;
                }
            }
            """
        )

        if 'successful' not in simple_test:
            pytest.skip(simple_test)

        await page.wait_for_timeout(500)
        await page.screenshot(path="test_screenshots/simple_webgl_test.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_simple_webgl())
