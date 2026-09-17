import os
import re
import time
import html
import requests
from datetime import datetime

# =========================================================
# SETTINGS
# =========================================================

API_KEY = os.environ["OPENROUTER_API_KEY"]

AFFILIATE_LINK = (
    "https://www.advancedbionutritionals.com/DS24/Advanced-Amino/"
    "Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld"
)

SITE_NAME = "StrongerYears"

# Pinterest website verification
PINTEREST_VERIFY = "<meta name=\"p:domain_verify\" content=\"f016855977a15f47f6a69d0278378f96\"/>"

DISCLOSURE = (
    "I may earn a commission if you buy through links on this page, "
    "at no extra cost to you."
)

CONTENT_DIR = "content"

MODEL = "openrouter/free"

# =========================================================
# VISUAL IMAGES
# =========================================================

HERO_IMAGE = (
    "https://images.unsplash.com/photo-1538805060514-97d9cc17730c"
    "?auto=format&fit=crop&w=2200&q=85"
)

STORY_IMAGE = (
    "https://images.unsplash.com/photo-1517836357463-d25dfeac3438"
    "?auto=format&fit=crop&w=1400&q=85"
)

MOUNTAIN_IMAGE = (
    "https://images.unsplash.com/photo-1551632811-561732d1e306"
    "?auto=format&fit=crop&w=1800&q=85"
)

CARD_IMAGES = [
    (
        "https://images.unsplash.com/photo-1538805060514-97d9cc17730c"
        "?auto=format&fit=crop&w=1200&q=82"
    ),
    (
        "https://images.unsplash.com/photo-1547592180-85f173990554"
        "?auto=format&fit=crop&w=1200&q=82"
    ),
    (
        "https://images.unsplash.com/photo-1534438327276-14e5300c3a48"
        "?auto=format&fit=crop&w=1200&q=82"
    ),
    (
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b"
        "?auto=format&fit=crop&w=1200&q=82"
    ),
]

# =========================================================
# BUYER-INTENT TOPICS
# =========================================================

TOPICS = [
    "How to maintain muscle strength as you age",
    "Simple ways to support muscle recovery after 50",
    "Why maintaining muscle matters as you get older",
    "Daily habits that support strength and mobility after 50",
    "How protein and amino acids fit into healthy aging",
    "How to build a simple muscle-support routine after 50",
    "What active adults over 50 should know about muscle recovery",
    "Practical nutrition habits for maintaining strength with age",
    "How resistance exercise and nutrition work together for healthy aging",
    "A simple morning routine for strength and vitality after 50",
    "How to stay active and support muscle as you age",
    "Healthy aging habits that support strength, energy and mobility",
]

# =========================================================
# AI REQUEST
# =========================================================

def ask_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://rasghsims.github.io/affiliate-agent/",
        "X-Title": SITE_NAME,
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert wellness content writer. "
                    "Create useful, original and readable educational content "
                    "for adults interested in healthy aging, strength, mobility, "
                    "nutrition, recovery and vitality. "
                    "Never invent studies, statistics, doctors, testimonials, "
                    "reviews or guarantees. "
                    "Do not make disease treatment or cure claims. "
                    "Do not use fear-based marketing or fake urgency. "
                    "Do not use miracle or guaranteed-result language."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.7,
    }

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

            print(
                f"AI request failed "
                f"(attempt {attempt + 1}/4): {e}"
            )

            if attempt < 3:
                time.sleep(5 * (attempt + 1))
            else:
                raise


# =========================================================
# HELPERS
# =========================================================

def clean_text(text):

    text = text.replace("\r", "")

    text = re.sub(
        r"```(?:html|markdown)?",
        "",
        text,
        flags=re.I,
    )

    text = text.replace("```", "")

    return text.strip()


def slugify(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9]+",
        "-",
        text,
    )

    text = re.sub(
        r"-+",
        "-",
        text,
    )

    return text.strip("-")[:80]


def get_existing_titles():

    titles = []

    if not os.path.exists(CONTENT_DIR):
        return titles

    for filename in os.listdir(CONTENT_DIR):

        if not filename.endswith(".html"):
            continue

        path = os.path.join(
            CONTENT_DIR,
            filename,
        )

        try:

            with open(
                path,
                "r",
                encoding="utf-8",
            ) as f:

                content = f.read()

            match = re.search(
                r"<title>(.*?)</title>",
                content,
                flags=re.I | re.S,
            )

            if match:

                title = re.sub(
                    r"\s+",
                    " ",
                    match.group(1),
                ).strip()

                titles.append(
                    title.lower()
                )

        except Exception:
            pass

    return titles


# =========================================================
# ARTICLE GENERATOR
# =========================================================

def generate_article(topic, existing_titles):

    prompt = f"""
Create a high-quality original article about:

"{topic}"

Audience:
Adults 50+ in the United States who are interested in
strength, mobility, recovery, nutrition and healthy aging.

Requirements:

- 1200–1600 words.
- Give it a strong, natural title.
- Start with an engaging introduction.
- Use H2 and H3 sections.
- Use short readable paragraphs.
- Include practical advice.
- Include a simple checklist.
- Explain why maintaining muscle and an active lifestyle matters.
- Explain how nutrition can support an active lifestyle.
- Explain the role amino acids can play in nutrition without exaggeration.
- Mention that supplements are optional and not a replacement for a balanced diet.
- Do not claim any supplement treats, cures, prevents or reverses disease.
- Do not invent studies, statistics or medical authorities.
- Do not create fake testimonials.
- Do not create fake reviews.
- Do not promise specific results.
- Do not use fake scarcity or urgency.
- Do not use words like miracle, guaranteed, secret cure or instant results.
- End with a natural optional recommendation for readers who want
  to explore amino-acid nutrition further.

Do not mention these instructions.

Existing titles:

{existing_titles[:30]}

Create a substantially different title from existing articles.
"""

    raw = clean_text(
        ask_ai(prompt)
    )

    lines = raw.splitlines()

    title = None

    for line in lines:

        cleaned = re.sub(
            r"^#+\s*",
            "",
            line,
        ).strip()

        if cleaned:

            title = cleaned
            break

    if not title:
        title = topic

    body_lines = lines[:]

    if body_lines:

        first = re.sub(
            r"^#+\s*",
            "",
            body_lines[0],
        ).strip()

        if first.lower() == title.lower():

            body_lines = body_lines[1:]

    body = "\n".join(
        body_lines
    ).strip()

    if title.lower() in existing_titles:
        return None, None

    return title, body


# =========================================================
# MARKDOWN TO HTML
# =========================================================

def markdown_to_html(text):

    lines = text.splitlines()

    output = []

    paragraph = []

    in_list = False

    def flush_paragraph():

        nonlocal paragraph

        if paragraph:

            joined = " ".join(
                x.strip()
                for x in paragraph
            ).strip()

            if joined:

                output.append(
                    "<p>"
                    + html.escape(joined)
                    + "</p>"
                )

            paragraph = []

    def close_list():

        nonlocal in_list

        if in_list:

            output.append("</ul>")

            in_list = False

    for line in lines:

        stripped = line.strip()

        if not stripped:

            flush_paragraph()

            continue

        if stripped.startswith("### "):

            flush_paragraph()
            close_list()

            heading = stripped[4:].strip()

            output.append(
                "<h3>"
                + html.escape(heading)
                + "</h3>"
            )

            continue

        if stripped.startswith("## "):

            flush_paragraph()
            close_list()

            heading = stripped[3:].strip()

            output.append(
                "<h2>"
                + html.escape(heading)
                + "</h2>"
            )

            continue

        if stripped.startswith("# "):

            flush_paragraph()
            close_list()

            continue

        if re.match(
            r"^[-*]\s+",
            stripped,
        ):

            flush_paragraph()

            if not in_list:

                output.append("<ul>")

                in_list = True

            item = re.sub(
                r"^[-*]\s+",
                "",
                stripped,
            )

            output.append(
                "<li>"
                + html.escape(item)
                + "</li>"
            )

            continue

        close_list()

        paragraph.append(
            stripped
        )

    flush_paragraph()
    close_list()

    return "\n".join(output)


# =========================================================
# ARTICLE PAGE
# =========================================================

def article_html(title, body_html):

    safe_title = html.escape(title)

    return f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">
{PINTEREST_VERIFY}

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{safe_title} | {SITE_NAME}</title>

<meta name="description"
content="{safe_title} — practical guidance for strength, mobility and healthy aging.">

<style>

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    background: #f4f3ed;
    color: #13211d;
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    line-height: 1.75;
}}

nav {{
    padding: 24px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0b1715;
    color: white;
}}

.logo {{
    font-size: 21px;
    font-weight: 800;
    letter-spacing: -1px;
}}

.logo span {{
    color: #b7f36b;
}}

.nav-link {{
    color: white;
    text-decoration: none;
    font-size: 13px;
}}

.hero {{
    position: relative;
    min-height: 550px;
    display: flex;
    align-items: end;
    overflow: hidden;
    color: white;
    background: #10201b;
}}

.hero-bg {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}}

.hero-overlay {{
    position: absolute;
    inset: 0;
    background:
        linear-gradient(
            90deg,
            rgba(5,18,14,.88),
            rgba(5,18,14,.2)
        ),
        linear-gradient(
            0deg,
            rgba(5,18,14,.65),
            transparent
        );
}}

.hero-content {{
    position: relative;
    z-index: 2;
    max-width: 1100px;
    width: 100%;
    margin: auto;
    padding: 90px 7%;
}}

.eyebrow {{
    color: #b7f36b;
    text-transform: uppercase;
    letter-spacing: 3px;
    font-size: 11px;
    font-weight: 800;
}}

h1 {{
    max-width: 900px;
    font-size: clamp(45px, 7vw, 85px);
    line-height: .95;
    letter-spacing: -4px;
    margin: 18px 0;
}}

.article {{
    max-width: 820px;
    margin: auto;
    padding: 80px 7% 100px;
}}

.article p {{
    font-size: 18px;
}}

.article h2 {{
    margin-top: 60px;
    font-size: 34px;
    line-height: 1.1;
    letter-spacing: -1px;
}}

.article h3 {{
    margin-top: 35px;
    font-size: 23px;
}}

.article li {{
    margin: 10px 0;
}}

.cta {{
    margin-top: 75px;
    padding: 45px;
    border-radius: 28px;
    background: #0b1715;
    color: white;
}}

.cta h2 {{
    margin-top: 0;
    font-size: 35px;
}}

.cta p {{
    color: rgba(255,255,255,.72);
}}

.button {{
    display: inline-block;
    margin-top: 15px;
    padding: 15px 23px;
    border-radius: 999px;
    background: #b7f36b;
    color: #10201b;
    text-decoration: none;
    font-weight: 800;
}}

.disclosure {{
    margin-top: 20px;
    font-size: 11px;
    opacity: .5;
}}

footer {{
    padding: 45px 7%;
    text-align: center;
    background: #07110f;
    color: white;
    font-size: 12px;
}}

</style>

</head>

<body>

<nav>

    <div class="logo">
        Stronger<span>Years</span>
    </div>

    <a
        class="nav-link"
        href="../index.html"
    >
        Home
    </a>

</nav>

<header class="hero">

    <img
        class="hero-bg"
        src="{HERO_IMAGE}"
        alt="Active older adult outdoors"
    >

    <div class="hero-overlay"></div>

    <div class="hero-content">

        <div class="eyebrow">
            Strength · Vitality · Healthy aging
        </div>

        <h1>
            {safe_title}
        </h1>

    </div>

</header>

<main class="article">

{body_html}

<section class="cta">

    <h2>
        Want to explore the nutrition side?
    </h2>

    <p>
        Amino acids are one part of the broader nutrition
        conversation around maintaining muscle and supporting
        an active lifestyle.
    </p>

    <a
        class="button"
        href="{AFFILIATE_LINK}"
        target="_blank"
        rel="nofollow sponsored"
    >
        Explore the Formula →
    </a>

    <div class="disclosure">
        {DISCLOSURE}
    </div>

</section>

</main>

<footer>
    © {datetime.now().year} {SITE_NAME}
</footer>

</body>

</html>
"""


# =========================================================
# PREMIUM HOMEPAGE
# =========================================================

def build_homepage():

    articles = []

    if os.path.exists(CONTENT_DIR):

        for filename in os.listdir(CONTENT_DIR):

            if not filename.endswith(".html"):
                continue

            path = os.path.join(
                CONTENT_DIR,
                filename,
            )

            try:

                with open(
                    path,
                    "r",
                    encoding="utf-8",
                ) as f:

                    content = f.read()

                match = re.search(
                    r"<title>(.*?)</title>",
                    content,
                    flags=re.I | re.S,
                )

                if match:

                    title = re.sub(
                        r"\s+",
                        " ",
                        match.group(1),
                    ).strip()

                    articles.append(
                        (title, filename)
                    )

            except Exception:
                pass

    articles = sorted(
        articles,
        key=lambda x: x[1],
        reverse=True,
    )[:8]

    cards = []

    for i, (title, filename) in enumerate(
        articles
    ):

        image = CARD_IMAGES[
            i % len(CARD_IMAGES)
        ]

        cards.append(
            f"""
            <a
                class="guide-card reveal"
                href="content/{html.escape(filename)}"
            >

                <div class="card-image">

                    <img
                        src="{image}"
                        alt="{html.escape(title)}"
                        loading="lazy"
                    >

                    <div class="card-gradient"></div>

                    <span class="card-tag">
                        GUIDE
                    </span>

                </div>

                <div class="card-content">

                    <h3>
                        {html.escape(title)}
                    </h3>

                    <span class="read-link">
                        Read guide <b>→</b>
                    </span>

                </div>

            </a>
            """
        )

    cards_html = "\n".join(cards)

    return f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">
{PINTEREST_VERIFY}

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
{SITE_NAME} — Age well. Live strong.
</title>

<meta
name="description"
content="Practical guides for strength, mobility, recovery, nutrition and healthy aging."
>

<style>

:root {{
    --ink: #10201b;
    --muted: #66716c;
    --cream: #f4f3ed;
    --white: #ffffff;
    --green: #b7f36b;
    --dark: #0b1715;
}}

* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    background: var(--cream);
    color: var(--ink);
    font-family:
        Arial,
        Helvetica,
        sans-serif;
    overflow-x: hidden;
}}

a {{
    color: inherit;
}}

.nav {{
    position: absolute;
    z-index: 20;
    top: 0;
    left: 0;
    width: 100%;
    padding: 25px 6%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: white;
}}

.logo {{
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -1px;
}}

.logo span {{
    color: var(--green);
}}

.nav-links {{
    display: flex;
    gap: 32px;
}}

.nav-links a {{
    color: white;
    text-decoration: none;
    font-size: 13px;
    opacity: .88;
    transition: opacity .2s ease;
}}

.nav-links a:hover {{
    opacity: 1;
}}

.hero {{
    min-height: 94vh;
    position: relative;
    display: flex;
    align-items: center;
    overflow: hidden;
    color: white;
    background: #18251f;
}}

.hero-image {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center;
    transform: scale(1.05);
    animation: heroZoom 12s ease-out forwards;
}}

.hero-overlay {{
    position: absolute;
    inset: 0;
    background:
        linear-gradient(
            90deg,
            rgba(5,18,14,.9) 0%,
            rgba(5,18,14,.63) 42%,
            rgba(5,18,14,.1) 78%
        ),
        linear-gradient(
            0deg,
            rgba(5,18,14,.55),
            transparent 55%
        );
}}

.hero-content {{
    position: relative;
    z-index: 2;
    width: 100%;
    max-width: 1250px;
    margin: auto;
    padding: 150px 6% 90px;
}}

.eyebrow {{
    text-transform: uppercase;
    letter-spacing: 4px;
    font-size: 11px;
    font-weight: 800;
    color: var(--green);
}}

.hero h1 {{
    max-width: 900px;
    margin: 22px 0;
    font-size: clamp(65px, 9vw, 140px);
    line-height: .86;
    letter-spacing: -9px;
    font-weight: 800;
}}

.hero h1 span {{
    color: var(--green);
}}

.hero-copy {{
    max-width: 590px;
    font-size: 19px;
    line-height: 1.6;
    color: rgba(255,255,255,.82);
}}

.hero-button {{
    display: inline-flex;
    align-items: center;
    gap: 14px;
    margin-top: 32px;
    padding: 16px 25px;
    background: var(--green);
    color: #13200f;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 800;
    transition:
        transform .25s ease,
        box-shadow .25s ease;
}}

.hero-button:hover {{
    transform: translateY(-4px);
    box-shadow: 0 15px 35px rgba(183,243,107,.2);
}}

.hero-button b {{
    font-size: 20px;
}}

.scroll {{
    margin-top: 65px;
    font-size: 10px;
    letter-spacing: 3px;
    text-transform: uppercase;
    opacity: .6;
    animation: float 2s ease-in-out infinite;
}}

.section {{
    padding: 120px 6%;
}}

.section-inner {{
    max-width: 1250px;
    margin: auto;
}}

.split {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 90px;
    align-items: center;
}}

.big-heading {{
    font-size: clamp(45px, 6vw, 78px);
    line-height: .98;
    letter-spacing: -4px;
    margin: 20px 0 28px;
}}

.body-copy {{
    max-width: 600px;
    font-size: 18px;
    line-height: 1.75;
    color: var(--muted);
}}

.story-image {{
    width: 100%;
    height: 620px;
    object-fit: cover;
    border-radius: 30px;
    box-shadow: 0 25px 70px rgba(0,0,0,.15);
    transition: transform .6s ease;
}}

.story-image:hover {{
    transform: scale(1.015);
}}

.stat-row {{
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 14px;
    margin-top: 45px;
}}

.stat {{
    padding: 20px;
    border-radius: 18px;
    background: rgba(255,255,255,.7);
    border: 1px solid rgba(0,0,0,.07);
    transition:
        transform .25s ease,
        box-shadow .25s ease;
}}

.stat:hover {{
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0,0,0,.08);
}}

.stat-icon {{
    font-size: 25px;
}}

.stat strong {{
    display: block;
    margin-top: 10px;
    font-size: 13px;
}}

.guides {{
    background: var(--dark);
    color: white;
}}

.guides-heading {{
    display: flex;
    justify-content: space-between;
    align-items: end;
    gap: 30px;
}}

.guides-heading .big-heading {{
    margin-bottom: 0;
}}

.guide-intro {{
    max-width: 530px;
    color: rgba(255,255,255,.62);
    line-height: 1.7;
}}

.guide-grid {{
    margin-top: 60px;
    display: grid;
    grid-template-columns: repeat(4,1fr);
    gap: 18px;
}}

.guide-card {{
    text-decoration: none;
    border-radius: 25px;
    overflow: hidden;
    background: #17231f;
    border: 1px solid rgba(255,255,255,.12);
    transition:
        transform .35s ease,
        border-color .35s ease,
        box-shadow .35s ease;
}}

.guide-card:hover {{
    transform: translateY(-9px);
    border-color: rgba(183,243,107,.55);
    box-shadow: 0 25px 55px rgba(0,0,0,.25);
}}

.card-image {{
    height: 235px;
    position: relative;
    overflow: hidden;
}}

.card-image img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform .6s ease;
}}

.guide-card:hover .card-image img {{
    transform: scale(1.08);
}}

.card-gradient {{
    position: absolute;
    inset: 0;
    background:
        linear-gradient(
            0deg,
            rgba(0,0,0,.55),
            transparent 60%
        );
}}

.card-tag {{
    position: absolute;
    left: 18px;
    bottom: 17px;
    padding: 7px 10px;
    border-radius: 999px;
    background: var(--green);
    color: #14200f;
    font-size: 9px;
    font-weight: 900;
    letter-spacing: 1.5px;
}}

.card-content {{
    padding: 25px;
}}

.card-content h3 {{
    margin: 0 0 25px;
    font-size: 22px;
    line-height: 1.16;
    letter-spacing: -.7px;
}}

.read-link {{
    color: rgba(255,255,255,.62);
    font-size: 13px;
}}

.read-link b {{
    color: var(--green);
    margin-left: 7px;
}}

.cta-section {{
    position: relative;
    min-height: 620px;
    overflow: hidden;
    display: flex;
    align-items: center;
}}

.cta-image {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
}}

.cta-overlay {{
    position: absolute;
    inset: 0;
    background:
        linear-gradient(
            90deg,
            rgba(244,243,237,.98) 0%,
            rgba(244,243,237,.82) 43%,
            rgba(244,243,237,.08) 100%
        );
}}

.cta-content {{
    position: relative;
    z-index: 2;
    max-width: 1250px;
    width: 100%;
    margin: auto;
    padding: 90px 6%;
}}

.cta-content h2 {{
    max-width: 620px;
    font-size: clamp(48px, 6vw, 82px);
    line-height: .95;
    letter-spacing: -4px;
    margin: 18px 0;
}}

.cta-content p {{
    max-width: 520px;
    color: var(--muted);
    line-height: 1.7;
    font-size: 18px;
}}

.outline-button {{
    display: inline-block;
    margin-top: 20px;
    padding: 15px 22px;
    border: 1px solid #17211e;
    border-radius: 999px;
    text-decoration: none;
    font-weight: 700;
    transition:
        background .25s ease,
        color .25s ease,
        transform .25s ease;
}}

.outline-button:hover {{
    background: #10201b;
    color: white;
    transform: translateY(-3px);
}}

.disclosure {{
    max-width: 700px;
    margin-top: 40px;
    color: var(--muted);
    font-size: 11px;
}}

footer {{
    background: #07110f;
    color: white;
    padding: 55px 6%;
}}

.footer-inner {{
    max-width: 1250px;
    margin: auto;
    display: flex;
    justify-content: space-between;
    gap: 30px;
}}

.footer-note {{
    max-width: 430px;
    color: rgba(255,255,255,.45);
    font-size: 12px;
    line-height: 1.6;
}}

.reveal {{
    opacity: 0;
    transform: translateY(25px);
    animation: reveal .8s ease forwards;
}}

.guide-card:nth-child(2) {{
    animation-delay: .08s;
}}

.guide-card:nth-child(3) {{
    animation-delay: .16s;
}}

.guide-card:nth-child(4) {{
    animation-delay: .24s;
}}

@keyframes reveal {{

    to {{
        opacity: 1;
        transform: translateY(0);
    }}

}}

@keyframes heroZoom {{

    from {{
        transform: scale(1.05);
    }}

    to {{
        transform: scale(1);
    }}

}}

@keyframes float {{

    0%,100% {{
        transform: translateY(0);
    }}

    50% {{
        transform: translateY(7px);
    }}

}}

@media (max-width: 950px) {{

    .nav-links {{
        display: none;
    }}

    .split {{
        grid-template-columns: 1fr;
        gap: 50px;
    }}

    .story-image {{
        height: 450px;
    }}

    .guide-grid {{
        grid-template-columns: repeat(2,1fr);
    }}

    .stat-row {{
        grid-template-columns: repeat(2,1fr);
    }}

}}

@media (max-width: 600px) {{

    .hero {{
        min-height: 88vh;
    }}

    .hero h1 {{
        letter-spacing: -4px;
    }}

    .hero-copy {{
        font-size: 17px;
    }}

    .section {{
        padding: 80px 6%;
    }}

    .guide-grid {{
        grid-template-columns: 1fr;
    }}

    .stat-row {{
        grid-template-columns: 1fr 1fr;
    }}

    .cta-section {{
        min-height: 560px;
    }}

    .footer-inner {{
        flex-direction: column;
    }}

}}

</style>

</head>

<body>

<nav class="nav">

    <div class="logo">
        Stronger<span>Years</span>
    </div>

    <div class="nav-links">

        <a href="#guides">
            Guides
        </a>

        <a href="#approach">
            Approach
        </a>

        <a href="#start">
            Start
        </a>

    </div>

</nav>

<header class="hero">

    <img
        class="hero-image"
        src="{HERO_IMAGE}"
        alt="Active older adult exercising outdoors"
    >

    <div class="hero-overlay"></div>

    <div class="hero-content">

        <div class="eyebrow">
            Healthy aging · Strength · Vitality
        </div>

        <h1>
            Age well.<br>
            <span>Live strong.</span>
        </h1>

        <p class="hero-copy">
            Practical guides, simple habits and thoughtful ideas
            for maintaining strength, mobility and everyday vitality
            as you get older.
        </p>

        <a
            class="hero-button"
            href="#guides"
        >
            Explore the guides
            <b>→</b>
        </a>

        <div class="scroll">
            Scroll to explore ↓
        </div>

    </div>

</header>

<section
    class="section"
    id="approach"
>

    <div class="section-inner split">

        <div>

            <div class="eyebrow">
                The bigger picture
            </div>

            <h2 class="big-heading">
                Your best years aren't behind you.
            </h2>

            <p class="body-copy">
                Healthy aging is about staying engaged with the
                things you enjoy. Movement, nutrition, recovery
                and consistent habits can all play a role in
                supporting an active lifestyle.
            </p>

            <div class="stat-row">

                <div class="stat">
                    <div class="stat-icon">
                        🏋️
                    </div>
                    <strong>
                        Strength
                    </strong>
                </div>

                <div class="stat">
                    <div class="stat-icon">
                        🧘
                    </div>
                    <strong>
                        Mobility
                    </strong>
                </div>

                <div class="stat">
                    <div class="stat-icon">
                        🥗
                    </div>
                    <strong>
                        Nutrition
                    </strong>
                </div>

                <div class="stat">
                    <div class="stat-icon">
                        ⚡
                    </div>
                    <strong>
                        Vitality
                    </strong>
                </div>

            </div>

        </div>

        <img
            class="story-image"
            src="{STORY_IMAGE}"
            alt="Active older adult exercising"
            loading="lazy"
        >

    </div>

</section>

<section
    class="section guides"
    id="guides"
>

    <div class="section-inner">

        <div class="guides-heading">

            <div>

                <div class="eyebrow">
                    Latest guides
                </div>

                <h2 class="big-heading">
                    Ideas worth reading.
                </h2>

            </div>

            <p class="guide-intro">
                Practical articles about strength, nutrition,
                recovery, mobility and healthy aging.
            </p>

        </div>

        <div class="guide-grid">

            {cards_html}

        </div>

    </div>

</section>

<section
    class="cta-section"
    id="start"
>

    <img
        class="cta-image"
        src="{MOUNTAIN_IMAGE}"
        alt="Older adult hiking outdoors"
        loading="lazy"
    >

    <div class="cta-overlay"></div>

    <div class="cta-content">

        <div class="eyebrow">
            Start simple
        </div>

        <h2>
            Better habits.<br>
            Stronger days.
        </h2>

        <p>
            Explore practical approaches to movement, nutrition,
            recovery and healthy aging — one useful idea at a time.
        </p>

        <a
            class="outline-button"
            href="#guides"
        >
            Browse all guides →
        </a>

        <div class="disclosure">
            {DISCLOSURE}
        </div>

    </div>

</section>

<footer>

    <div class="footer-inner">

        <div>

            <div class="logo">
                Stronger<span>Years</span>
            </div>

        </div>

        <div class="footer-note">

            Independent educational content about healthy aging,
            strength, mobility and everyday wellness.

            <br><br>

            {DISCLOSURE}

        </div>

    </div>

</footer>

</body>

</html>
"""


# =========================================================
# MAIN AGENT
# =========================================================

def main():

    os.makedirs(
        CONTENT_DIR,
        exist_ok=True
    )

    existing_titles = get_existing_titles()

    print(
        "Existing articles:",
        len(existing_titles)
    )

    topic_index = (
        len(existing_titles)
        % len(TOPICS)
    )

    title = None
    body = None

    for offset in range(len(TOPICS)):

        selected_topic = TOPICS[
            (topic_index + offset)
            % len(TOPICS)
        ]

        print(
            "Trying topic:",
            selected_topic
        )

        try:

            new_title, new_body = generate_article(
                selected_topic,
                existing_titles,
            )

        except Exception as e:

            print(
                "Generation failed:",
                e
            )

            continue

        if new_title and new_body:

            title = new_title
            body = new_body

            break

    if title:

        print(
            "Generated article:",
            title
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d-%H%M%S"
        )

        slug = slugify(title)

        filename = (
            f"{slug}-{timestamp}.html"
        )

        path = os.path.join(
            CONTENT_DIR,
            filename,
        )

        body_html = markdown_to_html(
            body
        )

        page = article_html(
            title,
            body_html,
        )

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as f:

            f.write(page)

        print(
            "Saved article:",
            path
        )

    else:

        print(
            "No new article generated."
        )

    # Always rebuild homepage
    homepage = build_homepage()

    with open(
        "index.html",
        "w",
        encoding="utf-8",
    ) as f:

        f.write(homepage)

    print(
        "Homepage updated."
    )

    print(
        "Agent finished successfully."
    )


if __name__ == "__main__":
    main()
