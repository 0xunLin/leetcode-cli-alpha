from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path.cwd() / "playwright_auth.json"

def main():
    print(f"[INFO] This will open a browser for you to log into LeetCode and save auth state to: {OUT}")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://leetcode.com/accounts/login/")
        print("[ACTION] Please complete the login in the opened browser window.")
        input("Press Enter here after you finish logging in and can see your profile page...")
        try:
            context.storage_state(path=str(OUT))
            print(f"[OK] Saved Playwright auth state to {OUT}")
        except Exception as e:
            print("[ERR] Failed to save auth state:", e)
        finally:
            browser.close()

if __name__ == "__main__":
    main()