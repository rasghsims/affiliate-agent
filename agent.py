import os
import re
import time
import html
import requests
from datetime import datetime

# =========================
# BASIC SETTINGS
# =========================

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

# =========================
# BUYER-INTENT TOPICS
# =========================

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

# =========================
# OPENROUTER
# =========================

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
                    "You are a careful health and wellness content writer. "
                    "Write useful, practical, original educational content. "
                    "Do not make disease treatment or cure claims. "
                    "Do not invent studies, doctors, testimonials, reviews, "
                    "statistics, guarantees, or medical results. "
                    "Avoid hype and fear-based marketing. "
                    "Use natural language suitable for adults interested in "
                    "healthy aging, strength, mobility, recovery and vitality."
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
            print(f"AI request failed (attempt {attempt + 1}/4): {e}")

            if attempt < 3:
                time.sleep(5 * (attempt + 1))
            else:
                raise


# =========================
# HELPERS
# =========================

def clean_text(text):
    text = text.replace("\r", "")
    text = re.sub(r"```(?:html|markdown)?", "", text, flags=re.I)
    text = text.replace("```", "")
    return text.strip()


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:80]


def get_existing_titles():
    titles = []

    if not os.path.exists(CONTENT_DIR):
        return titles

    for filename in os.listdir(CONTENT_DIR):
        if not filename.endswith(".html"):
            continue

        path = os.path.join(CONTENT_DIR, filename)

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.search(
                r"<title>(.*?)</title>",
                content,
                flags=re.I | re.S,
            )

            if match:
                title = re.sub(r"\s+", " ", match.group(1)).strip()
                titles.append(title.lower())

        except Exception:
            pass

    return titles


# =========================
# ARTICLE GENERATION
# =========================

def generate_article(topic, existing_titles):
    prompt = f"""
Create a high-quality original article for this topic:

"{topic}"

Audience:
Adults 50+ who want to maintain strength, mobility, recovery and vitality.

Requirements:

- 1200–1600 words.
- Give the article a compelling but honest title.
- Include a short introduction.
- Use clear H2 sections.
- Include practical steps readers can actually use.
- Include a concise checklist.
- Include a section explaining how nutrition can support muscle and healthy aging.
- Mention amino acids as one possible part of a broader nutrition strategy.
- Do not present any supplement as a cure or treatment.
- Do not claim a product will prevent, reverse or treat disease.
- Do not invent scientific studies or statistics.
- Do not create fake testimonials or reviews.
- Do not use fake urgency.
- Do not use exaggerated claims such as "miracle", "guaranteed", "secret", or "instant results".
- Do not mention this instruction.
- End with a natural optional recommendation for readers who want to learn
  more about amino-acid nutrition.

Existing article titles are below.
Avoid creating a title that is substantially similar to them:

{existing_titles[:30]}
"""

    raw = clean_text(ask_ai(prompt))

    # Try to extract title
    title_match = re.search(
        r"^(?:#\s*)?(.+)$",
        raw,
        flags=re.MULTILINE,
    )

    if title_match:
        title = title_match.group(1).strip()
    else:
        title = topic

    # Remove accidental markdown heading from title
    title = re.sub(r"^#+\s*", "", title).strip()

    # Remove title from body if it appears as first line
    lines = raw.splitlines()

    if lines:
        first = re.sub(r"^#+\s*", "", lines[0]).strip()

        if first.lower() == title.lower():
            raw = "\n".join(lines[1:]).strip()

    # Basic duplicate protection
    if title.lower() in existing_titles:
        return None, None

    return title, raw


# =========================
# MARKDOWN → HTML
# =========================

def markdown_to_html(text):
    lines = text.splitlines()

    output = []
    paragraph = []

    def flush_paragraph():
        if paragraph:
            joined = " ".join(x.strip() for x in paragraph).strip()

            if joined:
                output.append(
                    f"<p>{html.escape(joined)}</p>"
                )

            paragraph.clear()

    for line in lines:
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            heading = stripped[4:].strip()
            output.append(
                f"<h3>{html.escape(heading)}</h3>"
            )
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            heading = stripped[3:].strip()
            output.append(
                f"<h2>{html.escape(heading)}</h2>"
            )
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            item = re.sub(r"^[-*]\s+", "", stripped)

            if (
                not output
                or not output[-1].startswith("<ul>")
            ):
                output.append("<ul>")

            output.append(
                f"<li>{html.escape(item)}</li>"
            )
            continue

        paragraph.append(stripped)

    flush_paragraph()

    # Close list blocks
    final = []
    in_list = False

    for item in output:
        if item == "<ul>":
            if in_list:
                final.append("</ul>")
            final.append(item)
            in_list = True
        elif item.startswith("<li>"):
            final.append(item)
        else:
            if in_list:
                final.append("</ul>")
                in_list = False

            final.append(item)

    if in_list:
        final.append("</ul>")

    return "\n".join(final)


# =========================
# PREMIUM ARTICLE PAGE
# =========================

def article_html(title, body_html):
    safe_title = html.escape(title)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{safe_title} | {SITE_NAME}</title>

<meta name="description"
content="{html.escape(title)} — practical guidance for strength, mobility and healthy aging.">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f7f7f3;
    color: #171717;
    font-family: Arial, Helvetica, sans-serif;
    line-height: 1.75;
}}

nav {{
    padding: 24px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #deded8;
    background: rgba(247,247,243,.96);
}}

.logo {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

.nav-link {{
    text-decoration: none;
    color: #171717;
    font-size: 14px;
}}

.hero {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 90px 7% 70px;
}}

.eyebrow {{
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 12px;
    font-weight: 700;
    opacity: .55;
}}

h1 {{
    max-width: 900px;
    font-size: clamp(42px, 7vw, 78px);
    line-height: 1.02;
    letter-spacing: -4px;
    margin: 20px 0;
}}

.article {{
    max-width: 820px;
    margin: 0 auto;
    padding: 20px 7% 90px;
}}

.article p {{
    font-size: 18px;
}}

.article h2 {{
    margin-top: 55px;
    font-size: 32px;
    line-height: 1.15;
    letter-spacing: -1px;
}}

.article h3 {{
    margin-top: 35px;
    font-size: 23px;
}}

.article ul {{
    padding-left: 24px;
}}

.article li {{
    margin: 10px 0;
}}

.cta {{
    margin-top: 70px;
    padding: 45px;
    border-radius: 28px;
    background: #171717;
    color: white;
}}

.cta h2 {{
    margin-top: 0;
    font-size: 34px;
}}

.cta p {{
    opacity: .82;
}}

.button {{
    display: inline-block;
    margin-top: 20px;
    padding: 15px 24px;
    border-radius: 999px;
    background: white;
    color: #171717;
    text-decoration: none;
    font-weight: 700;
}}

.disclosure {{
    margin-top: 22px;
    font-size: 12px;
    opacity: .55;
}}

footer {{
    padding: 45px 7%;
    border-top: 1px solid #deded8;
    text-align: center;
    font-size: 13px;
    opacity: .55;
}}

@media (max-width: 650px) {{

    .hero {{
        padding-top: 55px;
    }}

    h1 {{
        letter-spacing: -2px;
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
    <div class="logo">{SITE_NAME}</div>
    <a class="nav-link" href="../index.html">Home</a>
</nav>

<header class="hero">
    <div class="eyebrow">Healthy aging · Strength · Vitality</div>
    <h1>{safe_title}</h1>
</header>

<main class="article">

{body_html}

<section class="cta">

    <h2>Want to explore the nutrition side?</h2>

    <p>
        Amino acids are one part of the broader nutrition conversation
        around maintaining muscle and supporting an active lifestyle.
        If you'd like to learn more, you can explore the formula below.
    </p>

    <a class="button"
       href="{AFFILIATE_LINK}"
       target="_blank"
       rel="nofollow sponsored">
       Explore the Formula
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


# =========================
# PREMIUM HOMEPAGE
# =========================

def build_homepage():
    articles = []

    if os.path.exists(CONTENT_DIR):
        for filename in os.listdir(CONTENT_DIR):

            if not filename.endswith(".html"):
                continue

            path = os.path.join(CONTENT_DIR, filename)

            try:
                with open(path, "r", encoding="utf-8") as f:
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
                        match.group(1)
                    ).strip()

                    articles.append(
                        (title, filename)
                    )

            except Exception:
                pass

    articles = sorted(
        articles,
        key=lambda x: x[1],
        reverse=True
    )[:12]

    cards = []

    for title, filename in articles:

        cards.append(
            f"""
            <a class="card" href="content/{html.escape(filename)}">
                <div class="card-label">GUIDE</div>
                <h3>{html.escape(title)}</h3>
                <span>Read guide →</span>
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

<title>{SITE_NAME} — Age well. Live strong.</title>

<meta name="description"
content="Practical ideas for strength, vitality, mobility and healthy aging.">

<style>

* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    background: #f7f7f3;
    color: #151515;
    font-family: Arial, Helvetica, sans-serif;
}}

nav {{
    padding: 25px 7%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(247,247,243,.95);
}}

.logo {{
    font-size: 21px;
    font-weight: 800;
    letter-spacing: -.7px;
}}

.nav-text {{
    font-size: 13px;
    opacity: .55;
}}

.hero {{
    min-height: 78vh;
    display: flex;
    align-items: center;
    padding: 70px 7%;
}}

.hero-inner {{
    max-width: 1050px;
}}

.eyebrow {{
    text-transform: uppercase;
    letter-spacing: 3px;
    font-size: 12px;
    font-weight: 700;
    opacity: .5;
}}

h1 {{
    font-size: clamp(64px, 11vw, 150px);
    line-height: .88;
    letter-spacing: -9px;
    max-width: 1000px;
    margin: 25px 0;
}}

.hero p {{
    max-width: 620px;
    font-size: 21px;
    line-height: 1.55;
    opacity: .68;
}}

.scroll {{
    margin-top: 50px;
    font-size: 12px;
    letter-spacing: 2px;
    text-transform: uppercase;
    opacity: .45;
}}

.section {{
    padding: 110px 7%;
}}

.section-inner {{
    max-width: 1200px;
    margin: auto;
}}

.section-title {{
    max-width: 700px;
    font-size: clamp(42px, 6vw, 76px);
    line-height: 1;
    letter-spacing: -4px;
}}

.section-intro {{
    max-width: 650px;
    font-size: 18px;
    line-height: 1.7;
    opacity: .65;
}}

.grid {{
    margin-top: 65px;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
}}

.card {{
    display: block;
    text-decoration: none;
    color: #151515;
    background: white;
    border: 1px solid #e3e3dd;
    border-radius: 25px;
    padding: 32px;
    min-height: 270px;
    transition: transform .25s ease;
}}

.card:hover {{
    transform: translateY(-5px);
}}

.card-label {{
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
    opacity: .4;
}}

.card h3 {{
    font-size: 27px;
    line-height: 1.12;
    letter-spacing: -1px;
    margin-top: 45px;
}}

.card span {{
    font-size: 13px;
    opacity: .55;
}}

.dark {{
    background: #171717;
    color: white;
}}

.pill-row {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 40px;
}}

.pill {{
    border: 1px solid #cfcfc7;
    border-radius: 999px;
    padding: 12px 18px;
    font-size: 13px;
}}

.dark .pill {{
    border-color: #555;
}}

.disclosure {{
    max-width: 700px;
    margin-top: 45px;
    font-size: 12px;
    opacity: .45;
}}

footer {{
    padding: 55px 7%;
    border-top: 1px solid #deded8;
    text-align: center;
    font-size: 13px;
    opacity: .5;
}}

@media (max-width: 800px) {{

    .hero {{
        min-height: 70vh;
    }}

    h1 {{
        letter-spacing: -5px;
    }}

    .grid {{
        grid-template-columns: 1fr;
    }}

    .section {{
        padding: 75px 7%;
    }}

}}

</style>

</head>

<body>

<nav>
    <div class="logo">{SITE_NAME}</div>
    <div class="nav-text">Healthy aging, thoughtfully.</div>
</nav>

<header class="hero">

    <div class="hero-inner">

        <div class="eyebrow">
            Strength · Vitality · Healthy aging
        </div>

        <h1>
            Age well.<br>
            Live strong.
        </h1>

        <p>
            Practical ideas for building better habits around strength,
            mobility, recovery and everyday vitality — without the hype.
        </p>

        <div class="scroll">
            Explore the guides ↓
        </div>

    </div>

</header>

<section class="section">

    <div class="section-inner">

        <div class="eyebrow">
            A different approach
        </div>

        <h2 class="section-title">
            Your best years aren't behind you.
        </h2>

        <p class="section-intro">
            Getting older doesn't mean giving up on strength or an active
            life. Small, consistent choices around movement, nutrition,
            sleep and recovery can help you build a lifestyle that supports
            the way you want to live.
        </p>

    </div>

</section>

<section class="section">

    <div class="section-inner">

        <div class="eyebrow">
            Latest guides
        </div>

        <h2 class="section-title">
            Ideas worth reading.
        </h2>

        <div class="grid">
            {cards_html}
        </div>

    </div>

</section>

<section class="section dark">

    <div class="section-inner">

        <div class="eyebrow">
            Start simple
        </div>

        <h2 class="section-title">
            Better habits.<br>
            Stronger days.
        </h2>

        <p class="section-intro">
            Explore practical approaches to movement, nutrition,
            recovery and healthy aging.
        </p>

        <div class="pill-row">

            <div class="pill">Muscle & strength</div>
            <div class="pill">Healthy aging</div>
            <div class="pill">Nutrition</div>
            <div class="pill">Recovery</div>
            <div class="pill">Mobility</div>

        </div>

        <div class="disclosure">
            {DISCLOSURE}
        </div>

    </div>

</section>

<footer>
    © {datetime.now().year} {SITE_NAME}
</footer>

</body>

</html>
"""


# =========================
# MAIN AGENT
# =========================

def main():

    os.makedirs(CONTENT_DIR, exist_ok=True)

    existing_titles = get_existing_titles()

    print("Existing articles:", len(existing_titles))

    # Rotate topics based on current number of articles
    topic_index = len(existing_titles) % len(TOPICS)

    topic = TOPICS[topic_index]

    print("Selected topic:", topic)

    title = None
    body = None

    # Try several topics if duplicate is encountered
    for offset in range(len(TOPICS)):

        selected_topic = TOPICS[
            (topic_index + offset) % len(TOPICS)
        ]

        print("Trying:", selected_topic)

        try:
            new_title, new_body = generate_article(
                selected_topic,
                existing_titles
            )

        except Exception as e:
            print("Generation failed:", e)
            continue

        if new_title and new_body:

            title = new_title
            body = new_body
            break

    if not title:
        print("No new article generated.")
        build_homepage()

        with open(
            "index.html",
            "w",
            encoding="utf-8"
        ) as f:
            f.write(build_homepage())

        return

    print("Generated:", title)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d-%H%M%S"
    )

    slug = slugify(title)

    filename = (
        f"{slug}-{timestamp}.html"
    )

    path = os.path.join(
        CONTENT_DIR,
        filename
    )

    body_html = markdown_to_html(body)

    page = article_html(
        title,
        body_html
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:
        f.write(page)

    print("Saved article:", path)

    # Rebuild homepage
    homepage = build_homepage()

    with open(
        "index.html",
        "w",
        encoding="utf-8"
    ) as f:
        f.write(homepage)

    print("Homepage updated.")

    print("Done.")


if __name__ == "__main__":
    main()
