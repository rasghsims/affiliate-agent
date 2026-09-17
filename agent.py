import os
import re
import time
import html
from pathlib import Path
from datetime import datetime
import requests


# =========================================================
# SETTINGS
# =========================================================

API_KEY = os.environ["OPENROUTER_API_KEY"]

AFFILIATE_LINK = (
    "https://www.advancedbionutritionals.com/DS24/Advanced-Amino/"
    "Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld"
)

SITE_NAME = "StrongerYears"
SITE_URL = "https://rasghsims.github.io/affiliate-agent"

DISCLOSURE = (
    "I may earn a commission if you buy through links on this page, "
    "at no extra cost to you."
)

CONTENT_DIR = "content"
ASSET_DIR = Path(CONTENT_DIR) / "assets"

MODEL = "openrouter/free"


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
        "HTTP-Referer": SITE_URL + "/",
        "X-Title": SITE_NAME,
    }

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert wellness content writer. "
                    "Create useful, original, readable educational content "
                    "for adults interested in healthy aging, strength, "
                    "mobility, nutrition, recovery and vitality. "
                    "Never invent studies, statistics, doctors, testimonials, "
                    "reviews or guarantees. "
                    "Do not make disease treatment or cure claims. "
                    "Do not use fear-based marketing, fake urgency, "
                    "miracle language or guaranteed-result language."
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

    content_path = Path(CONTENT_DIR)

    if not content_path.exists():
        return titles

    for path in content_path.glob("*.html"):

        try:

            content = path.read_text(
                encoding="utf-8"
            )

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

                title = re.sub(
                    r"\s+\|\s+StrongerYears$",
                    "",
                    title,
                    flags=re.I,
                )

                titles.append(title.lower())

        except Exception:
            pass

    return titles


# =========================================================
# ARTICLE GENERATION
# =========================================================

def generate_article(topic, existing_titles):

    prompt = f"""
Create a high-quality original article about:

"{topic}"

Audience:
Adults 50+ in the United States interested in strength,
mobility, recovery, nutrition and healthy aging.

Requirements:

- 1200–1600 words.
- Create a strong natural title.
- Start with an engaging introduction.
- Use H2 and H3 sections.
- Use short readable paragraphs.
- Give practical advice.
- Include a simple checklist.
- Explain why maintaining muscle and an active lifestyle matters.
- Explain how nutrition can support an active lifestyle.
- Explain the role amino acids can play in nutrition without exaggeration.
- Mention that supplements are optional and are not a replacement
  for a balanced diet.
- Do not claim supplements treat, cure, prevent or reverse disease.
- Do not invent studies, statistics or medical authorities.
- Do not create testimonials or reviews.
- Do not promise specific results.
- Do not use fake scarcity or urgency.
- Do not use miracle, guaranteed, secret cure or instant-result language.
- End with a natural optional recommendation for readers who want
  to explore amino-acid nutrition further.

Existing article titles:

{existing_titles[:40]}

Create a substantially different title.

Return only the article in Markdown.
Do not mention these instructions.
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

        cleaned = re.sub(
            r"\*+",
            "",
            cleaned,
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

        first = re.sub(
            r"\*+",
            "",
            first,
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

    def inline_format(value):

        value = html.escape(value)

        value = re.sub(
            r"\*\*(.+?)\*\*",
            r"<strong>\1</strong>",
            value,
        )

        value = re.sub(
            r"(?<!\*)\*([^*\n]+?)\*(?!\*)",
            r"<em>\1</em>",
            value,
        )

        # Final safety cleanup.
        value = value.replace("**", "")

        return value

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
                    + inline_format(joined)
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
                + inline_format(heading)
                + "</h3>"
            )

            continue

        if stripped.startswith("## "):

            flush_paragraph()
            close_list()

            heading = stripped[3:].strip()

            output.append(
                "<h2>"
                + inline_format(heading)
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
                + inline_format(item)
                + "</li>"
            )

            continue

        close_list()

        paragraph.append(stripped)

    flush_paragraph()

    close_list()

    return "\n".join(output)


# =========================================================
# LOCAL TOPIC VISUAL
# =========================================================

def topic_visual(title, slug):

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = ASSET_DIR / f"{slug}.svg"

    lower = title.lower()

    if any(
        word in lower
        for word in [
            "recovery",
            "recover",
            "morning",
            "routine",
        ]
    ):

        accent = "#b7f36b"
        secondary = "#8ebc9c"
        label = "RECOVER • REBUILD"

    elif any(
        word in lower
        for word in [
            "nutrition",
            "protein",
            "amino",
            "food",
            "diet",
        ]
    ):

        accent = "#d9efb7"
        secondary = "#6f9d7d"
        label = "NOURISH • SUPPORT"

    elif any(
        word in lower
        for word in [
            "mobility",
            "active",
            "exercise",
            "movement",
            "resistance",
        ]
    ):

        accent = "#c7f59b"
        secondary = "#527b67"
        label = "MOVE • STAY ACTIVE"

    else:

        accent = "#b7f36b"
        secondary = "#72957f"
        label = "STRENGTH • VITALITY"

    safe_label = html.escape(
        label
    )

    safe_title = html.escape(
        title[:42]
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
viewBox="0 0 1200 720"
role="img"
aria-label="{safe_title}">
<defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#081512"/>
        <stop offset="55%" stop-color="#19382c"/>
        <stop offset="100%" stop-color="#304f40"/>
    </linearGradient>

    <radialGradient id="glow">
        <stop offset="0%" stop-color="{accent}" stop-opacity=".42"/>
        <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
</defs>

<rect width="1200" height="720" fill="url(#bg)"/>

<circle
    cx="930"
    cy="180"
    r="270"
    fill="url(#glow)"
/>

<circle
    cx="1010"
    cy="580"
    r="210"
    fill="{secondary}"
    opacity=".14"
/>

<path
    d="M0 590 C220 470 370 680 590 530
       C760 415 870 485 1200 330
       L1200 720 L0 720 Z"
    fill="#07110e"
    opacity=".48"
/>

<circle
    cx="860"
    cy="285"
    r="82"
    fill="{accent}"
    opacity=".92"
/>

<path
    d="M760 425
       C790 345 935 345 965 425
       L1010 575
       L715 575 Z"
    fill="{accent}"
    opacity=".88"
/>

<rect
    x="640"
    y="555"
    width="420"
    height="18"
    rx="9"
    fill="{accent}"
    opacity=".75"
/>

<rect
    x="590"
    y="525"
    width="55"
    height="78"
    rx="12"
    fill="{secondary}"
/>

<rect
    x="1055"
    y="525"
    width="55"
    height="78"
    rx="12"
    fill="{secondary}"
/>

<text
    x="70"
    y="100"
    fill="{accent}"
    font-family="Arial, Helvetica, sans-serif"
    font-size="22"
    font-weight="800"
    letter-spacing="6">
    {safe_label}
</text>

<text
    x="70"
    y="635"
    fill="white"
    font-family="Arial, Helvetica, sans-serif"
    font-size="30"
    font-weight="700">
    STRONGER YEARS
</text>
</svg>
"""

    path.write_text(
        svg,
        encoding="utf-8",
    )

    return path.as_posix()


# =========================================================
# ARTICLE PAGE
# =========================================================

def article_html(
    title,
    body_html,
    visual_path,
):

    safe_title = html.escape(
        title
    )

    safe_visual = html.escape(
        "../" + visual_path
    )

    description = html.escape(
        f"{title} — practical guidance for strength, mobility, nutrition, recovery and healthy aging."
    )

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>{safe_title} | {SITE_NAME}</title>

<meta
name="description"
content="{description}"
>

<meta
name="robots"
content="index,follow"
>

<link
rel="canonical"
href="{SITE_URL}/content/{slugify(title)}"
>

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
    font-family: Arial, Helvetica, sans-serif;
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
    min-height: 570px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: end;
    color: white;
    background: #10201b;
}}

.hero img {{
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
            rgba(4,16,12,.93),
            rgba(4,16,12,.38),
            rgba(4,16,12,.12)
        ),
        linear-gradient(
            0deg,
            rgba(4,16,12,.75),
            transparent 60%
        );
}}

.hero-content {{
    position: relative;
    z-index: 2;
    width: 100%;
    max-width: 1200px;
    margin: auto;
    padding: 110px 7%;
}}

.eyebrow {{
    color: #b7f36b;
    text-transform: uppercase;
    letter-spacing: 3px;
    font-size: 11px;
    font-weight: 800;
}}

h1 {{
    max-width: 950px;
    font-size: clamp(46px, 7vw, 88px);
    line-height: .95;
    letter-spacing: -4px;
    margin: 18px 0;
}}

.article {{
    max-width: 820px;
    margin: auto;
    padding: 80px 7% 110px;
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

@media (max-width: 600px) {{

    h1 {{
        letter-spacing: -2px;
    }}

    .hero {{
        min-height: 520px;
    }}

    .article {{
        padding-top: 55px;
    }}

    .article p {{
        font-size: 17px;
    }}

    .cta {{
        padding: 30px;
    }}
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
href="../index.html">
    Home
</a>

</nav>

<header class="hero">

<img
src="{safe_visual}"
alt="{safe_title}"
loading="eager"
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
rel="nofollow sponsored">
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
# HOMEPAGE
# =========================================================

def build_homepage():

    articles = []

    content_path = Path(CONTENT_DIR)

    if content_path.exists():

        for path in content_path.glob("*.html"):

            try:

                content = path.read_text(
                    encoding="utf-8"
                )

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

                    title = re.sub(
                        r"\s+\|\s+StrongerYears$",
                        "",
                        title,
                        flags=re.I,
                    )

                    articles.append(
                        (
                            title,
                            path.name,
                        )
                    )

            except Exception:
                pass

    articles = sorted(
        articles,
        key=lambda x: x[1],
        reverse=True,
    )[:12]

    cards = []

    for index, (title, filename) in enumerate(
        articles
    ):

        safe_title = html.escape(
            title
        )

        visual_name = slugify(
            title
        ) + ".svg"

        visual = (
            "content/assets/"
            + visual_name
        )

        # If visual doesn't exist, create a basic local visual.
        visual_file = Path(
            CONTENT_DIR
        ) / "assets" / visual_name

        if not visual_file.exists():

            topic_visual(
                title,
                slugify(title),
            )

        cards.append(
            f"""
<a
class="guide-card"
href="content/{html.escape(filename)}">

<div class="card-image">

<img
src="{html.escape(visual)}"
alt="{safe_title}"
loading="lazy"
>

<div class="card-tag">
    GUIDE
</div>

</div>

<div class="card-content">

<h3>
    {safe_title}
</h3>

<span class="read-link">
    Read guide <b>→</b>
</span>

</div>

</a>
"""
        )

    cards_html = "\n".join(
        cards
    )

    return f"""<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">

<meta
name="viewport"
content="width=device-width, initial-scale=1.0"
>

<title>
{SITE_NAME} — Age well. Live strong.
</title>

<meta
name="description"
content="Practical guides for strength, mobility, recovery, nutrition and healthy aging."
>

<meta
name="robots"
content="index,follow"
>

<link
rel="canonical"
href="{SITE_URL}/"
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
    font-family: Arial, Helvetica, sans-serif;
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
}}

.hero {{
    min-height: 94vh;
    position: relative;
    display: flex;
    align-items: center;
    overflow: hidden;
    color: white;
    background:
        radial-gradient(
            circle at 78% 28%,
            rgba(183,243,107,.22),
            transparent 24%
        ),
        linear-gradient(
            135deg,
            #0b1715 0%,
            #17332a 48%,
            #10201b 100%
        );
}}

.hero-visual {{
    position: absolute;
    inset: 0;
    background:
        radial-gradient(
            circle at 78% 25%,
            rgba(183,243,107,.28),
            transparent 20%
        ),
        radial-gradient(
            circle at 65% 75%,
            rgba(117,160,133,.35),
            transparent 28%
        ),
        linear-gradient(
            135deg,
            #07110f,
            #17382c 55%,
            #10201b
        );
}}

.hero-visual::before {{
    content: "";
    position: absolute;
    width: 460px;
    height: 460px;
    right: 7%;
    top: 20%;
    border-radius: 50%;
    border: 1px solid rgba(183,243,107,.35);
    box-shadow:
        0 0 0 40px rgba(183,243,107,.025),
        0 0 0 100px rgba(183,243,107,.018);
}}

.hero-visual::after {{
    content: "";
    position: absolute;
    right: 13%;
    bottom: 15%;
    width: 300px;
    height: 300px;
    border-radius: 48% 52% 55% 45%;
    background:
        linear-gradient(
            145deg,
            rgba(183,243,107,.30),
            rgba(80,120,95,.08)
        );
    transform: rotate(-20deg);
}}

.hero-overlay {{
    position: absolute;
    inset: 0;
    background:
        linear-gradient(
            90deg,
            rgba(5,18,14,.92) 0%,
            rgba(5,18,14,.68) 43%,
            rgba(5,18,14,.12) 82%
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
    box-shadow:
        0 15px 35px rgba(183,243,107,.2);
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

.story-visual {{
    min-height: 470px;
    border-radius: 34px;
    overflow: hidden;
    position: relative;
    display: flex;
    align-items: end;
    padding: 42px;
    color: white;
    background:
        radial-gradient(
            circle at 72% 22%,
            rgba(183,243,107,.5),
            transparent 18%
        ),
        linear-gradient(
            145deg,
            #dfe8dd,
            #789984 50%,
            #19382d
        );
    box-shadow:
        0 30px 80px rgba(0,0,0,.15);
}}

.story-visual::before {{
    content: "";
    position: absolute;
    width: 250px;
    height: 250px;
    border-radius: 50%;
    right: 70px;
    top: 70px;
    border: 1px solid rgba(255,255,255,.6);
}}

.story-visual::after {{
    content: "";
    position: absolute;
    width: 130px;
    height: 260px;
    border-radius: 70px;
    right: 130px;
    top: 140px;
    background: rgba(183,243,107,.72);
    transform: rotate(18deg);
}}

.story-text {{
    position: relative;
    z-index: 2;
}}

.story-text span {{
    display: block;
    font-size: 11px;
    letter-spacing: 3px;
    font-weight: 800;
    margin-bottom: 12px;
}}

.story-text b {{
    display: block;
    max-width: 430px;
    font-size: clamp(32px, 4vw, 54px);
    line-height: 1;
    letter-spacing: -2px;
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
    box-shadow:
        0 15px 30px rgba(0,0,0,.08);
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
    box-shadow:
        0 25px 55px rgba(0,0,0,.25);
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
    transform: scale(1.05);
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
    min-height: 600px;
    overflow: hidden;
    display: flex;
    align-items: center;
    background:
        radial-gradient(
            circle at 80% 35%,
            rgba(183,243,107,.3),
            transparent 24%
        ),
        linear-gradient(
            135deg,
            #dfe8dd,
            #9eb6a3
        );
}}

.cta-visual {{
    position: absolute;
    right: 5%;
    width: 470px;
    height: 470px;
    border-radius: 50%;
    border: 1px solid rgba(16,32,27,.25);
}}

.cta-visual::before {{
    content: "";
    position: absolute;
    width: 300px;
    height: 300px;
    left: 85px;
    top: 85px;
    border-radius: 48%;
    background: rgba(16,32,27,.10);
    transform: rotate(25deg);
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

@media (max-width: 950px) {{

    .nav-links {{
        display: none;
    }}

    .split {{
        grid-template-columns: 1fr;
        gap: 50px;
    }}

    .guide-grid {{
        grid-template-columns: repeat(2,1fr);
    }}

    .stat-row {{
        grid-template-columns: repeat(2,1fr);
    }}

    .cta-visual {{
        opacity: .4;
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

    .story-visual {{
        min-height: 360px;
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

<div class="hero-visual"
aria-hidden="true"></div>

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
href="#guides">

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
id="approach">

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
    <div class="stat-icon">🏋️</div>
    <strong>Strength</strong>
</div>

<div class="stat">
    <div class="stat-icon">🧘</div>
    <strong>Mobility</strong>
</div>

<div class="stat">
    <div class="stat-icon">🥗</div>
    <strong>Nutrition</strong>
</div>

<div class="stat">
    <div class="stat-icon">⚡</div>
    <strong>Vitality</strong>
</div>

</div>

</div>

<div
class="story-visual"
aria-hidden="true">

<div class="story-text">

<span>
    STRONGER YEARS
</span>

<b>
    Move.<br>
    Nourish.<br>
    Recover.
</b>

</div>

</div>

</div>

</section>


<section
class="section guides"
id="guides">

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
id="start">

<div
class="cta-visual"
aria-hidden="true">
</div>

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
href="#guides">
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
# SITEMAP
# =========================================================

def build_sitemap():

    urls = [
        SITE_URL + "/"
    ]

    content_path = Path(
        CONTENT_DIR
    )

    if content_path.exists():

        for path in content_path.glob("*.html"):

            urls.append(
                SITE_URL
                + "/content/"
                + path.name
            )

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    entries = []

    for url in urls:

        entries.append(
            f"""
<url>
    <loc>{html.escape(url)}</loc>
    <lastmod>{today}</lastmod>
</url>
"""
        )

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>

<urlset
xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

{"".join(entries)}

</urlset>
"""

    Path(
        "sitemap.xml"
    ).write_text(
        sitemap,
        encoding="utf-8",
    )

    print(
        "Sitemap updated:",
        len(urls),
        "URLs"
    )


# =========================================================
# MAIN AGENT
# =========================================================

def main():

    Path(
        CONTENT_DIR
    ).mkdir(
        parents=True,
        exist_ok=True,
    )

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
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

    # -----------------------------------------------------
    # Try topics until a genuinely new article is generated.
    # -----------------------------------------------------

    for offset in range(
        len(TOPICS)
    ):

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

    # -----------------------------------------------------
    # Save new article.
    # -----------------------------------------------------

    if title:

        print(
            "Generated article:",
            title
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d-%H%M%S"
        )

        slug = slugify(
            title
        )

        filename = (
            f"{slug}-{timestamp}.html"
        )

        path = (
            Path(CONTENT_DIR)
            / filename
        )

        body_html = markdown_to_html(
            body
        )

        visual_path = topic_visual(
            title,
            slug,
        )

        page = article_html(
            title,
            body_html,
            visual_path,
        )

        path.write_text(
            page,
            encoding="utf-8",
        )

        print(
            "Saved article:",
            path
        )

        print(
            "Saved visual:",
            visual_path
        )

    else:

        print(
            "No new article generated."
        )

    # -----------------------------------------------------
    # Always rebuild homepage.
    # -----------------------------------------------------

    homepage = build_homepage()

    Path(
        "index.html"
    ).write_text(
        homepage,
        encoding="utf-8",
    )

    print(
        "Homepage updated."
    )

    # -----------------------------------------------------
    # Always rebuild sitemap.
    # -----------------------------------------------------

    build_sitemap()

    print(
        "Agent finished successfully."
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    main()
