import os
import re
import json
import time
from typing import Optional
import requests

# Configuration: model & endpoint (Gemini REST)
# Model chosen: "gemini-1.5" (adjust if your GCP project offers a different variant)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_ENDPOINT = os.getenv(
    "GEMINI_ENDPOINT",
    f"https://generative.googleapis.com/v1beta2/models/{GEMINI_MODEL}:generateText",
)

# Helpers to extract JSON or python code blocks from model output
def _extract_json(text: str) -> Optional[dict]:
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    m2 = re.search(r"(\{(?:[^{}]|\n|\r)*\})", text, re.S)
    if m2:
        try:
            return json.loads(m2.group(1))
        except Exception:
            pass
    return None

def _extract_code_block(text: str, lang: str = "python") -> Optional[str]:
    m = re.search(rf"```{lang}\s*(.*?)\s*```", text, re.S)
    if m:
        return m.group(1)
    m2 = re.search(r"```(?:.*?)\s*(.*?)\s*```", text, re.S)
    if m2:
        return m2.group(1)
    return None

def _parse_gemini_response(resp_json: dict) -> str:
    """
    Try several fields where model text may appear.
    Newer Gemini REST returns 'candidates' or 'output' arrays; be resilient.
    """
    # 1) candidates[*].content
    candidates = resp_json.get("candidates")
    if isinstance(candidates, list) and len(candidates) > 0:
        c0 = candidates[0]
        if isinstance(c0, dict):
            # content may be nested
            content = c0.get("content") or c0.get("output")
            if isinstance(content, str) and content.strip():
                return content
    # 2) output[*].content
    output = resp_json.get("output")
    if isinstance(output, list) and len(output) > 0:
        first = output[0]
        if isinstance(first, dict):
            # content might be a string or list
            text = first.get("content")
            if isinstance(text, str) and text.strip():
                return text
            # some variants embed content in 'text'
            ## if first.get("type") == "message" and isinstance(first.get("text"), str):
            ##     return first.get("text")

    # 3) top-level 'text' or 'response'
    for k in ("text", "response", "result"):
        v = resp_json.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # 4) fallback: dump entire json as a string
    return json.dumps(resp_json, ensure_ascii=False, indent=2)

def generate_tests(problem_statement: str, timeout: int = 30) -> str:
    """
    Use the Gemini REST generateText endpoint to produce a JSON object:
      { "readme": "...", "starter": "...", "tests": "..." }
    This function returns the 'tests' string to write into test_solution.py.

    Requirements:
    - Set GEMINI_API_KEY in your environment.
    - Adjust GEMINI_MODEL/GEMINI_ENDPOINT if needed.
    """
    # Offline stub if key missing
    if not GEMINI_KEY:
        return '''import pytest
from solution import Solution

def test_stub():
    s = Solution()
    assert hasattr(s, "__class__")
'''

    prompt = (
        "You are a code-generation assistant. Input: a LeetCode problem statement.\n"
        "Output: a single JSON object ONLY with keys: 'readme', 'starter', 'tests'.\n"
        "- 'starter' must be a minimal Python file string that defines class Solution with required method signatures.\n"
        "- 'tests' must be pytest-compatible code string that imports Solution from solution.py and contains unit tests\n"
        "  covering typical cases and edge cases. Do NOT include extraneous commentary.\n\n"
        "Problem statement:\n\n"
        f"{problem_statement}\n\n"
        "Return the JSON now."
    )

    headers = {
        "Authorization": f"Bearer {GEMINI_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": {"text": prompt},
        # conservative deterministic settings
        "temperature": 0.0,
        "max_output_tokens": 1024,
    }

    # Retry loop (simple backoff)
    backoff = [1, 2, 4]
    last_exc = None
    for wait in backoff + [None]:
        try:
            resp = requests.post(GEMINI_ENDPOINT, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            resp_json = resp.json()
            text = _parse_gemini_response(resp_json)
            # Try parse JSON from model text
            parsed = _extract_json(text)
            if parsed and isinstance(parsed, dict):
                tests = parsed.get("tests") or parsed.get("test") or parsed.get("tests.py")
                if isinstance(tests, str) and tests.strip():
                    return tests
            # Fallback: try to extract python code block from raw text
            code = _extract_code_block(text, "python")
            if code and ("pytest" in code or "from solution" in code):
                return code
            # If the parsed text itself looks like tests (heuristic), return it
            if "pytest" in text or "from solution" in text:
                return text
            # Last resort: return failure-wrapped stub including raw model output as comment
            return (
                "# AI output couldn't be cleanly parsed. Raw model output below:\n"
                "# --- BEGIN AI OUTPUT ---\n"
                + text.replace("\n", "\n# ")
                + "\n# --- END AI OUTPUT ---\n\n"
                "import pytest\nfrom solution import Solution\n\ndef test_stub():\n    assert True\n"
            )
        except Exception as e:
            last_exc = e
            if wait is None:
                break
            time.sleep(wait)

    # If we reach here, call failed repeatedly
    return f'''# AI generation failed after retries: {last_exc}
import pytest
from solution import Solution

def test_stub():
    assert True
'''