"""Write the latest posts from fryderykpryjma.com into README.md.

    python scripts/blog.py

Replaces everything between <!-- BLOG:START --> and <!-- BLOG:END -->.
Standard library only, so the workflow needs no extra installs.
"""
from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED = "https://fryderykpryjma.com/rss.xml"
MAX_POSTS = 4
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- BLOG:START -->", "<!-- BLOG:END -->"


def fetch() -> list[tuple[str, str, str]]:
    req = urllib.request.Request(FEED, headers={"User-Agent": "profile-readme-blog-sync"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    posts = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        date = item.findtext("pubDate")
        when = parsedate_to_datetime(date).strftime("%b %Y") if date else ""
        if title and link:
            posts.append((title, link, when))
    return posts[:MAX_POSTS]


def main() -> None:
    posts = fetch()
    if not posts:
        raise SystemExit("Feed returned no posts; leaving README unchanged.")
    lines = [
        f"- [{t.replace('[', '(').replace(']', ')')}]({link})" + (f" <sub>· {when}</sub>" if when else "")
        for t, link, when in posts
    ]
    block = f"{START}\n" + "\n".join(lines) + f"\n{END}"
    text = README.read_text(encoding="utf-8")
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
    if new != text:
        README.write_text(new, encoding="utf-8")
        print(f"Updated {len(posts)} posts.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
