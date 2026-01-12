import asyncio
from playwright.async_api import async_playwright, expect

async def verify_ripple():
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

        # Duplicate via Context Menu
        print("Duplicating clip...")
        await clip.click(button="right")
        await page.get_by_text("Duplicate clip").click()

        clips = page.locator(".timeline-element")
        await expect(clips).to_have_count(2)

        print("Enabling Ripple...")
        ripple_btn = page.locator("button:has(svg.lucide-link)")
        await ripple_btn.click()

        clip1 = clips.nth(0)

        # Drag Clip 1 to new track
        box1 = await clip1.bounding_box()
        print("Dragging clip 1 to new track...")
        await page.mouse.move(box1["x"] + 10, box1["y"] + 10)
        await page.mouse.down()
        await page.mouse.move(box1["x"] + 10, box1["y"] + 150, steps=10)
        await page.mouse.up()

        await page.wait_for_timeout(1000)

        # Analyze state
        new_clips = page.locator(".timeline-element")
        count = await new_clips.count()

        tids = set()
        ok_count = 0

        for i in range(count):
             el = new_clips.nth(i)
             style = await el.get_attribute("style")
             tid = await el.get_attribute("data-track-id")
             txt = await el.inner_text()
             print(f"Clip {i} ({txt}): Track={tid}, Style={style}")

             tids.add(tid)
             if "left: 0px" in style or "left: 5px" in style or "left: 4px" in style:
                  ok_count += 1

        if len(tids) > 1:
             print("SUCCESS: Clips are on different tracks (Drag worked).")
        else:
             print("FAILURE: Clips are on same track (Drag failed).")

        if ok_count == 2:
             print("SUCCESS: Both clips near 0px (Ripple worked).")
        else:
             print("FAILURE: Not all clips near 0px.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_ripple())
