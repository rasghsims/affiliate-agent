import os
import requests
import html
import re
from datetime import datetime

API_KEY = os.environ["OPENROUTER_API_KEY"]

AFFILIATE_LINK = "https://www.advancedbionutritionals.com/DS24/Advanced-Amino/Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld"

PROMPT = """
You are an ethical affiliate content strategist targeting US buyers.

Create ONE genuinely useful, original article for a premium wellness website.

Topic:
Healthy aging, maintaining muscle, strength, recovery, energy and active living.

Affiliate product:
Advanced Amino Formula by Advanced Bionutritionals

Audience:
US adults interested in healthy aging, maintaining muscle, strength,
recovery, energy and active living.

Rules:
- Do not make disease treatment or cure claims.
- Do not promise guaranteed results.
- Do not invent studies, reviews, testimonials or statistics.
- Do not pretend to be a doctor.
- Do not use the product or brand name in the SEO title.
- Do not use keyword stuffing.
- Give genuinely useful information.
- Explain practical considerations when choosing an amino-acid supplement.
- Include a natural recommendation section.
- Use the product name only in the recommendation section.
- Do not create fake urgency, fake scarcity or fake discounts.
- Include this exact affiliate disclosure:
"I may earn a commission if you buy through links on this page, at no extra cost to you."

Return ONLY Markdown.

Structure:

# SEO Title

## Introduction

## Main useful sections

## What to Consider Before Choosing a Supplement

## Recommended Option

## Conclusion

## Affiliate Disclosure
"""

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

article = response.json()["choices"][0]["message"]["content"].strip()


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
            title = html.escape(line[2:].strip())
            output.append(f"<h1>{title}</h1>")

        elif line.startswith("## "):
            heading = html.escape(line[3:].strip())
            output.append(f"<h2>{heading}</h2>")

        elif line.startswith("### "):
            heading = html.escape(line[4:].strip())
            output.append(f"<h3>{heading}</h3>")

        elif line.startswith("- "):
            if not in_list:
                output.append("<ul>")
                in_list = True

            text = html.escape(line[2:].strip())
            output.append(f"<li>{text}</li>")

        elif re.match(r"^\d+\.\s+", line):
            if not in_list:
                output.append("<ol>")
                in_list = True

            text = re.sub(r"^\d+\.\s+", "", line)
            text = html.escape(text)
            output.append(f"<li>{text}</li>")

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

            output.append(f"<p>{text}</p>")

    if in_list:
        output.append("</ul>")

    return "\n".join(output)


article_html = markdown_to_html(article)


title_match = re.search(
    r"<h1>(.*?)</h1>",
    article_html,
    re.IGNORECASE
)

if title_match:
    page_title = re.sub("<.*?>", "", title_match.group(1))
else:
    page_title = "Healthy Aging & Active Living"


timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
slug = re.sub(r"[^a-z0-9]+", "-", page_title.lower()).strip("-")

if not slug:
    slug = f"article-{timestamp}"

os.makedirs("content", exist_ok=True)

filename = f"content/{slug}-{timestamp}.html"


html_page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{html.escape(page_title)} | StrongerYears</title>

<meta name="description"
content="Practical information about healthy aging, muscle support,
strength, recovery, energy and active living.">

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background: #f7faf8;
    color: #173b3d;
    line-height: 1.75;
}}

header {{
    background: white;
    border-bottom: 1px solid #e6eeee;
    padding: 18px 6%;
}}

.nav {{
    max-width: 1100px;
    margin: auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.logo {{
    font-size: 22px;
    font-weight: 700;
}}

.logo span {{
    color: #23815f;
}}

nav a {{
    color: #173b3d;
    text-decoration: none;
    margin-left: 24px;
}}

.hero {{
    background: linear-gradient(135deg, #e8f3ed, #ffffff);
    padding: 70px 20px;
}}

.hero-inner {{
    max-width: 900px;
    margin: auto;
}}

.hero h1 {{
    font-size: clamp(36px, 6vw, 58px);
    line-height: 1.1;
    margin: 0 0 20px;
}}

.container {{
    max-width: 900px;
    margin: 50px auto;
    padding: 0 20px;
}}

.article {{
    background: white;
    padding: 45px;
    border-radius: 18px;
    box-shadow: 0 10px 35px rgba(20,60,60,.07);
}}

.article h2 {{
    margin-top: 42px;
    font-size: 30px;
}}

.article h3 {{
    margin-top: 30px;
}}

.article ul {{
    padding-left: 25px;
}}

.article li {{
    margin: 8px 0;
}}

.recommend {{
    margin-top: 45px;
    padding: 30px;
    border-radius: 16px;
    background: #edf7f1;
    border: 1px solid #d8eadf;
}}

.cta {{
    display: inline-block;
    margin-top: 18px;
    padding: 14px 24px;
    background: #23815f;
    color: white;
    text-decoration: none;
    border-radius: 30px;
    font-weight: 700;
}}

.disclosure {{
    margin-top: 40px;
    padding: 20px;
    background: #f4f6f5;
    border-radius: 12px;
    font-size: 14px;
}}

footer {{
    text-align: center;
    padding: 40px 20px;
    color: #637879;
    font-size: 13px;
}}

@media (max-width: 700px) {{
    .article {{
        padding: 25px;
    }}

    nav {{
        display: none;
    }}
}}
</style>
</head>

<body>

<header>
<div class="nav">
<div class="logo">Stronger<span>Years</span></div>

<nav>
<a href="../index.html">Home</a>
<a href="../articles.html">Articles</a>
</nav>
</div>
</header>

<section class="hero">
<div class="hero-inner">
<div style="text-transform:uppercase;letter-spacing:2px;font-size:13px;">
Healthy Aging • Active Living
</div>

<h1>{html.escape(page_title)}</h1>

<p>
Practical, easy-to-understand information to help you make
better decisions about an active and healthy lifestyle.
</p>
</div>
</section>

<main class="container">

<article class="article">

{article_html}

<div class="recommend">

<h2>Recommended Option</h2>

<p>
If you are considering an amino-acid formula as part of your
nutrition routine, you can learn more about Advanced Amino Formula
from Advanced Bionutritionals.
</p>

<a class="cta"
href="{AFFILIATE_LINK}"
rel="nofollow sponsored noopener"
target="_blank">
Learn More
</a>

</div>

<div class="disclosure">

<strong>Affiliate Disclosure</strong>

<p>
I may earn a commission if you buy through links on this page,
at no extra cost to you.
</p>

</div>

</article>

</main>

<footer>
© 2026 StrongerYears. Information provided for educational purposes
and is not medical advice.
</footer>

</body>
</html>
"""

with open(filename, "w", encoding="utf-8") as f:
    f.write(html_page)

print(f"Professional article page created: {filename}")
