import os
from pathlib import Path
import time


def submit_solution(slug: str, solution_path: Path, headless: bool = True):
    """
    Submit solution to LeetCode using Playwright with improved selectors and persistent auth state.

    Behavior:
    - Uses LEETCODE_AUTH_STATE env var or ./playwright_auth.json to store/reuse auth.
    - If auth state missing, will attempt to log in using LEETCODE_EMAIL / LEETCODE_PASSWORD env vars and save state.
    - Runs headless by default (set headless=False to debug interactively).
    - Attempts multiple editor-set strategies to place code into Monaco/textarea/CodeMirror.
    """
    auth_path = os.getenv("LEETCODE_AUTH_STATE") or str(
        Path.cwd() / "playwright_auth.json")
    email = os.getenv("LEETCODE_EMAIL")
    password = os.getenv("LEETCODE_PASSWORD")

    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except Exception:
        print("[SIMULATION] Playwright not installed. Install with: pip install playwright && playwright install")
        print(
            f"[MANUAL] Open https://leetcode.com/problems/{slug}/, paste {solution_path} into editor and submit.")
        return

    code = solution_path.read_text(encoding="utf-8")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        # If file exists, pass path to storage_state; Playwright accepts a JSON string path here.
        context = None
        if Path(auth_path).exists():
            try:
                context = browser.new_context(storage_state=auth_path)
                print(f"[INFO] Loaded auth state from {auth_path}")
            except Exception:
                context = None

        if context is None:
            context = browser.new_context()

        page = context.new_page()

        # Ensure logged in (navigate to profile page first to test)
        try:
            page.goto("https://leetcode.com/", timeout=15000)
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass

        logged_in = False
        # Heuristic: presence of avatar or "Sign in" absence
        try:
            # If user menu or profile avatar exists, consider logged in
            if page.locator("img[data-cy='profile-avatar']").count() > 0:
                logged_in = True
        except Exception:
            # fallback: try to check for "Sign in" button
            try:
                if page.locator("text=Sign in").count() == 0:
                    logged_in = True
            except Exception:
                logged_in = False

        if not logged_in:
            # Try to use saved state; if none, perform login using env creds
            if not Path(auth_path).exists():
                if not (email and password):
                    print(
                        "[AUTH] No stored auth and LEETCODE_EMAIL/LEETCODE_PASSWORD not set.")
                    print(
                        f"[MANUAL] Open https://leetcode.com/problems/{slug}/ and sign in, then save storage state to {auth_path}.")
                    page.close()
                    context.close()
                    browser.close()
                    return
                # Perform login flow
                print("[AUTH] Attempting login with provided credentials...")
                try:
                    page.goto("https://leetcode.com/accounts/login/",
                              timeout=15000)
                    page.wait_for_load_state("networkidle", timeout=10000)
                    # Fill form – try several selectors
                    try:
                        page.fill('input[name="login"]', email)
                    except Exception:
                        try:
                            page.fill('input[type="email"]', email)
                        except Exception:
                            pass
                    try:
                        page.fill('input[name="password"]', password)
                    except Exception:
                        try:
                            page.fill('input[type="password"]', password)
                        except Exception:
                            pass
                    # Click submit
                    try:
                        page.click('button[type="submit"]', timeout=5000)
                    except Exception:
                        try:
                            page.get_by_role("button", name="Sign In").click()
                        except Exception:
                            pass
                    # Wait for navigation / profile to appear
                    page.wait_for_load_state("networkidle", timeout=15000)
                    time.sleep(1)
                    # Save auth state
                    try:
                        context.storage_state(path=auth_path)
                        print(f"[AUTH] Saved auth state to {auth_path}")
                    except Exception as e:
                        print("[AUTH] Could not save auth state:", e)
                except Exception as e:
                    print("[AUTH] Login attempt failed:", e)
                    # continue — may still work if cookies set elsewhere
            else:
                # already attempted loading file above; still not logged in, proceed and hope page will prompt login
                pass

        # Navigate to problem
        page.goto(f"https://leetcode.com/problems/{slug}/", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)

        # Wait for editor area
        try:
            page.wait_for_selector(".monaco-editor", timeout=7000)
        except PWTimeout:
            # editor may not be monaco or may be lazy; continue anyway
            pass

        # Attempt multiple strategies to set editor content
        set_success = False
        try:
            # 1) Use Monaco API if available
            page.evaluate(
                """(code) => {
                try {
                    if (window.monaco && window.monaco.editor && window.monaco.editor.getModels) {
                        const models = window.monaco.editor.getModels();
                        if (models && models.length > 0) {
                            models[0].setValue(code);
                            return true;
                        }
                    }
                } catch(e) {}
                return false;
            }""",
                code,
            )
            # verify by reading value back (best-effort)
            val = page.evaluate(
                """() => {
                try {
                    if (window.monaco && window.monaco.editor && window.monaco.editor.getModels) {
                        const v = window.monaco.editor.getModels()[0].getValue();
                        return v && v.length;
                    }
                    return false;
                } catch(e) { return false; }
            }"""
            )
            if val:
                set_success = True
        except Exception:
            set_success = False

        if not set_success:
            # 2) Try direct textarea insertion (some pages have hidden textarea for Monaco)
            try:
                page.evaluate(
                    """(code) => {
                    const ta = document.querySelector('textarea');
                    if (ta) {
                        ta.focus();
                        ta.value = code;
                        ta.dispatchEvent(new Event('input', { bubbles: true }));
                        return true;
                    }
                    return false;
                }""",
                    code,
                )
                set_success = True
            except Exception:
                set_success = False

        if not set_success:
            # 3) Try CodeMirror style (rare)
            try:
                page.evaluate(
                    """(code) => {
                    const cmEl = document.querySelector('.CodeMirror');
                    if (cmEl && cmEl.CodeMirror) {
                        cmEl.CodeMirror.setValue(code);
                        return true;
                    }
                    return false;
                }""",
                    code,
                )
                set_success = True
            except Exception:
                set_success = False

        if not set_success:
            print(
                "[WARN] Could not reliably set editor content. You may need to paste manually in the opened page.")
        else:
            print("[INFO] Code injected into editor (best-effort).")

        # Try to set language if needed (optional). Attempt to click language dropdown and choose Python.
        try:
            # Common selector for language dropdown
            if page.locator("button[data-cy='lang-select']").count() > 0:
                page.click("button[data-cy='lang-select']")
                # choose Python
                try:
                    page.get_by_role(
                        "option", name="Python3").click(timeout=2000)
                except Exception:
                    try:
                        page.get_by_role(
                            "option", name="Python").click(timeout=2000)
                    except Exception:
                        pass
            else:
                # Try a fallback dropdown
                dd = page.locator("div[role='listbox']")
                if dd.count() > 0:
                    # try to click python text
                    try:
                        page.click("text=Python3")
                    except Exception:
                        pass
        except Exception:
            # ignore language selection errors
            pass

        # Click submit button (try multiple selectors)
        submitted = False
        try:
            if page.locator("button[data-cy='submit-code-btn']").count() > 0:
                page.click("button[data-cy='submit-code-btn']")
                submitted = True
            else:
                # try button with text
                try:
                    page.get_by_role("button", name="Submit").click()
                    submitted = True
                except Exception:
                    # try CSS button containing 'Submit'
                    try:
                        page.click("button:has-text('Submit')")
                        submitted = True
                    except Exception:
                        submitted = False
        except Exception:
            submitted = False

        if not submitted:
            print(
                "[WARN] Could not click submit automatically. Please submit manually in the opened page.")
        else:
            print("[INFO] Submit clicked. Waiting for result...")

            # Wait for common result indicators (Accepted / Wrong Answer / Runtime Error)
            verdict = None
            try:
                # Wait up to 20s for common verdict texts
                page.wait_for_selector("text=Accepted", timeout=20000)
                verdict = "Accepted"
            except Exception:

                # try to capture result area text (best-effort)
                try:
                    possible = page.locator("text=Accepted")
                    if possible.count() > 0:
                        verdict = "Accepted"
                except Exception:
                    pass

            if not verdict:
                # attempt to read the submission result area
                try:
                    # Some pages render a submission result area with classname 'result' or similar
                    txt = page.inner_text("body", timeout=2000)
                    if "Accepted" in txt:
                        verdict = "Accepted"
                    elif "Wrong Answer" in txt:
                        verdict = "Wrong Answer"
                    elif "Runtime Error" in txt:
                        verdict = "Runtime Error"
                except Exception:
                    verdict = None

            if verdict:
                print(f"✅ Submission verdict: {verdict}")
            else:
                print(
                    "ℹ️ Submission attempted — no clear verdict detected. Check the browser for details.")

        # Save auth state if not present previously
        try:
            Path(auth_path).parent.mkdir(parents=True, exist_ok=True)
            context.storage_state(path=auth_path)
            print(f"[AUTH] Stored/updated auth state at {auth_path}")
        except Exception:
            pass

        # close resources
        try:
            page.close()
            context.close()
            browser.close()
        except Exception:
            pass
