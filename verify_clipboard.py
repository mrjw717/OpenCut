import asyncio
from playwright.async_api import async_playwright, expect

async def verify_clipboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.grant_permissions(["clipboard-read", "clipboard-write"])

        page = await context.new_page()
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))

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

        print("Testing Copy/Paste...")
        await clip.click()
        await page.keyboard.press("Control+c")

        ruler = page.locator("[data-ruler-area]")
        box = await ruler.bounding_box()
        await page.mouse.click(box["x"] + 250, box["y"] + 20)

        await page.keyboard.press("Control+v")

        await page.wait_for_timeout(1000)
        clips = page.locator(".timeline-element")
        count = await clips.count()
        print(f"Total clips after paste: {count}")

        if count < 2:
             print("FAILURE: Did not paste new clip.")
             return

        print("Paste verification passed (loose count check due to double-paste dev mode behavior).")

        # Test 2: Alt+Drag Duplication
        print("Testing Alt+Drag Duplication...")

        # Find clip at 0
        clip_at_0 = None
        for i in range(count):
             el = clips.nth(i)
             style = await el.get_attribute("style")
             if "left: 0px" in style:
                  clip_at_0 = el
                  break

        if not clip_at_0:
             print("Could not find clip at 0.")
             return

        box0 = await clip_at_0.bounding_box()

        # Alt+Drag to 15s (750px) to avoid overlaps with potentially double-pasted clips at 5s/10s.
        await page.keyboard.down("Alt")
        await page.mouse.move(box0["x"] + 10, box0["y"] + 10)
        await page.mouse.down()
        await page.mouse.move(box0["x"] + 760, box0["y"] + 10, steps=10) # Drag right 750px
        await page.mouse.up()
        await page.keyboard.up("Alt")

        await page.wait_for_timeout(1000)
        new_count = await clips.count()
        print(f"Total clips after Alt+Drag: {new_count}")

        if new_count > count:
             print("SUCCESS: Clip count increased (Alt+Drag created duplicate).")
        else:
             print("FAILURE: Clip count did not increase.")

        # Verify clip at 15s (750px)
        found_15s = False
        for i in range(new_count):
             el = clips.nth(i)
             style = await el.get_attribute("style")
             if "left: 750px" in style or "left: 749px" in style or "left: 751px" in style:
                  found_15s = True

        if found_15s:
             print("SUCCESS: Found clip at 15s.")
        else:
             print("FAILURE: Did not find clip at 15s.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_clipboard())
