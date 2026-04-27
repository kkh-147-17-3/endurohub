#!/usr/bin/env python3
import json
import os
import sys
import time
import re
import subprocess
import signal

# Hard runtime cap: 2 minutes
start_time = time.time()
def time_remaining():
    return 120 - (time.time() - start_time)

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "--quiet"])
    import requests
    from bs4 import BeautifulSoup

STATE_FILE = "/home/user/endurohub/data/runninggal_seen.json"
BOT_TOKEN = "***REMOVED***"
CHAT_ID = "8581246573"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://gall.dcinside.com/",
}

GALLERY_URLS = [
    ("mgallery", "https://gall.dcinside.com/mgallery/board/lists/?id=running"),
    ("board",    "https://gall.dcinside.com/board/lists/?id=running"),
]

# --- State ---
def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data.get("seen_post_ids"), list):
                return data["seen_post_ids"]
    except Exception:
        pass
    return []

def save_state(seen_ids):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    capped = seen_ids[-500:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen_post_ids": capped}, f, ensure_ascii=False, indent=2)

# --- Fetch gallery list ---
def fetch_gallery():
    for gallery_type, url in GALLERY_URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                print(f"Fetched gallery via {gallery_type}: {url}")
                return gallery_type, url, resp.text
            else:
                print(f"HTTP {resp.status_code} for {url}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return None, None, None

def parse_posts(html, gallery_type, base_url):
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    rows = soup.select("tr.ub-content, tr[data-no]")
    if not rows:
        rows = soup.select("tbody tr")

    for row in rows:
        # Skip notices/ads by class
        row_classes = " ".join(row.get("class", []))
        if "us-post" in row_classes or "공지" in row_classes:
            continue

        # Try to get post_id from data-no attribute first
        post_id = row.get("data-no", "").strip()

        if not post_id:
            # Try gall_num cell
            num_cell = row.select_one("td.gall_num")
            if num_cell:
                post_id = num_cell.get_text(strip=True)

        # Skip non-numeric IDs (notices, ads)
        if not post_id or not re.match(r'^\d+$', post_id):
            continue

        # Title
        title_cell = row.select_one("td.gall_tit, td.ub-content")
        if not title_cell:
            title_cell = row.select_one("td.title")
        if not title_cell:
            continue

        # Get title link
        title_link = title_cell.select_one("a")
        if not title_link:
            continue

        title = title_link.get_text(strip=True)
        # Remove reply count like [3]
        title = re.sub(r'\[\d+\]$', '', title).strip()

        if not title:
            continue

        # Build post URL
        if gallery_type == "mgallery":
            post_url = f"https://gall.dcinside.com/mgallery/board/view/?id=running&no={post_id}"
        else:
            post_url = f"https://gall.dcinside.com/board/view/?id=running&no={post_id}"

        # Author
        author_cell = row.select_one("td.gall_writer, td.ub-writer")
        author = ""
        if author_cell:
            author = author_cell.get("data-nick", "") or author_cell.get_text(strip=True)

        posts.append({
            "post_id": post_id,
            "title": title,
            "url": post_url,
            "author": author,
        })

    return posts

# --- Race detection ---
RACE_INCLUDE = [
    r'대회', r'마라톤', r'레이스', r'달리기\s*대회', r'접수', r'신청',
    r'엔트리', r'참가', r'요강', r'공고', r'일정', r'모집', r'등록',
    r'출전', r'개최', r'코스', r'하프', r'풀코스', r'10k', r'5k',
    r'\d+km', r'트레일', r'울트라', r'로드레이스',
]

RACE_EXCLUDE = [
    r'후기', r'다녀왔', r'완주기', r'완주\s*후기', r'인증', r'훈련',
    r'장비', r'식단', r'부상', r'잡담', r'짤', r'정치', r'뻘글',
    r'러닝화', r'워치', r'가민', r'팁', r'질문', r'추천',
    r'오늘', r'어제', r'오운완', r'페이스', r'km\s*뛰',
]

def is_race_related_by_title(title):
    t = title.lower()
    for pat in RACE_EXCLUDE:
        if re.search(pat, title, re.IGNORECASE):
            return False, "exclude"
    for pat in RACE_INCLUDE:
        if re.search(pat, title, re.IGNORECASE):
            return True, "include"
    return None, "ambiguous"

def fetch_post_body(post_url):
    try:
        resp = requests.get(post_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            body = soup.select_one("div.write_div, div.tbody, div#bo_v_con")
            if body:
                return body.get_text(" ", strip=True)[:2000]
    except Exception as e:
        print(f"Error fetching post body {post_url}: {e}")
    return ""

def is_race_related_by_body(body):
    for pat in RACE_EXCLUDE:
        if re.search(pat, body, re.IGNORECASE):
            return False
    for pat in RACE_INCLUDE:
        if re.search(pat, body, re.IGNORECASE):
            return True
    return False

# --- Telegram ---
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"Telegram error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"Telegram exception: {e}")
        return False

# --- Main ---
def main():
    seen_ids = load_state()
    was_empty = len(seen_ids) == 0
    seen_set = set(seen_ids)

    gallery_type, gallery_url, html = fetch_gallery()
    if not html:
        print("Failed to fetch gallery. Exiting.")
        sys.exit(0)

    posts = parse_posts(html, gallery_type, gallery_url)
    if not posts:
        print("Warning: Parsed 0 posts. Possible HTML structure change. Exiting without commit.")
        sys.exit(0)

    print(f"Parsed {len(posts)} posts from gallery.")

    # Determine new posts
    new_posts = [p for p in posts if p["post_id"] not in seen_set]
    print(f"New posts: {len(new_posts)}")

    # First-run protection
    if was_empty and len(new_posts) >= 20:
        all_ids = list(seen_ids) + [p["post_id"] for p in posts]
        save_state(all_ids)
        # commit & push
        subprocess.run(["git", "-C", "/home/user/endurohub", "add", "data/runninggal_seen.json"])
        subprocess.run([
            "git", "-C", "/home/user/endurohub",
            "-c", "user.email=routine@endurohub.local",
            "-c", "user.name=Runninggal Bot",
            "commit", "-m", "Update runninggal seen posts"
        ])
        result = subprocess.run(["git", "-C", "/home/user/endurohub", "push"])
        if result.returncode != 0:
            subprocess.run(["git", "-C", "/home/user/endurohub", "pull", "--rebase"])
            subprocess.run(["git", "-C", "/home/user/endurohub", "push"])
        print(f"First run: bootstrapped {len(posts)} ids")
        print(f"Checked {len(posts)} posts, {len(new_posts)} new, 0 race-related, sent 0 telegrams.")
        sys.exit(0)

    # Process new posts (max 30, newest first)
    to_process = new_posts[:30]
    body_fetches = 0
    race_posts = []
    evaluated_ids = []
    failed_race_ids = set()

    for post in to_process:
        if time_remaining() < 15:
            print("Approaching time limit, stopping evaluation.")
            break

        pid = post["post_id"]
        title = post["title"]

        decision, reason = is_race_related_by_title(title)

        if decision is None and body_fetches < 10 and time_remaining() > 20:
            print(f"  Ambiguous title '{title}', fetching body...")
            body = fetch_post_body(post["url"])
            body_fetches += 1
            decision = is_race_related_by_body(body)
            if not decision:
                decision = False

        if decision is True:
            race_posts.append(post)
            print(f"  RACE: [{pid}] {title}")
        else:
            evaluated_ids.append(pid)
            print(f"  skip: [{pid}] {title}")

    # Send Telegram messages
    gallery_list_url = gallery_url
    sends_ok = 0
    send_cap = 10

    race_to_send = race_posts[:send_cap]
    race_overflow = race_posts[send_cap:]

    for post in race_to_send:
        if time_remaining() < 5:
            print("Time limit: skipping remaining Telegram sends.")
            break
        msg = f"🏃 새로운 대회 글\n\n<b>{post['title']}</b>\nby {post['author']}\n{post['url']}"
        ok = send_telegram(msg)
        if ok:
            sends_ok += 1
            evaluated_ids.append(post["post_id"])
            print(f"  Sent telegram for [{post['post_id']}]")
        else:
            failed_race_ids.add(post["post_id"])
            print(f"  Failed to send telegram for [{post['post_id']}]")
        time.sleep(0.4)

    if race_overflow:
        summary = f"그 외 {len(race_overflow)}건 더 있음: {gallery_list_url}"
        ok = send_telegram(summary)
        if ok:
            sends_ok += 1
            for p in race_overflow:
                evaluated_ids.append(p["post_id"])
        print(f"  Sent overflow summary ({len(race_overflow)} posts)")
        time.sleep(0.4)

    # Update seen_ids
    all_new_seen = list(seen_ids) + evaluated_ids
    # Deduplicate preserving order
    seen_final = list(dict.fromkeys(all_new_seen))
    save_state(seen_final)

    # Commit & push
    subprocess.run(["git", "-C", "/home/user/endurohub", "add", "data/runninggal_seen.json"])
    commit_result = subprocess.run([
        "git", "-C", "/home/user/endurohub",
        "-c", "user.email=routine@endurohub.local",
        "-c", "user.name=Runninggal Bot",
        "commit", "-m", "Update runninggal seen posts"
    ], capture_output=True, text=True)
    if "nothing to commit" in commit_result.stdout + commit_result.stderr:
        print("Nothing to commit.")
    else:
        push_result = subprocess.run(["git", "-C", "/home/user/endurohub", "push"], capture_output=True, text=True)
        if push_result.returncode != 0:
            subprocess.run(["git", "-C", "/home/user/endurohub", "pull", "--rebase"])
            subprocess.run(["git", "-C", "/home/user/endurohub", "push"])

    total_checked = len(posts)
    total_new = len(new_posts)
    total_race = len(race_posts)
    print(f"Checked {total_checked} posts, {total_new} new, {total_race} race-related, sent {sends_ok} telegrams.")

if __name__ == "__main__":
    main()
