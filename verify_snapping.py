import asyncio
from playwright.async_api import async_playwright, expect

async def verify_snapping():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Bypass onboarding
        await page.add_init_script("""
            localStorage.setItem("hasSeenOnboarding", "true");
        """)

        print("Navigating to home page...")
        try:
            await page.goto("http://localhost:3000", timeout=30000)
        except Exception as e:
            print(f"Failed to load home page: {e}")
            await browser.close()
            return

        print("Entering editor...")
        await page.get_by_text("Try early beta").click()
        await page.wait_for_url("**/projects", timeout=30000)

        # Click new project if available
        create_first = page.get_by_text("Create Your First Project")
        if await create_first.is_visible():
            await create_first.click()
        else:
             await page.get_by_text("New project").click()

        await page.wait_for_url("**/editor/**", timeout=30000)
        print("Editor loaded.")

        # Locate Magnet button
        # It's in the toolbar. It should have the Magnet icon.
        # Since we wrapped it in DropdownMenuTrigger, it's still a button.

        magnet_btn = page.locator("button:has(svg.lucide-magnet)")
        await expect(magnet_btn).to_be_visible()

        print("Opening snapping menu...")
        # Force click if needed, but standard click should work now that overlay is gone
        await magnet_btn.click()

        # Check menu items
        menu = page.locator("[role='menu']")
        await expect(menu).to_be_visible()

        enabled_item = page.get_by_role("menuitemcheckbox", name="Snapping Enabled")
        elements_item = page.get_by_role("menuitemcheckbox", name="Snap to Clips")
        playhead_item = page.get_by_role("menuitemcheckbox", name="Snap to Playhead")
        markers_item = page.get_by_role("menuitemcheckbox", name="Snap to Markers")

        await expect(enabled_item).to_be_visible()
        await expect(elements_item).to_be_visible()
        await expect(playhead_item).to_be_visible()
        await expect(markers_item).to_be_visible()

        print("Verifying default state (All checked)...")
        await expect(enabled_item).to_be_checked()
        await expect(elements_item).to_be_checked()
        await expect(playhead_item).to_be_checked()
        await expect(markers_item).to_be_checked()

        print("Toggling 'Snap to Markers'...")
        await markers_item.click()

        # Menu might close on click, so reopen
        # Playwright's click might auto-dismiss the menu.
        # We need to re-open to verify state if it closed.
        if not await menu.is_visible():
             await magnet_btn.click()

        await expect(markers_item).not_to_be_checked()
        print("Toggle successful.")

        print("Disabling Master Switch...")
        await enabled_item.click()

        if not await menu.is_visible():
             await magnet_btn.click()

        await expect(enabled_item).not_to_be_checked()

        # Check if sub-items are disabled
        await expect(elements_item).to_be_disabled()
        print("Sub-items disabled correctly.")

        await browser.close()
        print("Snapping verification complete.")

if __name__ == "__main__":
    asyncio.run(verify_snapping())
