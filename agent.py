import os
import requests
import html
import re
from datetime import datetime

API_KEY = os.environ["OPENROUTER_API_KEY"]

AFFILIATE_LINK = "https://www.advancedbionutritionals.com/DS24/Advanced-Amino/Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld"

TOPICS = [
    "How to maintain muscle and strength as you age",
    "Practical nutrition habits for active older adults",
    "What to consider when choosing an amino-acid supplement",
    "Amino acids and recovery after exercise",
    "Protein vs amino acids for active aging",
    "How to support an active lifestyle after 50",
    "Nutrition considerations for maintaining strength",
    "Everyday habits that support healthy aging",
]


# -------------------------------------------------
# FIND PREVIOUS ARTICLES
# -------------------------------------------------

os.makedirs("content", exist_ok=True)

previous_titles = []

for file in os.listdir("content"):
    if file.endswith(".html"):
        try:
            with open(
                os.path.join("content", file),
                "r",
                encoding="utf-8"
            ) as f:
                old_content = f.read()

            matches = re.findall(
                r"<h1>(.*?)</h1>",
                old_content,
                re.IGNORECASE
            )

            for match in matches:
                clean_title = re.sub("<.*?>", "", match)
                previous_titles.append(clean_title)

        except Exception:
            pass


previous_text = "\n".join(previous_titles[-20:])

if not previous_text:
    previous_text = "No previous articles."


# -------------------------------------------------
# AI PROMPT
# -------------------------------------------------

PROMPT = f"""
You are an ethical affiliate content strategist targeting US buyers.

Create ONE genuinely useful, original article for a premium wellness website.

Choose ONE topic from this list:

1. {TOPICS[0]}
2. {TOPICS[1]}
3. {TOPICS[2]}
4. {TOPICS[3]}
5. {TOPICS[4]}
6. {TOPICS[5]}
7. {TOPICS[6]}
8. {TOPICS[7]}

PREVIOUS ARTICLE TITLES:
{previous_text}

IMPORTANT:
- Choose a topic and angle substantially different from previous articles.
- Do not repeat previous titles.
- Do not repeat the same main argument.
- Target US readers.
- Write for adults interested in healthy aging and active living.
- Give genuinely useful information.
- Include practical tips.
- Have natural buyer intent without being pushy.
- Do not make disease treatment or cure claims.
- Do not promise guaranteed results.
- Do not invent studies, statistics, reviews or testimonials.
- Do not pretend to be a doctor.
- Do not use the product or brand name in the SEO title.
- Do not keyword stuff.
- Do not create fake urgency.
- Do not create fake scarcity.
- Do not create fake discounts.
- Do not create fake testimonials.
- Do not make unsupported medical claims.
- Mention Advanced Amino Formula only in the recommendation section.
- Do not claim that the product treats or cures a disease.
- Include this exact disclosure:

"I may earn a commission if you buy through links on this page, at no extra cost to you."

Return ONLY Markdown.

Structure:

# SEO Title

## Introduction

## Main Guide

## Practical Tips

## What to Consider Before Choosing a Supplement

## Recommended Option

## Conclusion

## Affiliate Disclosure
"""


# -------------------------------------------------
# CALL OPENROUTER
# -------------------------------------------------

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
    timeout=120,
)

response.raise_for_status()

data = response.json()

article = data["choices"][0]["message"]["content"].strip()


# -------------------------------------------------
# MARKDOWN → HTML
# -------------------------------------------------

def markdown_to_html(markdown_text):

    lines = markdown_text.splitlines()

    output = []

    in_list = False

    for line in lines:

        line = line.strip()

        if not line:

            if in_list:
                output.append("</ul>")
                in_list = False

            continue

        if line.startswith("# "):

            title = html.escape(
                line[2:].strip()
            )

            output.append(
                f"<h1>{title}</h1>"
            )

        elif line.startswith("## "):

            heading = html.escape(
                line[3:].strip()
            )

            output.append(
                f"<h2>{heading}</h2>"
            )

        elif line.startswith("### "):

            heading = html.escape(
                line[4:].strip()
            )

            output.append(
                f"<h3>{heading}</h3>"
            )

        elif line.startswith("- "):

            if not in_list:

                output.append("<ul>")

                in_list = True

            text = html.escape(
                line[2:].strip()
            )

            output.append(
                f"<li>{text}</li>"
            )

        else:

            if in_list:

                output.append("</ul>")

                in_list = False

            text = html.escape(line)

            text = re.sub(
                r"\*\*(.*?)\*\*",
                r"<strong>\1</strong>",
                text
            )

            output.append(
                f"<p>{text}</p>"
            )

    if in_list:
        output.append("</ul>")

    return "\n".join(output)


article_html = markdown_to_html(article)


# -------------------------------------------------
# GET ARTICLE TITLE
# -------------------------------------------------

title_match = re.search(
    r"<h1>(.*?)</h1>",
    article_html,
    re.IGNORECASE
)

if title_match:

    page_title = re.sub(
        "<.*?>",
        "",
        title_match.group(1)
    )

else:

    page_title = "Healthy Aging & Active Living"


# -------------------------------------------------
# DUPLICATE TITLE CHECK
# -------------------------------------------------

normalized_new_title = re.sub(
    r"[^a-z0-9]+",
    " ",
    page_title.lower()
).strip()

for old_title in previous_titles:

    normalized_old_title = re.sub(
        r"[^a-z0-9]+",
        " ",
        old_title.lower()
    ).strip()

    if normalized_new_title == normalized_old_title:

        raise RuntimeError(
            "Duplicate article title detected. "
            "Stopping instead of publishing duplicate content."
        )


# -------------------------------------------------
# CREATE SAFE FILENAME
# -------------------------------------------------

timestamp = datetime.now().strftime(
    "%Y-%m-%d-%H%M%S"
)

slug = re.sub(
    r"[^a-z0-9]+",
    "-",
    page_title.lower()
).strip("-")

if not slug:

    slug = f"article-{timestamp}"


filename = (
    f"content/"
    f"{slug}-"
    f"{timestamp}.html"
)


# -------------------------------------------------
# CREATE ARTICLE PAGE
# -------------------------------------------------

html_page = f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
{html.escape(page_title)} | StrongerYears
</title>

<meta name="description"
content="Practical information about healthy aging,
muscle support, strength, recovery, energy and active living.">

<style>

* {{
box-sizing:border-box;
}}

body {{
margin:0;
font-family:Arial,Helvetica,sans-serif;
background:#f7faf8;
color:#173b3d;
line-height:1.75;
}}

header {{
background:white;
border-bottom:1px solid #e5eeee;
padding:18px 6%;
}}

.nav {{
max-width:1120px;
margin:auto;
display:flex;
justify-content:space-between;
align-items:center;
}}

.logo {{
font-size:23px;
font-weight:800;
}}

.logo span {{
color:#23815f;
}}

nav a {{
margin-left:25px;
text-decoration:none;
color:#173b3d;
font-weight:600;
}}

.hero {{
padding:75px 20px;
background:linear-gradient(
135deg,
#e8f3ed,
#ffffff
);
}}

.hero-inner {{
max-width:900px;
margin:auto;
}}

.hero h1 {{
font-size:clamp(38px,6vw,64px);
line-height:1.08;
margin:20px 0;
}}

.hero p {{
font-size:18px;
color:#596d6d;
}}

.container {{
max-width:900px;
margin:55px auto;
padding:0 20px;
}}

.article {{
background:white;
padding:45px;
border-radius:20px;
box-shadow:
0 12px 40px rgba(20,60,60,.07);
}}

.article h2 {{
margin-top:42px;
font-size:30px;
}}

.article li {{
margin:8px 0;
}}

.recommend {{
margin-top:45px;
padding:30px;
border-radius:18px;
background:#edf7f1;
border:1px solid #d8eadf;
}}

.cta {{
display:inline-block;
margin-top:15px;
padding:14px 25px;
background:#23815f;
color:white;
text-decoration:none;
border-radius:30px;
font-weight:700;
}}

.disclosure {{
margin-top:40px;
padding:20px;
background:#f4f6f5;
border-radius:12px;
font-size:14px;
}}

footer {{
text-align:center;
padding:40px 20px;
color:#718080;
font-size:13px;
}}

@media(max-width:700px) {{

.article {{
padding:25px;
}}

}}

</style>

</head>

<body>

<header>

<div class="nav">

<div class="logo">
Stronger<span>Years</span>
</div>

<nav>

<a href="../index.html">
Home
</a>

</nav>

</div>

</header>

<section class="hero">

<div class="hero-inner">

<div style="
text-transform:uppercase;
letter-spacing:2px;
font-size:13px;
">

Healthy Aging • Active Living

</div>

<h1>
{html.escape(page_title)}
</h1>

<p>
Practical information to help you make more
informed decisions about an active and
healthy lifestyle.
</p>

</div>

</section>

<main class="container">

<article class="article">

{article_html}

<div class="recommend">

<h2>
Recommended Option
</h2>

<p>
If you are considering an amino-acid formula
as part of your nutrition routine, you can learn
more about Advanced Amino Formula from
Advanced Bionutritionals.
</p>

<a class="cta"
href="{AFFILIATE_LINK}"
rel="nofollow sponsored noopener"
target="_blank">

Learn More

</a>

</div>

<div class="disclosure">

<strong>
Affiliate Disclosure
</strong>

<p>
I may earn a commission if you buy through
links on this page, at no extra cost to you.
</p>

</div>

</article>

</main>

<footer>

© 2026 StrongerYears · Educational content only.
Not medical advice.

</footer>

</body>

</html>
"""


with open(
    filename,
    "w",
    encoding="utf-8"
) as f:

    f.write(html_page)


# -------------------------------------------------
# AUTOMATIC HOMEPAGE
# -------------------------------------------------

articles = []

for file in os.listdir("content"):

    if file.endswith(".html"):

        articles.append(file)


articles.sort(reverse=True)


cards = []

for article_file in articles[:10]:

    article_path = os.path.join(
        "content",
        article_file
    )

    try:

        with open(
            article_path,
            "r",
            encoding="utf-8"
        ) as f:

            content = f.read()


        match = re.search(
            r"<h1>(.*?)</h1>",
            content,
            re.IGNORECASE
        )


        if match:

            article_title = re.sub(
                "<.*?>",
                "",
                match.group(1)
            )

        else:

            article_title = article_file


        cards.append(
            f"""
<div class="article-card">

<h3>
{html.escape(article_title)}
</h3>

<p>
Explore this practical guide from
StrongerYears.
</p>

<a class="read-more"
href="content/{article_file}">

Read Full Article →

</a>

</div>
"""
        )

    except Exception:

        continue


article_cards = "\n".join(cards)


# -------------------------------------------------
# HOMEPAGE HTML
# -------------------------------------------------

latest_link = (
    f"content/{articles[0]}"
    if articles
    else "#"
)


homepage = f"""<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>
StrongerYears | Healthy Aging & Active Living
</title>

<meta name="description"
content="Practical guides for healthy aging,
muscle support, nutrition, strength,
recovery and active living.">

<style>

* {{
box-sizing:border-box;
}}

body {{
margin:0;
font-family:Arial,Helvetica,sans-serif;
background:#f7faf8;
color:#173b3d;
line-height:1.7;
}}

header {{
background:white;
border-bottom:1px solid #e5eeee;
padding:18px 6%;
}}

.nav {{
max-width:1120px;
margin:auto;
display:flex;
justify-content:space-between;
align-items:center;
}}

.logo {{
font-size:23px;
font-weight:800;
}}

.logo span {{
color:#23815f;
}}

nav a {{
margin-left:25px;
text-decoration:none;
color:#173b3d;
font-weight:600;
}}

.hero {{
padding:85px 20px;
background:linear-gradient(
135deg,
#e8f3ed,
#ffffff
);
}}

.hero-inner {{
max-width:950px;
margin:auto;
text-align:center;
}}

.badge {{
display:inline-block;
padding:7px 14px;
border-radius:30px;
background:white;
font-size:13px;
font-weight:700;
letter-spacing:1px;
text-transform:uppercase;
}}

.hero h1 {{
font-size:clamp(42px,7vw,70px);
line-height:1.05;
margin:22px 0;
}}

.hero p {{
max-width:700px;
margin:auto;
font-size:19px;
color:#526969;
}}

.container {{
max-width:1120px;
margin:60px auto;
padding:0 20px;
}}

.section-title {{
text-align:center;
margin-bottom:35px;
}}

.section-title h2 {{
font-size:36px;
}}

.articles {{
display:grid;
grid-template-columns:
repeat(2,1fr);
gap:24px;
}}

.article-card {{
background:white;
padding:32px;
border-radius:20px;
box-shadow:
0 12px 40px rgba(20,60,60,.08);
border:1px solid #e4eeee;
}}

.article-card h3 {{
font-size:27px;
margin-top:0;
}}

.article-card p {{
color:#596d6d;
}}

.read-more {{
display:inline-block;
margin-top:15px;
padding:13px 22px;
border-radius:28px;
background:#173b3d;
color:white;
text-decoration:none;
font-weight:700;
}}

.topics {{
display:grid;
grid-template-columns:
repeat(3,1fr);
gap:22px;
}}

.topic {{
background:white;
padding:28px;
border-radius:18px;
border:1px solid #e5eeee;
}}

.topic p {{
color:#637575;
}}

.cta-section {{
margin-top:70px;
padding:55px 30px;
border-radius:24px;
background:#edf7f1;
text-align:center;
}}

.button {{
display:inline-block;
margin-top:20px;
padding:15px 28px;
border-radius:30px;
background:#23815f;
color:white;
text-decoration:none;
font-weight:700;
}}

.disclosure {{
max-width:800px;
margin:45px auto;
padding:20px;
background:white;
border-radius:12px;
font-size:13px;
color:#657777;
text-align:center;
}}

footer {{
padding:40px 20px;
text-align:center;
color:#718080;
font-size:13px;
}}

@media(max-width:750px) {{

nav {{
display:none;
}}

.articles,
.topics {{
grid-template-columns:1fr;
}}

}}

</style>

</head>

<body>

<header>

<div class="nav">

<div class="logo">
Stronger<span>Years</span>
</div>

<nav>

<a href="index.html">
Home
</a>

<a href="{latest_link}">
Latest Article
</a>

</nav>

</div>

</header>

<section class="hero">

<div class="hero-inner">

<div class="badge">
Healthy Aging • Active Living
</div>

<h1>
Build stronger habits for your later years.
</h1>

<p>
Practical, easy-to-understand guides covering
muscle support, nutrition, recovery, energy
and active living.
</p>

</div>

</section>

<section class="container">

<div class="section-title">

<h2>
Latest Articles
</h2>

<p>
Useful information designed to help you make
more informed wellness and lifestyle decisions.
</p>

</div>

<div class="articles">

{article_cards}

</div>

</section>

<section class="container">

<div class="section-title">

<h2>
Explore Our Topics
</h2>

<p>
Simple guides focused on active aging.
</p>

</div>

<div class="topics">

<div class="topic">

<h3>
💪 Muscle & Strength
</h3>

<p>
Practical habits and nutrition considerations
for maintaining strength and staying active.
</p>

</div>

<div class="topic">

<h3>
🥗 Nutrition
</h3>

<p>
Understand everyday nutrition choices and
what to consider when evaluating supplements.
</p>

</div>

<div class="topic">

<h3>
🚶 Active Aging
</h3>

<p>
Ideas for supporting an active lifestyle and
building healthy long-term habits.
</p>

</div>

</div>

</section>

<section class="container">

<div class="cta-section">

<h2>
Explore Your Nutrition Options
</h2>

<p>
If you're exploring amino-acid supplements as
part of your nutrition routine, you can learn
more about one option here.
</p>

<a class="button"
href="{AFFILIATE_LINK}"
rel="nofollow sponsored noopener"
target="_blank">

Learn More

</a>

</div>

<div class="disclosure">

<strong>
Affiliate Disclosure
</strong>

<br><br>

I may earn a commission if you buy through
links on this page, at no extra cost to you.

</div>

</section>

<footer>

© 2026 StrongerYears · Educational content only.
Not medical advice.

</footer>

</body>

</html>
"""


with open(
    "index.html",
    "w",
    encoding="utf-8"
) as f:

    f.write(homepage)


print(
    f"Article created: {filename}"
)

print(
    "Homepage automatically updated."
)

print(
    f"Previous articles found: {len(previous_titles)}"
)

print(
    f"Total articles now: {len(articles)}"
)
