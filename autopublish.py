"""
CryptoHunt Auto-Publisher
Same logic as the Webflow auto-publisher — but instead of posting to Webflow CMS API,
this pushes a new markdown article file to GitHub, which triggers a Netlify rebuild.

Setup:
  pip install requests PyGithub

Environment variables required:
  GITHUB_TOKEN   — personal access token (repo scope)
  GITHUB_REPO    — e.g. "yourusername/cryptohunt-site"
"""

import os
import re
import base64
from datetime import date

# pip install PyGithub
try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    import requests
    GITHUB_AVAILABLE = False


def slugify(text):
    """Convert title to URL slug."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text


def create_frontmatter(title, slug, body_html, summary='', image_url='',
                        author='Usman Kashif', tags=None, read_time='5 min',
                        pub_date=None):
    """Build the markdown file content with YAML frontmatter."""
    if tags is None:
        tags = ['Scam Alerts']
    if pub_date is None:
        pub_date = date.today().isoformat()

    tags_yaml = '\n'.join(f'  - {t}' for t in tags)
    summary_clean = summary.replace('"', "'")
    title_clean = title.replace('"', "'")

    return f"""---
title: "{title_clean}"
slug: "{slug}"
date: "{pub_date}"
author: "{author}"
summary: "{summary_clean}"
image: "{image_url}"
read_time: "{read_time}"
tags:
{tags_yaml}
---

{body_html}
""".strip()


def publish_article(title, body_html, summary='', image_url='', slug=None,
                     author='Usman Kashif', tags=None, read_time='5 min',
                     pub_date=None, github_token=None, github_repo=None):
    token = github_token or os.environ.get('GITHUB_TOKEN')
    repo_name = github_repo or os.environ.get('GITHUB_REPO')
    if not token: raise ValueError("GITHUB_TOKEN not set")
    if not repo_name: raise ValueError("GITHUB_REPO not set")
    if not slug: slug = slugify(title)
    content = create_frontmatter(title=title, slug=slug, body_html=body_html,
        summary=summary, image_url=image_url, author=author,
        tags=tags or ['Scam Alerts'], read_time=read_time, pub_date=pub_date)
    file_path = f"content/articles/{slug}.md"
    url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {"message": f"New article: {title}", "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'), "branch": "main"}
    response = requests.put(url, json=payload, headers=headers)
    return {'slug': slug, 'url': f"https://cryptohunt.com.au/post/{slug}", 'file_path': file_path}
