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

DISCLOSURE = (
    "I may earn a commission if you buy through links on this page, "
    "at no extra cost to you."
)

CONTENT_DIR = "content"

MODEL = "openrouter/free"

# =========================================================
# VISUALS
# Local category images. The agent downloads them once into the repo,
# then the website references the local files (not remote image URLs).
# =========================================================

IMAGE_SOURCES = {
    "nutrition": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1600&q=82",
    "recovery": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1600&q=82",
    "mobility": "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=1600&q=82",
    "habits": "https://images.unsplash.com/photo-1499209974431-9dddcece7f88?auto=format&fit=crop&w=1600&q=82",
    "strength": "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=1600&q=82",
}


def image_category(title):
    lower = title.lower()
    if any(k in lower for k in ["nutrition", "protein", "amino", "food", "meal"]):
        return "nutrition"
    if any(k in lower for k in ["recovery", "exercise", "resistance", "workout", "training"]):
        return "recovery"
    if any(k in lower for k in ["mobility", "active", "movement", "walk"]):
        return "mobility"
    if any(k in lower for k in ["morning", "routine", "habits", "daily"]):
        return "habits"
    return "strength"


def _fallback_svg(category, path):
    labels = {
        "nutrition": ("NUTRITION", "Nourish your strength"),
        "recovery": ("RECOVERY", "Recover. Rebuild. Repeat."),
        "mobility": ("MOBILITY", "Keep moving forward"),
        "habits": ("DAILY HABITS", "Small habits. Stronger days."),
        "strength": ("STRENGTH", "Build for the years ahead"),
    }
    label, headline = labels.get(category, labels["strength"])
    svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1600 900\">
<defs><linearGradient id=\"g\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\"><stop stop-color=\"#07110f\"/><stop offset=\".55\" stop-color=\"#214a3a\"/><stop offset=\"1\" stop-color=\"#b7f36b\"/></linearGradient></defs>
<rect width=\"1600\" height=\"900\" fill=\"url(#g)\"/><circle cx=\"1240\" cy=\"220\" r=\"300\" fill=\"#fff\" opacity=\".08\"/><path d=\"M0 760 C300 570 510 820 760 650 S1200 530 1600 690 V900 H0Z\" fill=\"#07110f\" opacity=\".45\"/>
<text x=\"100\" y=\"150\" fill=\"#b7f36b\" font-family=\"Arial\" font-size=\"28\" font-weight=\"700\" letter-spacing=\"7\">{label}</text>
<text x=\"100\" y=\"290\" fill=\"white\" font-family=\"Arial\" font-size=\"70\" font-weight=\"800\">{headline}</text>
<text x=\"100\" y=\"805\" fill=\"white\" opacity=\".7\" font-family=\"Arial\" font-size=\"20\" letter-spacing=\"4\">STRONGER YEARS · AGE WELL · LIVE STRONG</text></svg>"""
    Path(path).write_text(svg, encoding="utf-8")


def topic_visual(title, filename):
    category = image_category(title)
    asset_dir = Path(CONTENT_DIR) / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-z0-9-]+", "-", filename.lower()).strip("-")
    image_path = asset_dir / f"{safe}.jpg"

    if not image_path.exists():
        try:
            response = requests.get(IMAGE_SOURCES[category], timeout=30)
            response.raise_for_status()
            if len(response.content) < 10000:
                raise ValueError("image response was unexpectedly small")
            image_path.write_bytes(response.content)
            print("Downloaded related image:", category, image_path)
        except Exception as e:
            print("Image download failed; using local SVG fallback:", e)
            fallback = asset_dir / f"{safe}.svg"
            _fallback_svg(category, fallback)
            return "assets/" + fallback.name

    return "assets/" + image_path.name

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
        cleaned = re.sub(r"\*+", "", cleaned).strip()

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

    def inline_format(value):

        # Escape first, then safely restore only the Markdown emphasis
        # that the AI is allowed to generate. This prevents literal **
        # markers from appearing on the live site.
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

        paragraph.append(
            stripped
        )

    flush_paragraph()
    close_list()

    return "\n".join(output)


# =========================================================
# ARTICLE PAGE
# =========================================================

def article_html(title, body_html, visual_path):

    safe_title = html.escape(title)

    return f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

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
    background:
        radial-gradient(circle at 78% 28%, rgba(183,243,107,.22), transparent 22%),
        linear-gradient(135deg, #07110f 0%, #17382c 52%, #10201b 100%);
}}

.hero-bg {{
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    background:
        radial-gradient(circle at 72% 35%, rgba(183,243,107,.18), transparent 20%),
        linear-gradient(125deg, transparent 30%, rgba(255,255,255,.035) 30.2%, transparent 30.5%),
        linear-gradient(145deg, #07110f 0%, #17382c 55%, #10201b 100%);
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

    <div class="hero-bg" style="background-image:url('{visual_path}');" aria-hidden="true"></div>

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

        image = topic_visual(title, slugify(title))

        cards.append(
            f"""
            <a
                class="guide-card reveal"
                href="content/{html.escape(filename)}"
            >

                <div class="card-image">

                    <div class="card-art" style="background-image:url('content/{image}');" aria-hidden="true"></div>

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
    background:
        radial-gradient(circle at 78% 28%, rgba(183,243,107,.22), transparent 24%),
        radial-gradient(circle at 58% 72%, rgba(65,120,94,.30), transparent 32%),
        linear-gradient(135deg, #0b1715 0%, #17332a 48%, #10201b 100%);
}}

.hero-image {{
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 72% 35%, rgba(183,243,107,.20), transparent 22%),
        linear-gradient(125deg, transparent 25%, rgba(255,255,255,.035) 25.2%, transparent 25.5%),
        linear-gradient(145deg, #07110f 0%, #17382c 52%, #10201b 100%);
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
    height: 430px;
    border-radius: 30px;
    box-shadow: 0 25px 70px rgba(0,0,0,.15);
    background:
        radial-gradient(circle at 70% 25%, rgba(183,243,107,.55), transparent 18%),
        linear-gradient(145deg, #dfe8dd, #a9c1ad 48%, #29483c);
    display: flex;
    flex-direction: column;
    justify-content: flex-end;
    padding: 42px;
    color: #10201b;
}}

.story-image span {{
    font-size: 11px;
    letter-spacing: 3px;
    font-weight: 800;
    opacity: .65;
}}

.story-image b {{
    margin-top: 8px;
    font-size: clamp(28px, 4vw, 48px);
    letter-spacing: -2px;
    max-width: 420px;
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

.card-art {{
    width: 100%;
    height: 100%;
    background:
        radial-gradient(circle at 75% 25%, rgba(183,243,107,.32), transparent 20%),
        linear-gradient(145deg, #29483c, #10201b 65%);
    transition: transform .6s ease;
}}

.guide-card:nth-child(2) .card-art {{ background: linear-gradient(145deg, #30483d, #17231f); }}
.guide-card:nth-child(3) .card-art {{ background: linear-gradient(145deg, #566a54, #17231f); }}
.guide-card:nth-child(4) .card-art {{ background: linear-gradient(145deg, #3c5548, #0e1916); }}

.guide-card:hover .card-art {{
    transform: scale(1.03);
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
    background:
        radial-gradient(circle at 82% 38%, rgba(183,243,107,.28), transparent 22%),
        linear-gradient(125deg, #dfe8dd 0%, #b9cdbd 48%, #5d7565 100%);
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
    from {{ opacity: .92; }}
    to {{ opacity: 1; }}
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
        height: 330px;
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

    <div class="hero-image" aria-hidden="true"></div>

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

        <div class="story-image" aria-hidden="true">
            <span>STRONGER YEARS</span>
            <b>Move. Nourish. Recover.</b>
        </div>

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

    <div class="cta-image" aria-hidden="true"></div>

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

        visual_path = topic_visual(title, slug)

        page = article_html(
            title,
            body_html,
            visual_path,
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
