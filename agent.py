import os
import re
import html
import json
import time
from pathlib import Path
from datetime import datetime, timezone

import requests


# ============================================================
# SETTINGS
# ============================================================

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

MODEL = "openrouter/free"

AFFILIATE_LINK = (
    "https://www.advancedbionutritionals.com/DS24/Advanced-Amino/"
    "Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld"
)

SITE_NAME = "StrongerYears"
SITE_URL = "https://rasghsims.github.io/affiliate-agent"

CONTENT_DIR = "content"
ASSET_DIR = os.path.join(CONTENT_DIR, "assets")

DISCLOSURE = (
    "I may earn a commission if you buy through links on this page, "
    "at no extra cost to you."
)


# ============================================================
# REAL PHOTO LIBRARY
# ============================================================
#
# These are direct Unsplash image files.
# No image API, no API key, no paid service.
# ============================================================

PHOTO_LIBRARY = {
    "strength": [
        "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1800&q=85",
    ],
    "muscle": [
        "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1599058917212-d750089bc07e?auto=format&fit=crop&w=1800&q=85",
    ],
    "walking": [
        "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?auto=format&fit=crop&w=1800&q=85",
    ],
    "nutrition": [
        "https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=1800&q=85",
    ],
    "healthy-aging": [
        "https://images.unsplash.com/photo-1544005313-94ddf0286df2?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1800&q=85",
    ],
    "recovery": [
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1800&q=85",
    ],
    "energy": [
        "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1800&q=85",
    ],
    "wellness": [
        "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1800&q=85",
        "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?auto=format&fit=crop&w=1800&q=85",
    ],
}


# ============================================================
# TOPICS
# ============================================================

TOPICS = [
    "Simple ways to support muscle recovery after 50",
    "Everyday nutrition habits that help preserve strength after 50",
    "How walking can support strength and healthy aging",
    "Practical ways to stay active as you get older",
    "Simple habits that support energy and vitality after 50",
    "How protein fits into a healthy aging routine",
    "Daily movement habits for maintaining strength after 50",
    "How recovery becomes more important with age",
    "Simple wellness habits for healthy aging",
    "Ways to make an active lifestyle easier after 50",
    "How strength training supports healthy aging",
    "Healthy routines that support muscle and mobility",
]


# ============================================================
# HELPERS
# ============================================================

def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"`(.*?)`", r"\1", text)

    return text.strip()


def existing_titles():
    titles = []

    if not os.path.exists(CONTENT_DIR):
        return titles

    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith(".html"):
            continue

        path = os.path.join(CONTENT_DIR, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            match = re.search(
                r"<title>(.*?)</title>",
                text,
                flags=re.I | re.S,
            )

            if match:
                title = re.sub(r"\s+", " ", match.group(1)).strip()
                titles.append(html.unescape(title))

        except Exception:
            pass

    return titles


# ============================================================
# PHOTO SELECTION
# ============================================================

def choose_photo(title):
    """
    Selects a real photographic image based on article topic.
    """

    t = title.lower()

    if any(x in t for x in [
        "muscle",
        "strength",
        "protein",
        "training",
        "workout",
    ]):
        category = "muscle"

    elif any(x in t for x in [
        "recover",
        "recovery",
        "rest",
    ]):
        category = "recovery"

    elif any(x in t for x in [
        "walk",
        "walking",
        "mobility",
        "movement",
        "active",
        "hiking",
    ]):
        category = "walking"

    elif any(x in t for x in [
        "nutrition",
        "food",
        "protein",
        "diet",
        "eating",
    ]):
        category = "nutrition"

    elif any(x in t for x in [
        "energy",
        "vitality",
    ]):
        category = "energy"

    elif any(x in t for x in [
        "aging",
        "older",
        "age",
        "longevity",
    ]):
        category = "healthy-aging"

    else:
        category = "wellness"

    # Rotate photos so every article doesn't get the same image.
    bucket = PHOTO_LIBRARY[category]

    index = len(existing_titles()) % len(bucket)

    return bucket[index], category


# ============================================================
# OPENROUTER
# ============================================================

def ask_ai(prompt):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is missing.")

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful wellness content writer. "
                    "Write useful, original, practical content. "
                    "Do not make medical treatment or cure claims. "
                    "Do not invent reviews, testimonials, studies, "
                    "statistics, doctors, or personal experiences. "
                    "Do not mention that you are an AI."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.7,
        "max_tokens": 2200,
    }

    last_error = None

    for attempt in range(4):

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=90,
            )

            response.raise_for_status()

            data = response.json()

            return data["choices"][0]["message"]["content"]

        except Exception as e:
            last_error = e

            if attempt < 3:
                time.sleep(5 * (attempt + 1))

    raise RuntimeError(
        f"OpenRouter request failed after retries: {last_error}"
    )


# ============================================================
# ARTICLE GENERATION
# ============================================================

def generate_article(topic, old_titles):

    prompt = f"""
Write a premium, useful wellness article for adults 50+.

Topic:
{topic}

Existing article titles:
{json.dumps(old_titles[-30:], ensure_ascii=False)}

Do not create a title that is substantially similar to an existing title.

Return ONLY this structure:

TITLE:
A compelling natural article title

INTRO:
2 short paragraphs

SECTION:
Heading
Paragraphs

SECTION:
Heading
Paragraphs

SECTION:
Heading
Paragraphs

PRACTICAL STEPS:
- practical step
- practical step
- practical step
- practical step
- practical step

FINAL:
A short encouraging conclusion

Rules:
- 900 to 1300 words.
- Clear American English.
- Useful rather than generic.
- No fake statistics.
- No fake testimonials.
- No disease-treatment claims.
- No cure claims.
- No guaranteed results.
- Do not overuse the keyword.
- Do not mention the affiliate product until the final CTA.
"""

    raw = ask_ai(prompt)

    title_match = re.search(
        r"TITLE:\s*(.+)",
        raw,
        flags=re.I,
    )

    if title_match:
        title = clean_text(title_match.group(1))
    else:
        title = topic

    return title, raw


# ============================================================
# MARKDOWN -> HTML
# ============================================================

def inline_format(text):

    text = html.escape(text)

    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<strong>\1</strong>",
        text,
    )

    text = re.sub(
        r"\*(.+?)\*",
        r"<em>\1</em>",
        text,
    )

    return text


def markdown_to_html(raw):

    lines = raw.splitlines()

    output = []

    skip = False

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        if re.match(r"^TITLE:\s*", stripped, re.I):
            continue

        if re.match(r"^(INTRO|FINAL):\s*$", stripped, re.I):
            continue

        if stripped.upper().startswith("SECTION:"):
            continue

        if stripped.upper().startswith("PRACTICAL STEPS:"):
            output.append(
                "<h2>Simple steps to try</h2>"
            )
            continue

        if stripped.startswith("- "):
            output.append(
                "<li>" +
                inline_format(stripped[2:]) +
                "</li>"
            )
            continue

        if (
            len(stripped) < 90
            and not stripped.endswith(".")
            and not stripped.startswith("<")
        ):
            output.append(
                "<h2>" +
                inline_format(
                    clean_text(stripped)
                ) +
                "</h2>"
            )
            continue

        output.append(
            "<p>" +
            inline_format(
                clean_text(stripped)
            ) +
            "</p>"
        )

    # Group consecutive li elements.
    final = []
    in_list = False

    for item in output:

        if item.startswith("<li>"):

            if not in_list:
                final.append("<ul>")
                in_list = True

            final.append(item)

        else:

            if in_list:
                final.append("</ul>")
                in_list = False

            final.append(item)

    if in_list:
        final.append("</ul>")

    return "\n".join(final)


# ============================================================
# ARTICLE HTML
# ============================================================

def build_article(title, raw, photo_url):

    body = markdown_to_html(raw)

    slug = slugify(title)

    published = datetime.now(
        timezone.utc
    ).strftime("%B %d, %Y")

    canonical = f"{SITE_URL}/content/{slug}.html"

    return f"""<!doctype html>
<html lang="en">
<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>{html.escape(title)} | {SITE_NAME}</title>

<meta name="description"
      content="{html.escape(title)} — practical habits for strength, mobility, recovery and healthy aging.">

<link rel="canonical"
      href="{canonical}">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f7f8f5;
    color: #182019;
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
    line-height: 1.75;
}}

.nav {{
    max-width: 1180px;
    margin: auto;
    padding: 26px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

.nav a {{
    color: #182019;
    text-decoration: none;
    font-weight: 600;
}}

.hero {{
    max-width: 1180px;
    margin: 10px auto 0;
    padding: 0 28px 55px;
}}

.hero-image {{
    width: 100%;
    height: min(62vw, 620px);
    min-height: 360px;
    object-fit: cover;
    border-radius: 30px;
    display: block;
}}

.kicker {{
    margin-top: 45px;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 12px;
    font-weight: 800;
    color: #58705d;
}}

h1 {{
    max-width: 950px;
    font-size: clamp(42px, 7vw, 82px);
    line-height: 0.98;
    letter-spacing: -4px;
    margin: 15px 0 24px;
}}

.date {{
    color: #68716a;
}}

.article {{
    max-width: 820px;
    margin: auto;
    padding: 30px 28px 100px;
}}

.article p {{
    font-size: 19px;
    margin: 0 0 25px;
}}

.article h2 {{
    font-size: 32px;
    line-height: 1.1;
    letter-spacing: -1px;
    margin: 55px 0 20px;
}}

.article ul {{
    padding-left: 25px;
    font-size: 18px;
}}

.cta {{
    margin-top: 65px;
    padding: 38px;
    border-radius: 24px;
    background: #182019;
    color: white;
}}

.cta h2 {{
    margin-top: 0;
    color: white;
}}

.cta a {{
    display: inline-block;
    margin-top: 12px;
    padding: 15px 22px;
    border-radius: 999px;
    background: white;
    color: #182019;
    text-decoration: none;
    font-weight: 800;
}}

.disclosure {{
    margin-top: 20px;
    font-size: 12px;
    color: #8a918b;
}}

footer {{
    max-width: 1180px;
    margin: auto;
    padding: 30px 28px 60px;
    color: #737b75;
    font-size: 13px;
}}

@media(max-width:700px) {{

    .nav {{
        padding: 20px;
    }}

    .hero {{
        padding: 0 16px 35px;
    }}

    .hero-image {{
        min-height: 300px;
        border-radius: 22px;
    }}

    h1 {{
        letter-spacing: -2.5px;
    }}

    .article {{
        padding-left: 20px;
        padding-right: 20px;
    }}

    .article p {{
        font-size: 17px;
    }}

}}

</style>

</head>

<body>

<nav class="nav">

<div class="logo">
{SITE_NAME}
</div>

<a href="{SITE_URL}/">
Guides
</a>

</nav>

<header class="hero">

<img
    class="hero-image"
    src="{photo_url}"
    alt="Healthy active lifestyle"
    loading="eager"
>

<div class="kicker">
Healthy aging guide
</div>

<h1>
{html.escape(title)}
</h1>

<div class="date">
Published {published}
</div>

</header>

<main class="article">

{body}

<section class="cta">

<h2>
Build a stronger everyday routine.
</h2>

<p>
If you're exploring nutrition and amino-acid support
alongside good food, movement and recovery habits,
you can learn more about the formula here.
</p>

<a
    href="{AFFILIATE_LINK}"
    target="_blank"
    rel="nofollow sponsored noopener"
>
Explore the Formula →
</a>

<div class="disclosure">
{DISCLOSURE}
</div>

</section>

</main>

<footer>
© 2026 {SITE_NAME}
</footer>

</body>
</html>
"""


# ============================================================
# HOMEPAGE
# ============================================================

def get_articles():

    articles = []

    if not os.path.exists(CONTENT_DIR):
        return articles

    for filename in os.listdir(CONTENT_DIR):

        if not filename.endswith(".html"):
            continue

        path = os.path.join(CONTENT_DIR, filename)

        try:

            with open(path, "r", encoding="utf-8") as f:
                text = f.read()

            title_match = re.search(
                r"<title>(.*?)</title>",
                text,
                flags=re.I | re.S,
            )

            if not title_match:
                continue

            title = html.unescape(
                title_match.group(1)
            )

            title = title.split("|")[0].strip()

            articles.append(
                {
                    "title": title,
                    "url": f"{CONTENT_DIR}/{filename}",
                }
            )

        except Exception:
            pass

    return articles


def build_homepage():

    articles = get_articles()

    cards = ""

    for article in articles[:12]:

        photo, _ = choose_photo(
            article["title"]
        )

        cards += f"""
        <article class="card">

            <img
                src="{photo}"
                alt="{html.escape(article["title"])}"
                loading="lazy"
            >

            <div class="card-body">

                <div class="small">
                    GUIDE
                </div>

                <h3>
                    {html.escape(article["title"])}
                </h3>

                <a href="../{article["url"]}">
                    Read guide →
                </a>

            </div>

        </article>
        """

    if not cards:

        cards = """
        <div class="empty">
            New guides are being prepared.
        </div>
        """

    html_page = f"""<!doctype html>
<html lang="en">

<head>

<meta charset="utf-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1">

<title>
{SITE_NAME} — Age well. Live strong.
</title>

<meta name="description"
      content="Practical guides for strength, movement, recovery and healthy aging.">

<link rel="canonical"
      href="{SITE_URL}/">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f7f8f5;
    color: #182019;
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}}

.nav {{
    max-width: 1250px;
    margin: auto;
    padding: 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 21px;
    font-weight: 850;
}}

.nav a {{
    color: #182019;
    text-decoration: none;
    font-weight: 700;
}}

.hero {{
    max-width: 1250px;
    margin: auto;
    padding: 25px 28px 100px;
}}

.hero-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 55px;
    align-items: center;
}}

.hero-copy h1 {{
    font-size: clamp(55px, 8vw, 108px);
    line-height: .9;
    letter-spacing: -6px;
    margin: 0 0 30px;
}}

.hero-copy p {{
    max-width: 570px;
    color: #657068;
    font-size: 20px;
    line-height: 1.6;
}}

.hero-photo {{
    width: 100%;
    height: 650px;
    object-fit: cover;
    border-radius: 34px;
    display: block;
}}

.eyebrow {{
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 12px;
    font-weight: 800;
    color: #58705d;
    margin-bottom: 20px;
}}

.button {{
    display: inline-block;
    margin-top: 15px;
    background: #182019;
    color: white;
    text-decoration: none;
    padding: 16px 25px;
    border-radius: 999px;
    font-weight: 800;
}}

.section {{
    max-width: 1250px;
    margin: auto;
    padding: 40px 28px 110px;
}}

.section-heading {{
    max-width: 700px;
    margin-bottom: 50px;
}}

.section-heading h2 {{
    font-size: clamp(40px, 5vw, 70px);
    line-height: 1;
    letter-spacing: -3px;
    margin: 0 0 20px;
}}

.section-heading p {{
    color: #657068;
    font-size: 18px;
    line-height: 1.6;
}}

.grid {{
    display: grid;
    grid-template-columns:
        repeat(3, minmax(0, 1fr));
    gap: 22px;
}}

.card {{
    overflow: hidden;
    background: white;
    border-radius: 25px;
    box-shadow:
        0 15px 45px rgba(20,30,20,.07);
}}

.card img {{
    width: 100%;
    height: 250px;
    object-fit: cover;
    display: block;
}}

.card-body {{
    padding: 27px;
}}

.small {{
    color: #748077;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.5px;
}}

.card h3 {{
    font-size: 25px;
    line-height: 1.12;
    letter-spacing: -.8px;
    margin: 12px 0 25px;
}}

.card a {{
    color: #182019;
    text-decoration: none;
    font-weight: 800;
}}

.cta {{
    max-width: 1250px;
    margin: 0 auto 80px;
    padding: 70px 50px;
    border-radius: 34px;
    background: #182019;
    color: white;
}}

.cta h2 {{
    max-width: 800px;
    font-size: clamp(40px, 5vw, 70px);
    line-height: 1;
    letter-spacing: -3px;
    margin: 0 0 22px;
}}

.cta p {{
    max-width: 650px;
    color: #cbd2cc;
    font-size: 18px;
    line-height: 1.6;
}}

.cta a {{
    display: inline-block;
    margin-top: 15px;
    background: white;
    color: #182019;
    text-decoration: none;
    padding: 16px 25px;
    border-radius: 999px;
    font-weight: 800;
}}

.disclosure {{
    margin-top: 22px;
    color: #9da69f;
    font-size: 12px;
}}

footer {{
    max-width: 1250px;
    margin: auto;
    padding: 30px 28px 70px;
    color: #778078;
    font-size: 13px;
}}

@media(max-width:850px) {{

    .hero-grid {{
        grid-template-columns: 1fr;
    }}

    .hero-photo {{
        height: 450px;
    }}

    .grid {{
        grid-template-columns: 1fr;
    }}

    .cta {{
        margin-left: 16px;
        margin-right: 16px;
        padding: 45px 28px;
    }}

}}

</style>

</head>

<body>

<nav class="nav">

<div class="logo">
{SITE_NAME}
</div>

<a href="#guides">
Guides
</a>

</nav>

<header class="hero">

<div class="hero-grid">

<div class="hero-copy">

<div class="eyebrow">
Strength · Movement · Recovery
</div>

<h1>
Age well.<br>
Live strong.
</h1>

<p>
Practical, evidence-aware guides for building
strength, supporting recovery and making healthy
aging part of everyday life.
</p>

<a class="button" href="#guides">
Explore the guides ↓
</a>

</div>

<div>

<img
    class="hero-photo"
    src="https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=1800&q=85"
    alt="Active older adult enjoying an outdoor lifestyle"
>

</div>

</div>

</header>


<section class="section" id="guides">

<div class="section-heading">

<div class="eyebrow">
The StrongerYears Journal
</div>

<h2>
Strength is something you can keep building.
</h2>

<p>
Explore practical guides covering movement,
nutrition, recovery, energy and healthy aging.
</p>

</div>

<div class="grid">

{cards}

</div>

</section>


<section class="cta">

<h2>
Make your everyday habits work harder.
</h2>

<p>
Good nutrition, regular movement and recovery
all work together. If you're also exploring
amino-acid support, learn more about the formula.
</p>

<a
    href="{AFFILIATE_LINK}"
    target="_blank"
    rel="nofollow sponsored noopener"
>
Explore the Formula →
</a>

<div class="disclosure">
{DISCLOSURE}
</div>

</section>


<footer>
© 2026 {SITE_NAME}
</footer>

</body>

</html>
"""

    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(html_page)


# ============================================================
# SITEMAP
# ============================================================

def build_sitemap():

    urls = [
        f"{SITE_URL}/"
    ]

    if os.path.exists(CONTENT_DIR):

        for filename in os.listdir(CONTENT_DIR):

            if filename.endswith(".html"):

                urls.append(
                    f"{SITE_URL}/{CONTENT_DIR}/{filename}"
                )

    items = []

    for url in urls:

        items.append(
            f"""
    <url>
        <loc>{html.escape(url)}</loc>
    </url>
"""
        )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>

<urlset
xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

{"".join(items)}

</urlset>
"""

    with open(
        "sitemap.xml",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(sitemap)


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(CONTENT_DIR, exist_ok=True)
    os.makedirs(ASSET_DIR, exist_ok=True)

    old_titles = existing_titles()

    print(
        "Existing articles:",
        len(old_titles)
    )

    generated = False

    for topic in TOPICS:

        print(
            "Trying topic:",
            topic
        )

        try:

            title, raw = generate_article(
                topic,
                old_titles
            )

            title_clean = clean_text(title)

            if any(
                title_clean.lower()
                == old.lower()
                for old in old_titles
            ):
                print(
                    "Duplicate title, skipping:",
                    title_clean
                )
                continue

            photo_url, category = choose_photo(
                title_clean
            )

            print(
                "Generated article:",
                title_clean
            )

            article = build_article(
                title_clean,
                raw,
                photo_url
            )

            slug = slugify(title_clean)

            filename = (
                f"{slug}.html"
            )

            path = os.path.join(
                CONTENT_DIR,
                filename
            )

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:

                f.write(article)

            print(
                "Saved:",
                path
            )

            generated = True

            break

        except Exception as e:

            print(
                "Topic failed:",
                repr(e)
            )

    build_homepage()
    build_sitemap()

    print(
        "Homepage updated."
    )

    print(
        "Sitemap updated."
    )

    if not generated:

        print(
            "No new article generated this run."
        )

    print(
        "DONE"
    )


if __name__ == "__main__":
    main()
