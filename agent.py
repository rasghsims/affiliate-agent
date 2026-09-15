import os
import requests
from datetime import datetime

API_KEY = os.environ["OPENROUTER_API_KEY"]

PROMPT = """
You are an ethical affiliate content strategist targeting US buyers.

Affiliate product:
Advanced Amino Formula by Advanced Bionutritionals

Affiliate link:
https://www.advancedbionutritionals.com/DS24/Advanced-Amino/Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld

Audience:
US adults interested in healthy aging, maintaining muscle, strength,
recovery, energy and active living.

Goal:
Create ONE genuinely useful, original article with strong buyer intent.

Rules:
- Do not make disease treatment or cure claims.
- Do not promise guaranteed results.
- Do not invent studies, reviews, testimonials or statistics.
- Do not pretend to be a doctor.
- Do not use the product or brand name in the SEO title.
- Provide useful information, not keyword stuffing.
- Naturally explain when an amino-acid supplement may be worth considering.
- Include a natural product recommendation section.
- Use the affiliate link only as the CTA.
- Include this exact disclosure:
  "I may earn a commission if you buy through links on this page,
  at no extra cost to you."

Return ONLY the article in Markdown.

Structure:
# SEO Title

## Introduction

## Main useful sections

## What to consider before choosing a supplement

## Recommended option

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

article = response.json()["choices"][0]["message"]["content"]

# Add affiliate CTA
article += """

## Learn More

If you want to learn more about the recommended amino-acid formula,
you can check the official product page here:

[Learn more about the formula](https://www.advancedbionutritionals.com/DS24/Advanced-Amino/Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld)

**Affiliate disclosure:** I may earn a commission if you buy through links
on this page, at no extra cost to you.
"""

os.makedirs("content", exist_ok=True)

filename = f"content/article-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(article)

print(f"Article created: {filename}")
