import requests
from bs4 import BeautifulSoup
from typing import Optional
from pathlib import Path
import json

GRAPHQL_ENDPOINT = "https://leetcode.com/graphql"
QUESTION_QUERY = """
query getQuestionDetail($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionId
    title
    titleSlug
    content
    difficulty
    exampleTestcases
    codeSnippets { lang code }
    topicTags { name slug }
  }
}
"""

# cache dir (project root /.cache)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = _PROJECT_ROOT / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    lines = []

    for elem in soup.children:
        if getattr(elem, "name", None) == "pre":
            code_text = elem.get_text()
            lines.append("```python")
            lines.append(code_text.rstrip())
            lines.append("```")
        else:
            text = elem.get_text(separator="\n").strip()
            if text:
                lines.append(text)
    return "\n\n".join(lines).strip()

def _question_to_markdown(q: dict, slug: str) -> str:
    title = q.get("title") or slug
    difficulty = q.get("difficulty", "")
    tags = ", ".join([t.get("name") for t in q.get("topicTags", []) if t.get("name")])
    content_html = q.get("content", "")
    examples = q.get("exampleTestcases") or ""

    md_parts = [f"# {title}", f"**Difficulty:** {difficulty}" if difficulty else "", f"**Tags:** {tags}" if tags else ""]
    if content_html:
        md_parts.append(_html_to_markdown(content_html))
    if examples:
        md_parts.append("## Example Testcases\n")
        md_parts.append("```\n" + examples.strip() + "\n```")

    return "\n\n".join([p for p in md_parts if p]).strip()

def _cache_path(slug: str) -> Path:
    return CACHE_DIR / f"{slug}.json"

def fetch_problem(slug: str, force: bool = False) -> str:
    """
    Use LeetCode GraphQL to fetch question content and return Markdown.
    Caches GraphQL JSON at .cache/<slug>.json. Set force=True to ignore cache.
    """
    cache_file = _cache_path(slug)
    # Try cache first (unless forcing)
    if cache_file.exists() and not force:
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            q = data.get("data", {}).get("question")
            if q:
                return _question_to_markdown(q, slug) + f"\n\n<!-- Cached: {cache_file.name} -->"
            # if cache invalid fall through to network fetch
        except Exception:
            # ignore parse errors and fetch fresh
            pass

    # Perform GraphQL fetch
    try:
        payload = {"query": QUESTION_QUERY, "variables": {"titleSlug": slug}}
        headers = {"Content-Type": "application/json", "Referer": f"https://leetcode.com/problems/{slug}/"}
        r = requests.post(GRAPHQL_ENDPOINT, json=payload, headers=headers, timeout=10)
        if r.status_code != 200:
            return f"# {slug}\n\nGraphQL fetch failed (status {r.status_code})."

        resp_json = r.json()
        # Save to cache (best-effort)
        try:
            cache_file.write_text(json.dumps(resp_json, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

        q = resp_json.get("data", {}).get("question")
        if not q:
            return f"# {slug}\n\nQuestion not found in GraphQL response."

        return _question_to_markdown(q, slug)
    except Exception as e:
        # fallback: try to use cached file even if force was true but network failed
        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                q = data.get("data", {}).get("question")
                if q:
                    return _question_to_markdown(q, slug) + "\n\n<!-- Fallback to cached content due to network error -->"
            except Exception:
                pass
        return f"# {slug}\n\nFetch error: {e}"
