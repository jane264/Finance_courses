import json
import time
import random
import csv
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

URL = "https://www.udemy.com/courses/search/?q=finance+courses"
MAX_PAGES = 417

DATA_JSON = "courses_all_pages.json"
DATA_CSV = "courses_all_pages.csv"
CHECKPOINT_FILE = "checkpoint.json"


def human_sleep(a=1.5, b=3.0):
    time.sleep(random.uniform(a, b))


def save_checkpoint(page_no, global_index):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(
            {
                "last_page": page_no,
                "global_index": global_index
            },
            f,
            indent=2
        )


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"last_page": 0, "global_index": 1}


def save_results(results):
    # JSON
    with open(DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # CSV
    with open(DATA_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["index", "title", "description", "author", "course_url"]
        )
        writer.writeheader()
        writer.writerows(results)


def scrape_page(html, results, start_index):
    soup = BeautifulSoup(html, "html.parser")
    course_boxes = soup.select("div.content-grid-item-module--item--MDYzd")

    idx = start_index

    for box in course_boxes:
        title_el = box.select_one(".card-title-module--clipped--DPJnT")
        desc_el = box.select_one(
            'span[data-purpose="safely-set-inner-html:course-card:course-headline"]'
        )
        author_el = box.select_one(
            'span[data-purpose="safely-set-inner-html:course-card:visible-instructors"]'
        )
        link_el = box.select_one('a[href^="/course/"]')

        course_url = (
            "https://www.udemy.com" + link_el["href"]
            if link_el and link_el.has_attr("href")
            else None
        )

        if not title_el and not course_url:
            continue

        results.append({
            "index": idx,
            "title": title_el.get_text(strip=True) if title_el else None,
            "description": desc_el.get_text(" ", strip=True) if desc_el else None,
            "author": author_el.get_text(" ", strip=True) if author_el else None,
            "course_url": course_url,
        })

        idx += 1

    return idx


def main():
    checkpoint = load_checkpoint()
    start_page = checkpoint["last_page"] + 1
    global_index = checkpoint["global_index"]

    results = []

    # Load existing results if resuming
    if os.path.exists(DATA_JSON):
        with open(DATA_JSON, "r", encoding="utf-8") as f:
            results = json.load(f)

    last_successful_page = checkpoint["last_page"]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ],
            )

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )

            page = context.new_page()

            for page_no in range(start_page, MAX_PAGES + 1):
                page_url = f"{URL}&p={page_no}"
                print(f"🔵 Scraping page {page_no}")

                page.goto(page_url, timeout=60000)
                human_sleep()

                for _ in range(4):
                    page.mouse.wheel(0, 2500)
                    human_sleep()

                page.wait_for_load_state("networkidle", timeout=30000)

                html = page.content()
                global_index = scrape_page(html, results, global_index)

                # ✅ SAVE AFTER EACH PAGE
                save_results(results)
                save_checkpoint(page_no, global_index)

                last_successful_page = page_no
                print(f"✅ Page {page_no} saved successfully")

                human_sleep(2.0, 4.0)

            browser.close()

    except Exception as e:
        print("❌ Script terminated unexpectedly!")
        print(f"⚠️ Reason: {e}")

    finally:
        print(f"📌 Last successfully scraped page: {last_successful_page}")
        print(f"📊 Total courses saved: {len(results)}")


if __name__ == "__main__":
    main()
