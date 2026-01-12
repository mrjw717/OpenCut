import asyncio
from playwright.async_api import async_playwright, expect
import time

async def verify_zoom():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print("Navigating to home page...")
        try:
            await page.goto("http://localhost:3000", timeout=30000)
        except Exception as e:
            print(f"Failed to load home page: {e}")
            await browser.close()
            return

        print("Clicking 'Try early beta'...")
        try:
            await page.get_by_text("Try early beta").click()
        except:
             print("Could not find 'Try early beta'")
             await browser.close()
             return

        print("Waiting for projects page...")
        try:
            await page.wait_for_url("**/projects", timeout=30000)
        except:
             print("Timed out waiting for projects page")
             await browser.close()
             return

        print("Checking for project creation buttons...")
        create_first = page.get_by_text("Create Your First Project")
        new_project = page.get_by_text("New project")

        if await create_first.is_visible():
            await create_first.click()
        elif await new_project.is_visible():
            await new_project.click()
        else:
            print("No create project button found.")
            await browser.close()
            return

        print("Waiting for editor...")
        try:
            await page.wait_for_url("**/editor/**", timeout=30000)
            await page.wait_for_selector("[data-ruler-area]", state="visible", timeout=30000)
        except Exception as e:
            print(f"Wait for editor exception: {e}")
            await browser.close()
            return

        print("Editor loaded. Verifying zoom...")

        slider = page.get_by_role("slider")

        # Verify markers exist before zooming (at zoom 1)
        # Selector for markers: div inside data-ruler-area that has border-l class
        markers = page.locator("[data-ruler-area] .border-l")
        count_zoom_1 = await markers.count()
        print(f"Markers at Zoom 1: {count_zoom_1}")

        # Zoom in moderately
        print("Zooming in to max...")
        for _ in range(20):
             await page.keyboard.press("Control+=")
             await page.wait_for_timeout(100) # Slower to let React render

        # Wait for render
        await page.wait_for_timeout(2000)

        try:
            max_val = await slider.get_attribute("aria-valuenow")
            print(f"Max slider value: {max_val}")
        except:
            print("Could not get slider value (maybe timeout), skipping check.")

        count_zoom_max = await markers.count()
        print(f"Markers at Zoom Max: {count_zoom_max}")

        if count_zoom_max > count_zoom_1:
             print("SUCCESS: More markers visible at higher zoom.")
        else:
             print(f"WARNING: Marker count did not increase (Zoom 1: {count_zoom_1}, Zoom Max: {count_zoom_max}).")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_zoom())
