import os
import re
import time
import html
import requests
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

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

os.makedirs(CONTENT_DIR, exist_ok=True)

# ============================================================
# CONTENT TOPICS
# ============================================================

TOPICS = [
    "How to maintain muscle strength as you get older",
    "Best ways to support strength and recovery after 50",
    "How protein and amino acids fit into healthy aging",
    "Simple habits for maintaining an active lifestyle as you age",
    "What to consider when choosing a muscle-support supplement",
    "How older adults can support strength and daily energy",
    "A practical guide to maintaining muscle while aging",
    "How nutrition supports an active lifestyle after 50",
    "What essential amino acids are and why people use them",
    "How to build a simple healthy-aging nutrition routine",
]


# ============================================================
# HELPERS
# ============================================================

def clean_title(title):
    title = re.sub(r"<[^>]+>", "", title)
    title = title.replace("#", "")
    return title.strip()


def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")[:90]


def get_existing_titles():
    titles = []

    for filename in os.listdir(CONTENT_DIR):

        if not filename.endswith(".html"):
            continue

        path = os.path.join(CONTENT_DIR, filename)

        try:

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            matches = re.findall(
                r"<h1[^>]*>(.*?)</h1>",
                content,
                flags=re.IGNORECASE | re.DOTALL
            )

            for match in matches:

                title = re.sub(
                    r"<[^>]+>",
                    "",
                    match
                )

                title = html.unescape(title).strip()

                if title:
                    titles.append(title)

        except Exception as e:
            print(f"Could not read {filename}: {e}")

    return titles


def markdown_to_html(markdown_text):

    lines = markdown_text.splitlines()

    output = []

    in_ul = False
    paragraph = []

    def flush_paragraph():

        nonlocal paragraph

        if paragraph:

            text = " ".join(
                x.strip()
                for x in paragraph
            ).strip()

            if text:
                output.append(
                    f"<p>{text}</p>"
                )

            paragraph = []

    for raw_line in lines:

        line = raw_line.strip()

        if not line:

            flush_paragraph()

            if in_ul:
                output.append("</ul>")
                in_ul = False

            continue

        if line.startswith("# "):

            flush_paragraph()

            if in_ul:
                output.append("</ul>")
                in_ul = False

            output.append(
                f"<h1>{line[2:].strip()}</h1>"
            )

            continue

        if line.startswith("## "):

            flush_paragraph()

            if in_ul:
                output.append("</ul>")
                in_ul = False

            output.append(
                f"<h2>{line[3:].strip()}</h2>"
            )

            continue

        if line.startswith("### "):

            flush_paragraph()

            if in_ul:
                output.append("</ul>")
                in_ul = False

            output.append(
                f"<h3>{line[4:].strip()}</h3>"
            )

            continue

        if line.startswith("- "):

            flush_paragraph()

            if not in_ul:
                output.append("<ul>")
                in_ul = True

            output.append(
                f"<li>{line[2:].strip()}</li>"
            )

            continue

        line = re.sub(
            r"\*\*(.*?)\*\*",
            r"<strong>\1</strong>",
            line
        )

        line = re.sub(
            r"\[(.*?)\]\((.*?)\)",
            r'<a href="\2" target="_blank" rel="nofollow sponsored noopener">\1</a>',
            line
        )

        paragraph.append(line)

    flush_paragraph()

    if in_ul:
        output.append("</ul>")

    return "\n".join(output)


def extract_h1(markdown):

    match = re.search(
        r"^#\s+(.+)$",
        markdown,
        flags=re.MULTILINE
    )

    if match:
        return clean_title(match.group(1))

    return "A Stronger Approach to Healthy Aging"


# ============================================================
# EXISTING CONTENT
# ============================================================

existing_titles = get_existing_titles()

topic_index = len(existing_titles) % len(TOPICS)

selected_topic = TOPICS[topic_index]

print("========================================")
print("STRONGERYEARS AI AGENT")
print("========================================")
print(f"Existing articles: {len(existing_titles)}")
print(f"Selected topic: {selected_topic}")


previous_titles = "\n".join(
    f"- {title}"
    for title in existing_titles[-20:]
)


# ============================================================
# AI PROMPT
# ============================================================

PROMPT = f"""
You are the senior editorial writer for a premium US wellness
and healthy-aging publication called StrongerYears.

Today's article topic:

{selected_topic}

Audience:

US adults, especially adults interested in healthy aging,
maintaining muscle, strength, recovery, energy and active living.

Write ONE exceptional, original article.

The article must feel like premium editorial content rather than
generic AI content.

Writing style:

- intelligent
- calm
- confident
- useful
- modern
- human
- easy to read
- no hype
- no keyword stuffing
- short paragraphs
- strong transitions
- practical examples
- clear explanations

The reader should feel that the article genuinely helped them.

Do not use the product or brand name in the SEO title.

Do not make medical treatment or cure claims.

Do not diagnose conditions.

Do not promise guaranteed results.

Do not invent studies.

Do not invent statistics.

Do not invent reviews.

Do not invent testimonials.

Do not pretend to be a doctor.

Do not use fake urgency or fake scarcity.

Do not use fear-based marketing.

When discussing supplements, explain sensible considerations
such as ingredients, quality, personal goals and individual needs.

Naturally introduce this product as an optional product to research:

Advanced Amino Formula by Advanced Bionutritionals

Affiliate link:

{AFFILIATE_LINK}

Do not put the affiliate link throughout the article.
The website will add the final recommendation CTA automatically.

Include practical sections that answer real questions people may have.

Previous article titles:

{previous_titles}

Do NOT reuse any previous title.

Structure:

# Strong SEO-friendly title

## Introduction

## Main educational section

## Another useful section

## Practical steps

## What to consider before choosing a supplement

## Recommended option

## Conclusion

## Affiliate Disclosure

Use this exact disclosure:

{DISCLOSURE}

Length:

1000-1500 words.

Return ONLY Markdown.
"""


# ============================================================
# OPENROUTER WITH 3 RETRIES
# ============================================================

article = None
last_error = None

for attempt in range(1, 4):

    try:

        print(
            f"AI request attempt {attempt}/3"
        )

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openrouter/free",
                "messages": [
                    {
                        "role": "user",
                        "content": PROMPT
                    }
                ],
            },
            timeout=(20, 180),
        )

        response.raise_for_status()

        data = response.json()

        if "choices" not in data:
            raise RuntimeError(
                f"OpenRouter response missing choices: {data}"
            )

        article = (
            data["choices"][0]["message"]["content"]
            .strip()
        )

        if not article:
            raise RuntimeError(
                "AI returned an empty article."
            )

        print(
            "AI article generated successfully."
        )

        break

    except Exception as e:

        last_error = e

        print(
            f"AI request failed on attempt {attempt}: {e}"
        )

        if attempt < 3:

            print(
                "Waiting 10 seconds before retry..."
            )

            time.sleep(10)

        else:

            raise RuntimeError(
                f"OpenRouter failed after 3 attempts: {last_error}"
            )


# ============================================================
# TITLE
# ============================================================

article = article.strip()

title = extract_h1(article)

print(f"Generated title: {title}")


# ============================================================
# DUPLICATE PROTECTION
# ============================================================

existing_normalized = {
    re.sub(
        r"\s+",
        " ",
        title.lower()
    ).strip()
    for title in existing_titles
}

if title.lower().strip() in existing_normalized:

    print(
        "Duplicate title detected."
    )

    retry_prompt = PROMPT + """

IMPORTANT:

The title you generated is already used.

Create a completely different article title
and a completely different article.

Do NOT reuse any previous title.
"""

    replacement = None

    for attempt in range(1, 4):

        try:

            print(
                f"Replacement request {attempt}/3"
            )

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "openrouter/free",
                    "messages": [
                        {
                            "role": "user",
                            "content": retry_prompt
                        }
                    ],
                },
                timeout=(20, 180),
            )

            response.raise_for_status()

            data = response.json()

            replacement = (
                data["choices"][0]["message"]["content"]
                .strip()
            )

            replacement_title = extract_h1(
                replacement
            )

            if (
                replacement_title.lower().strip()
                not in existing_normalized
            ):

                article = replacement
                title = replacement_title

                print(
                    f"Replacement accepted: {title}"
                )

                break

        except Exception as e:

            print(
                f"Replacement failed: {e}"
            )

            if attempt < 3:
                time.sleep(10)

    if title.lower().strip() in existing_normalized:

        print(
            "Could not create a unique article."
        )

        raise SystemExit(0)


# ============================================================
# CONVERT ARTICLE
# ============================================================

article_html = markdown_to_html(article)


# Remove AI-generated affiliate disclosure.
article_html = re.sub(
    r"<h2>Affiliate Disclosure</h2>.*?(?=<h2>|$)",
    "",
    article_html,
    flags=re.IGNORECASE | re.DOTALL
)


# ============================================================
# PREMIUM RECOMMENDATION
# ============================================================

affiliate_section = f"""

<section class="recommendation">

    <div class="recommendation-kicker">
        A PRODUCT WORTH RESEARCHING
    </div>

    <h2>
        Looking for an amino-acid option?
    </h2>

    <p>
        If you are exploring amino-acid supplements as part of
        an overall approach to healthy aging and active living,
        Advanced Amino Formula is one option you can research.
    </p>

    <p>
        Review the formula, ingredients and manufacturer's
        information to decide whether it fits your own needs.
    </p>

    <a
        class="premium-button"
        href="{AFFILIATE_LINK}"
        target="_blank"
        rel="nofollow sponsored noopener"
    >
        Explore the Formula
        <span>↗</span>
    </a>

    <p class="small-note">
        Consider your individual needs and consult a qualified
        healthcare professional when appropriate.
    </p>

</section>

<section class="disclosure">

    <div class="disclosure-title">
        Affiliate Disclosure
    </div>

    <p>
        {DISCLOSURE}
    </p>

</section>
"""

article_html += affiliate_section


# ============================================================
# ARTICLE FILE
# ============================================================

slug = slugify(title)

timestamp = datetime.now().strftime(
    "%Y-%m-%d-%H%M%S"
)

filename = f"{slug}-{timestamp}.html"

filepath = os.path.join(
    CONTENT_DIR,
    filename
)


article_page = f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
{html.escape(title)} | {SITE_NAME}
</title>

<meta
    name="description"
    content="{html.escape(title)} — practical guidance for healthy aging, strength and active living."
>

<meta
    name="robots"
    content="index,follow"
>

<style>

:root {{

    --ink: #111713;
    --soft-ink: #445049;
    --green: #183b2e;
    --green-2: #2f624d;
    --cream: #f5f3ed;
    --paper: #fffefa;
    --line: #deded6;
    --gold: #b49a68;
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

    line-height: 1.8;
}}

.topbar {{

    position: sticky;

    top: 0;

    z-index: 20;

    background:
        rgba(245,243,237,.92);

    backdrop-filter:
        blur(18px);

    border-bottom:
        1px solid rgba(0,0,0,.07);
}}

.topbar-inner {{

    max-width: 1180px;

    margin: auto;

    padding: 18px 25px;

    display: flex;

    justify-content: space-between;

    align-items: center;
}}

.logo {{

    color: var(--ink);

    text-decoration: none;

    font-size: 19px;

    font-weight: 800;

    letter-spacing: -.5px;
}}

.nav-link {{

    color: var(--soft-ink);

    text-decoration: none;

    font-size: 14px;

    font-weight: 600;
}}

.article-hero {{

    min-height: 74vh;

    display: flex;

    align-items: center;

    padding: 90px 25px;

    background:

        radial-gradient(
            circle at 80% 20%,
            rgba(180,154,104,.18),
            transparent 28%
        ),

        linear-gradient(
            135deg,
            #edf0e9,
            #f5f3ed
        );
}}

.hero-inner {{

    width: 100%;

    max-width: 1080px;

    margin: auto;
}}

.kicker {{

    display: inline-block;

    margin-bottom: 22px;

    color: var(--green-2);

    font-size: 12px;

    font-weight: 800;

    letter-spacing: 2px;

    text-transform: uppercase;
}}

.article-hero h1 {{

    max-width: 950px;

    margin: 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(48px, 8vw, 94px);

    line-height: .98;

    letter-spacing: -4px;

    color: var(--ink);
}}

.hero-line {{

    width: 70px;

    height: 3px;

    margin-top: 35px;

    background: var(--gold);
}}

.article-shell {{

    max-width: 900px;

    margin: 0 auto;

    padding: 75px 25px 100px;
}}

.article-content {{

    font-size: 18px;

    color: #29332e;
}}

.article-content h1 {{
    display: none;
}}

.article-content h2 {{

    margin-top: 65px;

    margin-bottom: 20px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 35px;

    line-height: 1.2;

    letter-spacing: -.7px;

    color: var(--green);
}}

.article-content h3 {{

    margin-top: 40px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 24px;

    color: var(--green);
}}

.article-content p {{

    margin:
        0 0 25px;
}}

.article-content ul {{

    margin:
        25px 0 35px;

    padding-left: 28px;
}}

.article-content li {{

    margin-bottom: 12px;
}}

.article-content a {{

    color: var(--green-2);

    font-weight: 700;
}}

.recommendation {{

    margin-top: 80px;

    padding:
        55px;

    background:
        linear-gradient(
            135deg,
            #183b2e,
            #295640
        );

    color: white;

    border-radius: 4px;

    box-shadow:
        0 25px 70px
        rgba(24,59,46,.18);
}}

.recommendation-kicker {{

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2px;

    opacity: .72;

    margin-bottom: 18px;
}}

.recommendation h2 {{

    margin:
        0 0 20px;

    color: white;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 42px;

    line-height: 1.1;
}}

.recommendation p {{

    max-width: 650px;

    color:
        rgba(255,255,255,.82);

    font-size: 17px;
}}

.premium-button {{

    display: inline-flex;

    align-items: center;

    gap: 20px;

    margin-top: 18px;

    padding:
        16px 23px;

    background: white;

    color: var(--green) !important;

    text-decoration: none;

    font-weight: 800;

    border-radius: 2px;
}}

.premium-button span {{
    font-size: 18px;
}}

.small-note {{

    margin-top: 22px !important;

    font-size: 13px !important;

    opacity: .65;
}}

.disclosure {{

    margin-top: 60px;

    padding-top: 28px;

    border-top:
        1px solid var(--line);

    color: #737b75;

    font-size: 13px;
}}

.disclosure-title {{

    margin-bottom: 8px;

    color: var(--ink);

    font-weight: 800;
}}

footer {{

    padding:
        45px 25px;

    background: #101914;

    color:
        rgba(255,255,255,.65);

    text-align: center;

    font-size: 13px;
}}

@media (max-width: 650px) {{

    .topbar-inner {{
        padding: 15px 18px;
    }}

    .article-hero {{
        min-height: 65vh;
        padding: 70px 20px;
    }}

    .article-hero h1 {{
        font-size: 50px;
        letter-spacing: -2px;
    }}

    .article-shell {{
        padding:
            55px 20px 75px;
    }}

    .article-content {{
        font-size: 17px;
    }}

    .article-content h2 {{
        font-size: 30px;
        margin-top: 50px;
    }}

    .recommendation {{
        padding: 32px 25px;
    }}

    .recommendation h2 {{
        font-size: 34px;
    }}

}}

</style>

</head>

<body>

<header class="topbar">

    <div class="topbar-inner">

        <a
            class="logo"
            href="../index.html"
        >
            StrongerYears
        </a>

        <a
            class="nav-link"
            href="../index.html"
        >
            All Guides
        </a>

    </div>

</header>


<section class="article-hero">

    <div class="hero-inner">

        <div class="kicker">
            StrongerYears / Editorial Guide
        </div>

        <h1>
            {html.escape(title)}
        </h1>

        <div class="hero-line"></div>

    </div>

</section>


<main class="article-shell">

    <article class="article-content">

        {article_html}

    </article>

</main>


<footer>

    © {datetime.now().year} StrongerYears

    <br><br>

    Practical information for healthy aging and active living.

</footer>

</body>

</html>
"""


with open(
    filepath,
    "w",
    encoding="utf-8"
) as f:

    f.write(article_page)


print(
    f"Article created: {filepath}"
)


# ============================================================
# BUILD HOMEPAGE
# ============================================================

articles = []

for filename in os.listdir(CONTENT_DIR):

    if not filename.endswith(".html"):
        continue

    path = os.path.join(
        CONTENT_DIR,
        filename
    )

    try:

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()

        match = re.search(
            r"<h1[^>]*>(.*?)</h1>",
            content,
            flags=re.IGNORECASE | re.DOTALL
        )

        if match:

            article_title = re.sub(
                r"<[^>]+>",
                "",
                match.group(1)
            )

            article_title = html.unescape(
                article_title
            ).strip()

        else:

            article_title = (
                filename
                .replace(".html", "")
                .replace("-", " ")
                .title()
            )

        articles.append(
            {
                "filename": filename,
                "title": article_title,
            }
        )

    except Exception as e:

        print(
            f"Could not process {filename}: {e}"
        )


articles.sort(
    key=lambda x: x["filename"],
    reverse=True
)

latest_articles = articles[:10]


# ============================================================
# PREMIUM ARTICLE CARDS
# ============================================================

cards = ""

for number, item in enumerate(
    latest_articles,
    start=1
):

    cards += f"""

    <article class="story-card">

        <div class="story-number">
            0{number}
        </div>

        <div class="story-body">

            <div class="story-category">
                HEALTHY AGING / GUIDE
            </div>

            <h3>
                {html.escape(item["title"])}
            </h3>

            <a
                href="content/{html.escape(item["filename"])}"
            >
                Read article
                <span>↗</span>
            </a>

        </div>

    </article>

    """


if not cards:

    cards = """

    <div class="empty-state">
        New guides are coming soon.
    </div>

    """


# ============================================================
# PREMIUM HOMEPAGE
# ============================================================

homepage_html = f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
>

<title>
StrongerYears — A Better Way to Age Strong
</title>

<meta
    name="description"
    content="Practical, thoughtful guides for strength, nutrition, recovery and active living as you age."
>

<meta
    name="robots"
    content="index,follow"
>

<style>

:root {{

    --ink: #111713;
    --green: #183b2e;
    --green-2: #2f624d;
    --cream: #f5f3ed;
    --white: #fffefa;
    --line: #deded6;
    --gold: #b49a68;
    --muted: #68736d;
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
}}

.header {{

    position: sticky;

    top: 0;

    z-index: 50;

    background:
        rgba(245,243,237,.9);

    backdrop-filter:
        blur(20px);

    border-bottom:
        1px solid rgba(0,0,0,.06);
}}

.header-inner {{

    max-width: 1180px;

    margin: auto;

    padding: 18px 25px;

    display: flex;

    align-items: center;

    justify-content: space-between;
}}

.logo {{

    color: var(--ink);

    text-decoration: none;

    font-size: 20px;

    font-weight: 850;

    letter-spacing: -1px;
}}

.header-link {{

    color: var(--muted);

    text-decoration: none;

    font-size: 13px;

    font-weight: 700;
}}


/* HERO */

.hero {{

    min-height: 88vh;

    display: flex;

    align-items: center;

    padding:
        90px 25px;

    background:

        radial-gradient(
            circle at 82% 18%,
            rgba(180,154,104,.2),
            transparent 25%
        ),

        radial-gradient(
            circle at 10% 80%,
            rgba(47,98,77,.1),
            transparent 30%
        ),

        linear-gradient(
            135deg,
            #edf0e9,
            #f5f3ed
        );
}}

.hero-inner {{

    width: 100%;

    max-width: 1180px;

    margin: auto;
}}

.hero-kicker {{

    display: inline-block;

    margin-bottom: 24px;

    color: var(--green-2);

    font-size: 12px;

    font-weight: 800;

    letter-spacing: 2.5px;

    text-transform: uppercase;
}}

.hero h1 {{

    max-width: 1000px;

    margin: 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(58px, 9vw, 118px);

    line-height: .9;

    letter-spacing: -6px;

    font-weight: 500;
}}

.hero h1 em {{

    color: var(--green-2);

    font-style: italic;
}}

.hero-copy {{

    max-width: 620px;

    margin-top: 38px;

    color: var(--muted);

    font-size: 19px;

    line-height: 1.65;
}}

.hero-bottom {{

    margin-top: 55px;

    display: flex;

    align-items: center;

    gap: 25px;

    flex-wrap: wrap;
}}

.hero-button {{

    display: inline-flex;

    align-items: center;

    gap: 20px;

    padding:
        16px 22px;

    background: var(--green);

    color: white;

    text-decoration: none;

    font-size: 14px;

    font-weight: 800;

    border-radius: 2px;
}}

.hero-button span {{
    font-size: 18px;
}}

.hero-note {{

    color: var(--muted);

    font-size: 13px;
}}


/* INTRO STRIP */

.intro {{

    background: var(--green);

    color: white;

    padding:
        95px 25px;
}}

.intro-inner {{

    max-width: 1000px;

    margin: auto;

    text-align: center;
}}

.intro-label {{

    margin-bottom: 22px;

    color:
        rgba(255,255,255,.55);

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2.5px;
}}

.intro h2 {{

    margin: 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(38px, 5vw, 65px);

    line-height: 1.05;

    font-weight: 500;

    letter-spacing: -2px;
}}

.intro p {{

    max-width: 650px;

    margin:
        28px auto 0;

    color:
        rgba(255,255,255,.72);

    font-size: 17px;

    line-height: 1.7;
}}


/* STORIES */

.stories {{

    max-width: 1180px;

    margin: auto;

    padding:
        110px 25px;
}}

.section-top {{

    display: flex;

    align-items: end;

    justify-content: space-between;

    gap: 30px;

    margin-bottom: 50px;
}}

.section-kicker {{

    color: var(--green-2);

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2px;
}}

.section-title {{

    margin:
        10px 0 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(40px, 5vw, 62px);

    font-weight: 500;

    line-height: 1;

    letter-spacing: -2px;
}}

.story-list {{

    border-top:
        1px solid var(--line);
}}

.story-card {{

    display: grid;

    grid-template-columns:
        100px 1fr;

    padding:
        35px 0;

    border-bottom:
        1px solid var(--line);

    transition:
        padding .25s ease;
}}

.story-card:hover {{
    padding-left: 12px;
}}

.story-number {{

    color: var(--gold);

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 18px;
}}

.story-category {{

    margin-bottom: 12px;

    color: var(--muted);

    font-size: 10px;

    font-weight: 800;

    letter-spacing: 1.8px;
}}

.story-body h3 {{

    max-width: 800px;

    margin:
        0 0 20px;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(27px, 4vw, 44px);

    line-height: 1.1;

    letter-spacing: -1px;

    font-weight: 500;
}}

.story-body a {{

    color: var(--green-2);

    text-decoration: none;

    font-size: 13px;

    font-weight: 800;
}}

.story-body a span {{
    margin-left: 8px;
}}


/* BRAND SECTION */

.brand-section {{

    padding:
        120px 25px;

    background: #e8ebe3;
}}

.brand-inner {{

    max-width: 1180px;

    margin: auto;

    display: grid;

    grid-template-columns:
        1fr 1fr;

    gap: 90px;

    align-items: center;
}}

.brand-label {{

    color: var(--green-2);

    font-size: 11px;

    font-weight: 800;

    letter-spacing: 2px;
}}

.brand-inner h2 {{

    margin:
        15px 0 0;

    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size:
        clamp(40px, 5vw, 65px);

    line-height: 1;

    font-weight: 500;

    letter-spacing: -2px;
}}

.brand-copy {{

    color: var(--muted);

    font-size: 17px;

    line-height: 1.8;
}}

.pill-row {{

    display: flex;

    flex-wrap: wrap;

    gap: 10px;

    margin-top: 30px;
}}

.pill {{

    padding:
        9px 13px;

    border:
        1px solid #cdd2ca;

    color: var(--green);

    font-size: 11px;

    font-weight: 800;

    letter-spacing: .7px;
}}


/* DISCLOSURE */

.disclosure {{

    max-width: 850px;

    margin: auto;

    padding:
        60px 25px;

    color: var(--muted);

    font-size: 13px;

    line-height: 1.7;
}}

.disclosure-title {{

    color: var(--ink);

    font-weight: 800;

    margin-bottom: 7px;
}}


/* FOOTER */

.footer {{

    padding:
        50px 25px;

    background: #101914;

    color:
        rgba(255,255,255,.6);

    text-align: center;

    font-size: 13px;
}}

.footer strong {{

    display: block;

    margin-bottom: 10px;

    color: white;

    font-size: 16px;
}}


@media (max-width: 750px) {{

    .hero {{
        min-height: 82vh;
        padding: 75px 20px;
    }}

    .hero h1 {{
        font-size: 58px;
        letter-spacing: -3px;
    }}

    .hero-copy {{
        font-size: 17px;
    }}

    .intro {{
        padding: 75px 20px;
    }}

    .stories {{
        padding: 75px 20px;
    }}

    .section-top {{
        display: block;
    }}

    .story-card {{
        grid-template-columns:
            55px 1fr;
        padding:
            28px 0;
    }}

    .story-body h3 {{
        font-size: 29px;
    }}

    .brand-section {{
        padding: 75px 20px;
    }}

    .brand-inner {{
        grid-template-columns: 1fr;
        gap: 35px;
    }}

}}

</style>

</head>

<body>


<header class="header">

    <div class="header-inner">

        <a
            class="logo"
            href="index.html"
        >
            StrongerYears
        </a>

        <a
            class="header-link"
            href="#guides"
        >
            Explore Guides ↓
        </a>

    </div>

</header>


<section class="hero">

    <div class="hero-inner">

        <div class="hero-kicker">
            Healthy aging / Active living
        </div>

        <h1>
            Age well.<br>
            Live <em>strong.</em>
        </h1>

        <p class="hero-copy">

            Thoughtful, practical guidance for people who want
            to protect their strength, stay active and make
            smarter choices as the years go by.

        </p>

        <div class="hero-bottom">

            <a
                class="hero-button"
                href="#guides"
            >
                Explore the guides
                <span>↓</span>
            </a>

            <div class="hero-note">
                No hype. Just useful information.
            </div>

        </div>

    </div>

</section>


<section class="intro">

    <div class="intro-inner">

        <div class="intro-label">
            THE STRONGERYEARS APPROACH
        </div>

        <h2>
            Your best years aren't behind you.
        </h2>

        <p>

            Getting older changes your body.
            It doesn't have to shrink your ambitions.
            We make complex topics around nutrition,
            strength and active living easier to understand.

        </p>

    </div>

</section>


<section
    class="stories"
    id="guides"
>

    <div class="section-top">

        <div>

            <div class="section-kicker">
                THE JOURNAL
            </div>

            <h2 class="section-title">
                Latest Guides
            </h2>

        </div>

    </div>


    <div class="story-list">

        {cards}

    </div>

</section>


<section class="brand-section">

    <div class="brand-inner">

        <div>

            <div class="brand-label">
                WHAT WE COVER
            </div>

            <h2>
                Simple ideas.<br>
                Better habits.
            </h2>

        </div>


        <div>

            <p class="brand-copy">

                StrongerYears explores the everyday choices
                that can support an active, independent
                lifestyle — from nutrition and recovery
                to strength and healthy aging.

            </p>

            <div class="pill-row">

                <div class="pill">
                    STRENGTH
                </div>

                <div class="pill">
                    NUTRITION
                </div>

                <div class="pill">
                    RECOVERY
                </div>

                <div class="pill">
                    ACTIVE LIVING
                </div>

                <div class="pill">
                    HEALTHY AGING
                </div>

            </div>

        </div>

    </div>

</section>


<section class="disclosure">

    <div class="disclosure-title">
        Affiliate Disclosure
    </div>

    <div>
        {DISCLOSURE}
    </div>

</section>


<footer class="footer">

    <strong>
        StrongerYears
    </strong>

    Practical information for healthy aging and active living.

    <br><br>

    © {datetime.now().year} StrongerYears

</footer>


</body>

</html>
"""


with open(
    "index.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(homepage_html)


print(
    "Premium homepage generated successfully."
)

print("========================================")
print("STRONGERYEARS AGENT COMPLETED")
print("========================================")
