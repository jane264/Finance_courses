import requests
import csv

# Coursera Courses API
url = (
    "https://api.coursera.org/api/courses.v1"
    "?start=0&limit=100000"
    "&includes=partnerIds"
    "&fields=id,name,slug,description,partnerIds"
)

response = requests.get(url)
data = response.json()

courses = data.get("elements", [])
linked = data.get("linked", {})
partners = linked.get("partners.v1", [])

# Build partnerId → partner name mapping
partner_map = {
    p["id"]: p.get("name", "Unknown")
    for p in partners
}

# =========================
# 🔹 SAVE UNFILTERED COURSES
# =========================
unfiltered_file = "coursera_all_courses_unfiltered.csv"

with open(unfiltered_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["course_id", "course_name", "author (partner)", "course_link"])

    for course in courses:
        course_id = course.get("id")
        name = course.get("name", "")
        slug = course.get("slug")

        if not course_id or not slug:
            continue

        course_url = f"https://www.coursera.org/learn/{slug}"
        partner_ids = course.get("partnerIds", [])
        authors = [partner_map.get(pid, "Unknown") for pid in partner_ids]
        author_str = ", ".join(authors)

        writer.writerow([course_id, name, author_str, course_url])

print(f"💾 Saved UNFILTERED courses to {unfiltered_file}")

# =========================
# 🔹 FINANCE KEYWORDS (UNCHANGED)
# =========================
finance_keywords = [
    "probability", "statistics", "regression","time series", "time", "series",
    "monte carlo", "hypothesis testing", "linear algebra","linear","algebra","time",
    "numerical methods", "time value of money", "discounted","cash","flow","mutual fund",
    "financial","markets", "equity","equity market", "money","market","asset","ipo",
    "forex", "bond", "derivatives", "options","banking","valuation","capital","etf",
    "hedging", "value at risk","VAT","finance","volatility","portfolio", "var", "stress testing",
    "volatility modeling", "portfolio management","investment", "investing", "trading", "stocks"
    "credit risk","credit","risk", "credit analysis", "cva","securities","budgeting ",
    "operational risk", "market risk", "liquidity risk","liquidity","wealth","economics",
    "esg", "fintech", "blockchain", "cryptocurrency","fund","account","accounting","corporate"]

finance_keywords = [k.lower() for k in finance_keywords]

# =========================
# 🔹 FILTER FINANCE COURSES
# =========================
finance_courses = {}

for course in courses:
    name = course.get("name", "")
    description = course.get("description", "")
    text = f"{name} {description}".lower()

    if any(keyword in text for keyword in finance_keywords):
        course_id = course.get("id")
        slug = course.get("slug")

        if not course_id or not slug:
            continue

        course_url = f"https://www.coursera.org/learn/{slug}"
        partner_ids = course.get("partnerIds", [])
        authors = [partner_map.get(pid, "Unknown") for pid in partner_ids]
        author_str = ", ".join(authors)

        finance_courses[course_id] = [
            course_id,
            name,
            author_str,
            course_url
        ]

finance_courses = list(finance_courses.values())

print(f"✅ Finance courses found: {len(finance_courses)}")

# =========================
# 🔹 SAVE FILTERED CSV
# =========================
filtered_file = "coursera_finance_courses_domain_filtered.csv"

with open(filtered_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["course_id", "course_name", "author (partner)", "course_link"])
    writer.writerows(finance_courses)

print(f"💾 Saved FILTERED finance courses to {filtered_file}")
