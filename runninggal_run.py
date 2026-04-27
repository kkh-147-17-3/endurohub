#!/usr/bin/env python3
import json, os, sys, time, re
import subprocess

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4", "--quiet"], check=True)
    import requests
    from bs4 import BeautifulSoup

STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "runninggal_seen.json")
BOT_TOKEN = "8701008789:AAGRxjKU4YZZmO5J3ShZ6tP3AnGfjMeAvqM"
CHAT_ID = "8581246573"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://gall.dcinside.com/",
}

RACE_KEYWORDS = [
    "대회", "마라톤", "레이스", "달리기대회", "런닝대회",
    "접수", "모집", "요강", "신청", "엔트리", "참가", "일정", "공고",
    "트레일", "울트라", "하프", "풀코스", "10km", "5km",
]
EXCLUDE_KEYWORDS = [
    "후기", "다녀왔", "완주기", "인증", "훈련", "장비", "식단",
    "부상", "잡담", "짤", "정치", "뻘글", "ㅋㅋ", "ㅠㅠ",
]

def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("seen_post_ids", [])
    except Exception:
        return []

def save_state(ids):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    ids = list(dict.fromkeys(ids))  # deduplicate, preserve order
    ids = ids[-500:]  # cap to 500 most recent
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen_post_ids": ids}, f, ensure_ascii=False, indent=2)

def fetch_gallery(session):
    urls = [
        ("mgallery", "https://gall.dcinside.com/mgallery/board/lists/?id=running"),
        ("gallery",  "https://gall.dcinside.com/board/lists/?id=running"),
    ]
    for gtype, url in urls:
        try:
            r = session.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                print(f"Fetched gallery from {url}")
                return gtype, url, r.text
        except Exception as e:
            print(f"Failed {url}: {e}")
    return None, None, None

def parse_posts(html, gtype):
    soup = BeautifulSoup(html, "html.parser")
    posts = []

    # Try multiple table selectors
    table = soup.select_one("table.gall_list")
    if not table:
        table = soup.select_one("tbody.listwrap")

    rows = []
    if table:
        rows = table.select("tr")
    else:
        rows = soup.select("tr.ub-content")

    if not rows:
        # broader fallback
        rows = soup.select("tr[data-no]")

    for row in rows:
        # Skip notices/ads by class
        row_class = " ".join(row.get("class", []))
        if any(c in row_class for c in ["us-post", "notice", "ad-post"]):
            continue

        # Get post id
        no_cell = row.select_one("td.gall_num")
        if not no_cell:
            no_cell = row.select_one("td.num")
        if not no_cell:
            # try data-no attribute
            data_no = row.get("data-no", "")
            if data_no and re.match(r"^\d+$", data_no.strip()):
                post_id = data_no.strip()
            else:
                continue
        else:
            raw = no_cell.get_text(strip=True)
            if not re.match(r"^\d+$", raw):
                continue
            post_id = raw

        # Get title
        title_cell = row.select_one("td.gall_tit a")
        if not title_cell:
            title_cell = row.select_one("td.title a")
        if not title_cell:
            title_cell = row.select_one("a.reply_num")
        if not title_cell:
            continue

        # Find the actual title link (not reply count link)
        title_links = row.select("td.gall_tit a, td.title a")
        title_link = None
        for lnk in title_links:
            href = lnk.get("href", "")
            if "view" in href or "no=" in href:
                title_link = lnk
                break
        if not title_link:
            # fallback: any link with the post no
            for lnk in row.select("a"):
                href = lnk.get("href", "")
                if f"no={post_id}" in href:
                    title_link = lnk
                    break
        if not title_link:
            title_link = title_cell

        title = title_link.get_text(strip=True)
        # Remove reply count suffix like [3]
        title = re.sub(r"\s*\[\d+\]$", "", title).strip()

        href = title_link.get("href", "")
        if href.startswith("http"):
            post_url = href
        elif href.startswith("/"):
            post_url = "https://gall.dcinside.com" + href
        else:
            base = "mgallery" if gtype == "mgallery" else "board"
            post_url = f"https://gall.dcinside.com/{base}/view/?id=running&no={post_id}"

        # Get author
        author_cell = row.select_one("td.gall_writer")
        if not author_cell:
            author_cell = row.select_one("td.writer")
        author = author_cell.get_text(strip=True) if author_cell else "unknown"

        posts.append({
            "post_id": post_id,
            "title": title,
            "url": post_url,
            "author": author,
        })

    return posts

def is_race_related_by_title(title):
    title_lower = title.lower()
    for kw in EXCLUDE_KEYWORDS:
        if kw in title:
            return False, "exclude"
    for kw in RACE_KEYWORDS:
        if kw in title:
            return True, "include"
    return None, "ambiguous"

def fetch_post_body(session, gtype, post_id):
    base = "mgallery" if gtype == "mgallery" else "board"
    url = f"https://gall.dcinside.com/{base}/view/?id=running&no={post_id}"
    try:
        r = session.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            body = soup.select_one("div.write_div") or soup.select_one("div.post-contents")
            if body:
                return body.get_text(strip=True)[:2000]
    except Exception as e:
        print(f"  Body fetch failed for {post_id}: {e}")
    return ""

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "false",
    }
    try:
        r = requests.post(url, data=data, timeout=10)
        if r.status_code == 200:
            return True
        else:
            print(f"  Telegram send failed: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        print(f"  Telegram send error: {e}")
        return False

def main():
    start_time = time.time()

    # 1. Load state
    seen_ids = load_state()
    was_empty = len(seen_ids) == 0
    seen_set = set(seen_ids)
    print(f"Loaded {len(seen_ids)} seen post IDs.")

    # 2. Fetch gallery
    session = requests.Session()
    gtype, list_url, html = fetch_gallery(session)
    if not html:
        print("Gallery fetch failed. Exiting.")
        sys.exit(0)

    # 3. Parse posts
    posts = parse_posts(html, gtype)
    if not posts:
        print("WARNING: Parsed 0 posts — possible HTML structure change. Exiting without commit.")
        sys.exit(0)
    print(f"Parsed {len(posts)} posts from gallery.")

    # 4. Find new posts
    new_posts = [p for p in posts if p["post_id"] not in seen_set]
    all_post_ids = [p["post_id"] for p in posts]
    print(f"New posts: {len(new_posts)}")

    # 4. First-run protection
    if was_empty and len(new_posts) >= 20:
        new_seen = list(seen_ids) + all_post_ids
        save_state(new_seen)
        subprocess.run(["git", "add", "data/runninggal_seen.json"], check=False)
        subprocess.run([
            "git", "-c", "user.email=routine@endurohub.local",
            "-c", "user.name=Runninggal Bot",
            "commit", "-m", "Update runninggal seen posts"
        ], check=False)
        subprocess.run(["git", "push"], check=False)
        print(f"First run: bootstrapped {len(all_post_ids)} ids")
        return

    # 5. Evaluate new posts (cap at 30, newest first)
    candidates = new_posts[:30]
    race_posts = []
    non_race_ids = []
    body_fetches = 0

    for post in candidates:
        if time.time() - start_time > 110:
            print("Approaching time limit, stopping evaluation.")
            break

        decision, reason = is_race_related_by_title(post["title"])

        if decision is None and body_fetches < 10:
            # Ambiguous: fetch body
            body = fetch_post_body(session, gtype, post["post_id"])
            body_fetches += 1
            decision_body, _ = is_race_related_by_title(body)
            if decision_body is True:
                decision = True
            elif decision_body is False:
                decision = False
            else:
                decision = False  # default ambiguous to non-race
        elif decision is None:
            decision = False

        if decision:
            race_posts.append(post)
            print(f"  RACE: [{post['post_id']}] {post['title']}")
        else:
            non_race_ids.append(post["post_id"])
            print(f"  skip: [{post['post_id']}] {post['title']}")

    # 6-7. Send Telegram messages
    sent_count = 0
    failed_race_ids = []
    gallery_list_url = list_url

    to_send = race_posts[:10]
    overflow = race_posts[10:]

    for post in to_send:
        if time.time() - start_time > 115:
            print("Time limit reached, stopping Telegram sends.")
            break
        msg = (
            f"🏃 새로운 대회 글\n\n"
            f"<b>{post['title']}</b>\n"
            f"by {post['author']}\n"
            f"{post['url']}"
        )
        ok = send_telegram(msg)
        if ok:
            sent_count += 1
        else:
            failed_race_ids.append(post["post_id"])
        time.sleep(0.4)

    if overflow:
        summary = f"그 외 {len(overflow)}건 더 있음: {gallery_list_url}"
        ok = send_telegram(summary)
        if ok:
            sent_count += 1
        time.sleep(0.4)

    # 8. Update seen_post_ids
    # Add all evaluated posts EXCEPT failed Telegram sends (race posts only)
    failed_set = set(failed_race_ids)
    newly_seen = []
    for post in candidates:
        if post["post_id"] not in failed_set:
            newly_seen.append(post["post_id"])

    updated_seen = list(seen_ids) + newly_seen
    # Also add non-new posts from current page to refresh recency
    for pid in all_post_ids:
        if pid not in set(updated_seen):
            updated_seen.append(pid)

    save_state(updated_seen)

    # 9. Commit and push
    subprocess.run(["git", "add", "data/runninggal_seen.json"], check=False)
    result = subprocess.run([
        "git", "-c", "user.email=routine@endurohub.local",
        "-c", "user.name=Runninggal Bot",
        "commit", "-m", "Update runninggal seen posts"
    ], capture_output=True, text=True)
    if "nothing to commit" in result.stdout + result.stderr:
        print("Nothing to commit.")
    else:
        print(f"Committed: {result.stdout.strip()}")
        push_result = subprocess.run(["git", "push", "-u", "origin", "HEAD"], capture_output=True, text=True)
        if push_result.returncode != 0:
            print(f"Push failed, trying pull+rebase: {push_result.stderr[:100]}")
            subprocess.run(["git", "pull", "--rebase"], check=False)
            subprocess.run(["git", "push", "-u", "origin", "HEAD"], check=False)
        else:
            print("Pushed successfully.")

    total_checked = len(posts)
    total_new = len(new_posts)
    total_race = len(race_posts)
    print(f"Checked {total_checked} posts, {total_new} new, {total_race} race-related, sent {sent_count} telegrams.")

if __name__ == "__main__":
    main()
