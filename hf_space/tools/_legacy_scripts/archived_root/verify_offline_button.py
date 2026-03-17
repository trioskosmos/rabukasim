from playwright.sync_api import expect, sync_playwright


def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto("http://localhost:8080/")

        # Take a screenshot
        page.screenshot(path="/home/jules/verification/offline_button.png")

        # Verify the button exists and is visible
        offline_btn = page.get_by_text("Start Offline (WASM)")
        expect(offline_btn).to_be_visible()

    except Exception as e:
        print(f"Error: {e}")
        raise e
    finally:
        browser.close()


with sync_playwright() as playwright:
    run(playwright)
