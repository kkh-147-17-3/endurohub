#!/usr/bin/env python3
import json
import os
import sys
import time
import re
import subprocess
import requests
from bs4 import BeautifulSoup

STATE_FILE = "data/runninggal_seen.json"
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
if not BOT_TOKEN or not CHAT_ID:
    sys.exit("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID 환경변수가 필요합니다.")
MAX_SENDS = 10
MAX_BODY_FETCHES = 10
MAX_PER_RUN = 30
MAX_SEEN = 500

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

RACE_KEYWORDS = [
    '대회', '마라톤', '달리기 대회', '10km', '하프', '풀코스',
    '접수', '신청', '모집', '엔트리', '참가', '요강', '공고', '일정 안내',
    '등록', '선착순', '조기마감', '대기자', '추첨',
]
RACE_PATTERNS = [
    r'대회\s*(일정|공고|요강|접수|안내|신청|모집)',
    r'(접수|신청|모집|엔트리)\s*(시작|오픈|안내)',
    r'참가\s*(신청|안내|모집)',
    r'(마라톤|울트라|트레일|로드)\s*(대회|레이스)',
    r'\d+[Kk]m',
    r'(하프|풀코스|10K|5K)',
]
EXCLUDE_KEYWORDS = [
    '후기', '다녀왔', '완주기', '완주했', '인증', '훈련', '장비', '식단',
    '부상', '잡담', '짤', '정치', '뻘글', '어떻게', '추천', '질문',
    '러닝화', '신발', '양말', '시계', '웨어', '복장',
]


def load_state():
    if not os.path.exists(STATE_FILE):
        return []
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("seen_post_ids", [])
    except Exception:
        return []


def save_state(seen_ids):
    seen_ids = seen_ids[-MAX_SEEN:]
    os.makedirs("data", exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen_post_ids": seen_ids}, f, ensure_ascii=False, indent=2)


def fetch_gallery():
    sources = [
        ("mgallery", "https://gall.dcinside.com/mgallery/board/lists/?id=running"),
        ("gallery", "https://gall.dcinside.com/board/lists/?id=running"),
    ]
    for gtype, url in sources:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200 and len(resp.text) > 1000:
                print(f"Fetched gallery from: {url}")
                return gtype, url, resp.text
            else:
                print(f"Got status {resp.status_code} from {url}, trying next.")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
    return None, None, None


def parse_posts(html, gtype):
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    # Try to find the post list table/rows
    rows = soup.select("tr.ub-content, tr[data-no]")
    if not rows:
        rows = soup.select("tbody tr")

    for row in rows:
        # Skip notice/ad rows
        row_class = " ".join(row.get("class", []))
        if "us-post" in row_class or "notice" in row_class:
            continue

        # Get post id
        post_id = row.get("data-no", "")
        if not post_id:
            # Try gall_num cell
            num_cell = row.select_one("td.gall_num, .gall_num")
            if num_cell:
                post_id = num_cell.get_text(strip=True)

        if not post_id or not post_id.isdigit():
            continue

        # Get title
        title_cell = row.select_one("td.gall_tit, .gall_tit")
        if not title_cell:
            continue

        title_link = title_cell.select_one("a")
        if not title_link:
            continue

        title = title_link.get_text(strip=True)
        # Remove comment count suffix like [5]
        title = re.sub(r'\s*\[\d+\]\s*$', '', title).strip()

        if not title:
            continue

        # Get author
        author_cell = row.select_one("td.gall_writer, .gall_writer, td.wr_name")
        author = "unknown"
        if author_cell:
            author = author_cell.get("data-nick", "") or author_cell.get_text(strip=True)

        # Build post URL
        if gtype == "mgallery":
            post_url = f"https://gall.dcinside.com/mgallery/board/view/?id=running&no={post_id}"
            list_base = "https://gall.dcinside.com/mgallery/board"
        else:
            post_url = f"https://gall.dcinside.com/board/view/?id=running&no={post_id}"
            list_base = "https://gall.dcinside.com/board"

        posts.append({
            "post_id": post_id,
            "title": title,
            "post_url": post_url,
            "author": author,
        })

    return posts


def is_race_related_by_title(title):
    title_lower = title.lower()

    # Check exclusion first
    for kw in EXCLUDE_KEYWORDS:
        if kw in title:
            return False, "exclude"

    # Check race patterns
    for pattern in RACE_PATTERNS:
        if re.search(pattern, title):
            return True, "pattern"

    # Check race keywords
    for kw in RACE_KEYWORDS:
        if kw in title:
            return True, "keyword"

    return None, "ambiguous"


def fetch_post_body(post_url):
    try:
        resp = requests.get(post_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            body = soup.select_one(".write_div, .thum-upload, .writing-view-box, #bo_v_con")
            if body:
                return body.get_text(" ", strip=True)[:2000]
            return resp.text[:2000]
    except Exception as e:
        print(f"Error fetching post body {post_url}: {e}")
    return ""


def is_race_related_by_body(body):
    for pattern in RACE_PATTERNS:
        if re.search(pattern, body):
            return True
    for kw in RACE_KEYWORDS[:8]:
        if kw in body:
            return True
    return False


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code == 200:
            return True
        else:
            print(f"Telegram send failed: {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"Telegram send error: {e}")
        return False


def commit_and_push():
    cmds = [
        ["git", "add", "data/runninggal_seen.json"],
        ["git", "-c", "user.email=routine@endurohub.local", "-c", "user.name=Runninggal Bot",
         "commit", "-m", "Update runninggal seen posts"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Git cmd output: {result.stdout} {result.stderr}")

    # Push with retry
    push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if push_result.returncode != 0:
        print("Push failed, trying pull --rebase then push...")
        subprocess.run(["git", "pull", "--rebase"], capture_output=True, text=True)
        push_result2 = subprocess.run(["git", "push"], capture_output=True, text=True)
        if push_result2.returncode != 0:
            print(f"Push still failed: {push_result2.stderr}")
        else:
            print("Push succeeded after rebase.")
    else:
        print("Push succeeded.")


def main():
    start_time = time.time()

    # 1. Load state
    seen_ids = load_state()
    was_empty = len(seen_ids) == 0
    seen_set = set(seen_ids)

    # 2. Fetch gallery
    gtype, list_url, html = fetch_gallery()
    if not html:
        print("ERROR: Could not fetch gallery. Exiting without state change.")
        return

    if gtype == "mgallery":
        gallery_list_url = "https://gall.dcinside.com/mgallery/board/lists/?id=running"
    else:
        gallery_list_url = "https://gall.dcinside.com/board/lists/?id=running"

    # 3. Parse posts
    posts = parse_posts(html, gtype)
    if not posts:
        print("WARNING: Parsed 0 posts. HTML structure may have changed. Exiting.")
        return

    print(f"Parsed {len(posts)} posts from gallery.")

    # 4. Find new posts
    new_posts = [p for p in posts if p["post_id"] not in seen_set]

    # 5. First-run protection
    if was_empty and len(new_posts) >= 20:
        all_ids = seen_ids + [p["post_id"] for p in posts]
        save_state(all_ids)
        commit_and_push()
        print(f"First run: bootstrapped {len(posts)} ids")
        return

    # Process at most 30 new posts, newest first
    new_posts_to_process = new_posts[:MAX_PER_RUN]

    race_posts = []
    non_race_ids = []
    body_fetches = 0

    for post in new_posts_to_process:
        if time.time() - start_time > 110:
            print("Approaching time limit, stopping evaluation.")
            break

        is_race, reason = is_race_related_by_title(post["title"])

        if is_race is None and body_fetches < MAX_BODY_FETCHES:
            # Ambiguous - fetch body
            body = fetch_post_body(post["post_url"])
            body_fetches += 1
            is_race = is_race_related_by_body(body)
            reason = "body"
        elif is_race is None:
            is_race = False
            reason = "ambiguous_skipped"

        print(f"  Post {post['post_id']}: {post['title'][:50]} -> {'RACE' if is_race else 'skip'} ({reason})")

        if is_race:
            race_posts.append(post)
        else:
            non_race_ids.append(post["post_id"])

    # 6-7. Send Telegram notifications
    sends_ok = 0
    failed_race_ids = set()
    telegram_ok = True

    if race_posts:
        to_send_individually = race_posts[:MAX_SENDS]
        overflow = race_posts[MAX_SENDS:]

        for post in to_send_individually:
            if time.time() - start_time > 110:
                break
            msg = (
                f"🏃 새로운 대회 글\n\n"
                f"<b>{post['title']}</b>\n"
                f"by {post['author']}\n"
                f"{post['post_url']}"
            )
            ok = send_telegram(msg)
            if ok:
                sends_ok += 1
            else:
                failed_race_ids.add(post["post_id"])
                telegram_ok = False
            time.sleep(0.4)

        if overflow:
            summary = f"그 외 {len(overflow)}건 더 있음: {gallery_list_url}"
            ok = send_telegram(summary)
            if ok:
                sends_ok += 1
            time.sleep(0.4)

    # 8. Update seen_post_ids
    # Add all evaluated posts EXCEPT those whose Telegram send failed
    successfully_evaluated_ids = (
        [p["post_id"] for p in race_posts if p["post_id"] not in failed_race_ids]
        + non_race_ids
    )

    new_seen = seen_ids + successfully_evaluated_ids
    # Deduplicate preserving order
    seen_dedup = list(dict.fromkeys(new_seen))
    save_state(seen_dedup)

    # 9. Commit and push
    commit_and_push()

    total_checked = len(posts)
    total_new = len(new_posts)
    total_race = len(race_posts)
    print(f"Checked {total_checked} posts, {total_new} new, {total_race} race-related, sent {sends_ok} telegrams.")


if __name__ == "__main__":
    main()
