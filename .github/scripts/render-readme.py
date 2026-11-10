#!/usr/bin/env python3
"""Render README.tmpl to README.md, filling the RECENT_* markers from the GitHub API."""
import json
import os
import sys
import urllib.request

USER = os.environ.get("PROFILE_USER", "technicks89")
TOKEN = os.environ.get("GH_TOKEN", "")


def api(path):
    req = urllib.request.Request(
        "https://api.github.com" + path,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-readme"},
    )
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def line(url, name, desc):
    desc = " ".join((desc or "").split())
    return "- [%s](%s)%s" % (name, url, " - " + desc if desc else "")


def recent_repos(own_only_pushed):
    repos = api("/users/%s/repos?sort=pushed&per_page=30&type=owner" % USER)
    repos = [r for r in repos if not r["fork"] and r["name"] != USER]
    return [line(r["html_url"], r["name"], r["description"]) for r in repos[:own_only_pushed]]


PR_REPOS = ["technicks89/Lyona", "ChrisTitusTech/dwm-titus", "ChrisTitusTech/linutil"]


PRS_PER_REPO = 2


def recent_prs():
    items = []
    for repo in PR_REPOS:
        q = "author:%s+type:pr+repo:%s" % (USER, repo)
        items += api("/search/issues?q=%s&sort=created&order=desc&per_page=%d" % (q, PRS_PER_REPO))["items"]
    items.sort(key=lambda i: i["created_at"], reverse=True)
    return [
        line(i["html_url"], i["repository_url"].split("/repos/")[1] + "#%d" % i["number"], i["title"])
        for i in items
    ]


def recent_stars():
    req = urllib.request.Request(
        "https://api.github.com/users/%s/starred?per_page=5" % USER,
        headers={"Accept": "application/vnd.github.star+json", "User-Agent": "profile-readme"},
    )
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        stars = json.load(r)
    return [line(s["repo"]["html_url"], s["repo"]["full_name"], s["repo"]["description"]) for s in stars]


def section(fn, *args):
    try:
        out = fn(*args)
    except Exception as exc:  # keep the page usable if the API fails
        print("warning: %s failed: %s" % (fn.__name__, exc), file=sys.stderr)
        out = []
    return "\n".join(out) if out else "- Nothing to show yet."


def main():
    src, dst = sys.argv[1], sys.argv[2]
    text = open(src, encoding="utf-8").read()
    text = text.replace("<!-- RECENT_WORK -->", section(recent_repos, 3))
    text = text.replace("<!-- RECENT_REPOS -->", section(recent_repos, 6))
    text = text.replace("<!-- RECENT_PULL_REQUESTS -->", section(recent_prs))
    text = text.replace("<!-- RECENT_STARS -->", section(recent_stars))
    open(dst, "w", encoding="utf-8").write(text)


if __name__ == "__main__":
    main()
