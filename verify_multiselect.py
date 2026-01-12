import asyncio
from playwright.async_api import async_playwright, expect

async def verify_multiselect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.add_init_script("""
            localStorage.setItem("hasSeenOnboarding", "true");
        """)

        print("Navigating to home page...")
        await page.goto("http://localhost:3000", timeout=30000)

        print("Entering editor...")
        await page.get_by_text("Try early beta").click()
        await page.wait_for_url("**/projects", timeout=30000)

        create_first = page.get_by_text("Create Your First Project")
        if await create_first.is_visible():
            await create_first.click()
        else:
             await page.get_by_text("New project").click()

        await page.wait_for_url("**/editor/**", timeout=30000)
        print("Editor loaded.")

        print("Adding test clip...")
        await page.wait_for_timeout(1000)
        add_test_btn = page.get_by_role("button", name="Add Test Clip")
        if await add_test_btn.is_visible():
             await add_test_btn.click()

        clip = page.locator(".timeline-element").first
        await expect(clip).to_be_visible()

        # Duplicate to get 3 clips
        await clip.click(button="right")
        await page.get_by_text("Duplicate clip").click()
        await page.wait_for_timeout(500)

        clips = page.locator(".timeline-element")
        await expect(clips).to_have_count(2)
        await clips.nth(1).click(button="right")
        await page.get_by_text("Duplicate clip").click()
        await expect(clips).to_have_count(3)

        print("Selecting Clip 1...")
        await clips.nth(0).click()

        badge = page.get_by_text("1 selected")
        await expect(badge).to_be_visible()
        print("Badge visible: 1 selected")

        print("Shift+Clicking Clip 3...")
        await page.keyboard.down("Shift")
        await clips.nth(2).click()
        await page.keyboard.up("Shift")

        badge3 = page.get_by_text("3 selected")
        await expect(badge3).to_be_visible()
        print("Badge visible: 3 selected (Range works)")

        # Clear selection
        await page.locator("button:has(svg.lucide-x)").click()
        await expect(page.get_by_text("selected")).not_to_be_visible()

        # Drag Box
        box1 = await clips.nth(0).bounding_box()
        box2 = await clips.nth(1).bounding_box()

        # Start below Clip 1 (safely inside X range)
        start_x = box1["x"] + 10
        start_y = box1["y"] + box1["height"] + 20

        # End inside Clip 2
        end_x = box2["x"] + 10
        end_y = box2["y"] + 5

        print("Dragging selection box...")
        await page.mouse.move(start_x, start_y)
        await page.mouse.down()
        await page.mouse.move(end_x, end_y, steps=10)
        await page.mouse.up()

        badge2 = page.get_by_text("2 selected")
        await expect(badge2).to_be_visible()
        print("Badge visible: 2 selected (Box works)")

        # Test Shift+Drag Box (Additive)
        box3 = await clips.nth(2).bounding_box()

        # Start below Clip 3
        start_x_3 = box3["x"] + 10
        start_y_3 = box3["y"] + box3["height"] + 20
        end_x_3 = box3["x"] + 10
        end_y_3 = box3["y"] + 5

        print("Shift+Dragging box over Clip 3...")
        await page.keyboard.down("Shift")
        await page.mouse.move(start_x_3, start_y_3)
        await page.mouse.down()
        await page.mouse.move(end_x_3, end_y_3, steps=10)
        await page.mouse.up()
        await page.keyboard.up("Shift")

        await expect(badge3).to_be_visible()
        print("Badge visible: 3 selected (Additive Box works)")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_multiselect())
