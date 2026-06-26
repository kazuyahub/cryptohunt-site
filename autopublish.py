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
    """
    Publish a new article by pushing it to the GitHub repo.
    Netlify will automatically rebuild and deploy the site.
    
    Args:
        title        : Article title
        body_html    : Full article HTML body (from your content generator)
        summary      : Short summary/excerpt
        image_url    : Hero image URL
        slug         : URL slug (auto-generated from title if not provided)
        author       : Author name ('Usman Kashif' or 'Ilyan Kashif')
        tags         : List of tags e.g. ['Scam Alerts']
        read_time    : e.g. '5 min'
        pub_date     : Publication date (defaults to today)
        github_token : GitHub personal access token (or set GITHUB_TOKEN env var)
        github_repo  : GitHub repo e.g. 'username/cryptohunt-site' (or GITHUB_REPO env var)
    
    Returns:
        dict with 'slug', 'url', 'file_path', 'commit_url'
    """
    token = github_token or os.environ.get('GITHUB_TOKEN')
    repo_name = github_repo or os.environ.get('GITHUB_REPO')

    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    if not repo_name:
        raise ValueError("GITHUB_REPO environment variable not set")

    if not slug:
        slug = slugify(title)

    content = create_frontmatter(
        title=title, slug=slug, body_html=body_html,
        summary=summary, image_url=image_url, author=author,
        tags=tags or ['Scam Alerts'], read_time=read_time, pub_date=pub_date
    )

    file_path = f"content/articles/{slug}.md"
    commit_message = f"New article: {title}"

    if GITHUB_AVAILABLE:
        # Use PyGithub library
        g = Github(token)
        repo = g.get_repo(repo_name)
        result = repo.create_file(
            path=file_path,
            message=commit_message,
            content=content,
            branch="main"
        )
        commit_url = result['commit'].html_url
    else:
        # Use raw GitHub API (no extra dependencies)
        url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "message": commit_message,
            "content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
            "branch": "main"
        }
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code not in (200, 201):
            raise Exception(f"GitHub API error {response.status_code}: {response.text}")
        commit_url = response.json()['commit']['html_url']

    print(f"✓ Article published: {title}")
    print(f"  File: {file_path}")
    print(f"  Commit: {commit_url}")
    print(f"  → Netlify will rebuild in ~60 seconds")
    print(f"  → Live at: https://cryptohunt.com.au/post/{slug}")

    return {
        'slug': slug,
        'url': f"https://cryptohunt.com.au/post/{slug}",
        'file_path': file_path,
        'commit_url': commit_url
    }


# ─── Example usage ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Set your credentials (or use environment variables)
    # os.environ['GITHUB_TOKEN'] = 'ghp_your_token_here'
    # os.environ['GITHUB_REPO']  = 'yourusername/cryptohunt-site'

    result = publish_article(
        title="Example: New Crypto Scam Alert 2026",
        body_html="""
<h2>Introduction</h2>
<p>This is the article body in HTML. Your auto-publisher generates this content
and passes it directly to this function — same as it did with Webflow API.</p>

<h2>What Happened</h2>
<p>Details about the scam here...</p>

<h2>How to Stay Safe</h2>
<p>Protection tips here...</p>
""",
        summary="A new crypto scam targeting Australians has been identified. Here's what you need to know.",
        image_url="https://cdn.prod.website-files.com/69c6e47d43da620ce27fc19e/example-image.png",
        author="Usman Kashif",
        tags=["Scam Alerts"],
        read_time="4 min"
    )
    print(f"\nPublished: {result['url']}")
