#!/usr/bin/env python3
"""DC Inside Running Gallery monitor - detects race-related posts and sends Telegram notifications."""

import json
import os
import sys
import time
import re
import subprocess
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

STATE_FILE = Path(__file__).parent / "runninggal_seen.json"
BOT_TOKEN = "8701008789:AAGRxjKU4YZZmO5J3ShZ6tP3AnGfjMeAvqM"
CHAT_ID = "8581246573"
TELEGRAM_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Referer": "https://gall.dcinside.com/",
}

SOURCES = [
    ("mgallery", "https://gall.dcinside.com/mgallery/board/lists/?id=running"),
    ("gallery",  "https://gall.dcinside.com/board/lists/?id=running"),
]

# Race-related keywords (include)
RACE_INCLUDE = re.compile(
    r"대회|마라톤|레이스|하프|풀코스|10km|5km|울트라|트레일|로드레이스|"
    r"접수|모집|신청|요강|공고|일정|엔트리|참가|등록|출전|개최|"
    r"런닝대회|달리기대회|마라토|경기|대회안내|대회정보",
    re.IGNORECASE
)

# Non-race keywords (exclude)
RACE_EXCLUDE = re.compile(
    r"후기|다녀왔|완주기|인증|훈련|장비|식단|부상|잡담|짤|정치|뻘글|"
    r"공지|리뷰|추천|구매|질문|도움|방법|조언|팁|tip|패이스|페이스|"
    r"사진|영상|유튜브|유투브|기록|PR|PB|러닝화|양말|"
    r"근육|스트레칭|준비운동|회복|아이싱",
    re.IGNORECASE
)

def load_state():
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
            return data.get("seen_post_ids", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_state(seen_ids):
    # Cap to 500 most recent
    seen_ids = seen_ids[-500:]
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump({"seen_post_ids": seen_ids}, f, ensure_ascii=False, indent=2)

def fetch_gallery():
    """Try each source URL; return (gallery_type, base_url, soup) or None on failure."""
    for gtype, url in SOURCES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                if not resp.content:
                    print(f"HTTP 200 but empty body from {url} — anti-bot block suspected")
                    continue
                print(f"Fetched gallery from: {url}")
                soup = BeautifulSoup(resp.text, "html.parser")
                return gtype, url, soup
            else:
                print(f"HTTP {resp.status_code} from {url}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return None

def build_post_url(gtype, post_id):
    if gtype == "mgallery":
        return f"https://gall.dcinside.com/mgallery/board/view/?id=running&no={post_id}"
    else:
        return f"https://gall.dcinside.com/board/view/?id=running&no={post_id}"

def parse_posts(soup, gtype):
    """Parse gallery list, return list of (post_id, title, post_url, author)."""
    posts = []

    # DC Inside uses tr rows in a table with class 'gall_list'
    rows = soup.select("table.gall_list tbody tr")
    if not rows:
        # Fallback: try any tr rows that look like posts
        rows = soup.select("tr.ub-content")
    if not rows:
        rows = soup.select("tr[data-no]")

    for row in rows:
        # Skip notice/ad rows
        row_classes = " ".join(row.get("class", []))
        if "us-post" in row_classes or "notice" in row_classes:
            continue

        # Try data-no attribute first
        post_id = row.get("data-no", "").strip()
        if not post_id or not post_id.isdigit():
            # Try the gall_num td
            num_td = row.select_one("td.gall_num")
            if num_td:
                post_id = num_td.get_text(strip=True)
            if not post_id or not post_id.isdigit():
                continue

        # Get title
        title_td = row.select_one("td.gall_tit")
        if not title_td:
            title_td = row.select_one("td.ub-word")
        if not title_td:
            continue

        title_a = title_td.select_one("a")
        if not title_a:
            continue
        title = title_a.get_text(strip=True)
        # Remove reply count suffix like [3]
        title = re.sub(r"\[\d+\]$", "", title).strip()

        if not title:
            continue

        # Get author
        author_td = row.select_one("td.gall_writer") or row.select_one("td.ub-writer")
        author = ""
        if author_td:
            author = author_td.get("data-nick", "") or author_td.get_text(strip=True)

        post_url = build_post_url(gtype, post_id)
        posts.append((post_id, title, post_url, author))

    return posts

def is_race_related_title(title):
    """Returns True/False/None. None means ambiguous (needs body fetch)."""
    if RACE_EXCLUDE.search(title):
        return False
    if RACE_INCLUDE.search(title):
        return True
    # Ambiguous if title contains '대회' alone or is very short
    if len(title) <= 5 or re.search(r"^대회$|대회\s*$", title.strip()):
        return None
    return False

def fetch_post_body(gtype, post_id):
    """Fetch a post body for disambiguation."""
    url = build_post_url(gtype, post_id)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        body = soup.select_one("div.write_div") or soup.select_one("div.s_write") or soup.select_one("div#content")
        return body.get_text(separator=" ", strip=True)[:2000] if body else ""
    except Exception as e:
        print(f"  Body fetch error for {post_id}: {e}")
        return ""

def send_telegram(text):
    """Send a Telegram message. Returns True on success."""
    try:
        resp = requests.post(
            f"{TELEGRAM_BASE}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": "false",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return True
        else:
            print(f"  Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  Telegram send exception: {e}")
        return False

def main():
    start_time = time.time()

    # 1. Load state
    seen_ids_original = load_state()
    seen_set = set(seen_ids_original)
    was_empty = len(seen_ids_original) == 0
    print(f"Loaded {len(seen_ids_original)} seen post IDs")

    # 2. Fetch gallery
    result = fetch_gallery()
    if result is None:
        print("Gallery fetch failed. Exiting without state change.")
        # If this is the very first run, initialize an empty state file so the
        # infrastructure is in place for the next hourly attempt.
        if was_empty:
            save_state([])
            repo_root = Path(__file__).parent.parent
            subprocess.run(["git", "add", "data/runninggal_seen.json"], cwd=repo_root)
            subprocess.run([
                "git", "-c", "user.email=routine@endurohub.local", "-c", "user.name=Runninggal Bot",
                "commit", "-m", "Update runninggal seen posts"
            ], cwd=repo_root)
            push_result = subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=repo_root)
            if push_result.returncode != 0:
                subprocess.run(["git", "pull", "--rebase", "origin", "master"], cwd=repo_root)
                subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=repo_root)
            print("Initialized empty state file and committed.")
        sys.exit(0)

    gtype, gallery_url, soup = result
    list_url = gallery_url.split("?")[0] + "?id=running"

    posts = parse_posts(soup, gtype)
    if not posts:
        print("WARNING: Parsed 0 posts — possible HTML structure change. Exiting.")
        sys.exit(0)

    print(f"Parsed {len(posts)} posts from gallery")

    # 3. Find new posts
    new_posts = [(pid, title, url, author) for pid, title, url, author in posts if pid not in seen_set]
    print(f"New posts: {len(new_posts)}")

    # 4. First-run protection
    if was_empty and len(new_posts) >= 20:
        all_ids = seen_ids_original[:]
        for pid, _, _, _ in posts:
            if pid not in seen_set:
                all_ids.append(pid)
                seen_set.add(pid)
        save_state(all_ids)
        subprocess.run(["git", "add", "data/runninggal_seen.json"], cwd=Path(__file__).parent.parent)
        subprocess.run([
            "git", "-c", "user.email=routine@endurohub.local", "-c", "user.name=Runninggal Bot",
            "commit", "-m", "Update runninggal seen posts"
        ], cwd=Path(__file__).parent.parent, capture_output=False)
        push_result = subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=Path(__file__).parent.parent)
        if push_result.returncode != 0:
            subprocess.run(["git", "pull", "--rebase", "origin", "master"], cwd=Path(__file__).parent.parent)
            subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=Path(__file__).parent.parent)
        print(f"First run: bootstrapped {len(all_ids)} ids")
        sys.exit(0)

    # 5. Evaluate new posts (max 30)
    new_posts_to_check = new_posts[:30]
    body_fetches = 0
    race_posts = []
    evaluated_ids = []

    for pid, title, url, author in new_posts_to_check:
        # Hard cap: 2 minutes
        if time.time() - start_time > 110:
            print("Approaching time limit, stopping evaluation")
            break

        decision = is_race_related_title(title)
        if decision is None and body_fetches < 10:
            print(f"  Ambiguous title '{title}' — fetching body for post {pid}")
            body = fetch_post_body(gtype, pid)
            body_fetches += 1
            if RACE_INCLUDE.search(body) and not RACE_EXCLUDE.search(body[:200]):
                decision = True
            else:
                decision = False

        if decision is None:
            decision = False  # couldn't fetch, assume non-race

        evaluated_ids.append(pid)
        if decision:
            race_posts.append((pid, title, url, author))
            print(f"  RACE: [{pid}] {title}")
        else:
            print(f"  skip: [{pid}] {title}")

    # 6 & 7. Send Telegram messages
    sent_count = 0
    failed_ids = set()

    if race_posts:
        to_send_individually = race_posts[:10]
        extra_posts = race_posts[10:]

        for pid, title, url, author in to_send_individually:
            if time.time() - start_time > 115:
                break
            msg = f"🏃 새로운 대회 글\n\n<b>{title}</b>\nby {author}\n{url}"
            success = send_telegram(msg)
            if success:
                sent_count += 1
                print(f"  Sent Telegram for [{pid}] {title[:40]}")
            else:
                failed_ids.add(pid)
                print(f"  Failed Telegram for [{pid}]")
            time.sleep(0.4)

        if extra_posts:
            summary = f"그 외 {len(extra_posts)}건 더 있음: {list_url}"
            success = send_telegram(summary)
            if success:
                sent_count += 1
                print(f"  Sent summary for {len(extra_posts)} more posts")
            time.sleep(0.4)

    # 8. Update seen_post_ids
    # Add all evaluated ids EXCEPT those that failed Telegram (race only)
    updated_seen = list(seen_ids_original)
    for pid in evaluated_ids:
        if pid not in seen_set:
            # If this was a race post that failed to send, don't add it
            if pid in failed_ids:
                continue
            updated_seen.append(pid)
            seen_set.add(pid)

    # Also add all other (non-new) post_ids from this run that weren't new
    # (they're already in seen_set, no action needed)

    # 9. Save state and commit
    save_state(updated_seen)

    repo_root = Path(__file__).parent.parent
    subprocess.run(["git", "add", "data/runninggal_seen.json"], cwd=repo_root)
    commit_result = subprocess.run([
        "git", "-c", "user.email=routine@endurohub.local", "-c", "user.name=Runninggal Bot",
        "commit", "-m", "Update runninggal seen posts"
    ], cwd=repo_root)
    if commit_result.returncode == 0:
        push_result = subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=repo_root)
        if push_result.returncode != 0:
            subprocess.run(["git", "pull", "--rebase", "origin", "master"], cwd=repo_root)
            subprocess.run(["git", "push", "origin", "HEAD:master"], cwd=repo_root)
    else:
        print("Nothing to commit")

    total_checked = len(posts)
    total_new = len(new_posts)
    total_race = len(race_posts)
    print(f"Checked {total_checked} posts, {total_new} new, {total_race} race-related, sent {sent_count} telegrams.")

if __name__ == "__main__":
    main()
