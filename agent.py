import os
import requests
from datetime import datetime

API_KEY = os.environ["OPENROUTER_API_KEY"]

prompt = """
You are an ethical affiliate marketing content planner.

Product:
Advanced Amino Formula by Advanced Bionutritionals

Affiliate link:
https://www.advancedbionutritionals.com/DS24/Advanced-Amino/Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld

Target audience:
US adults interested in healthy aging, maintaining muscle, strength, recovery and energy.

Create ONE useful, original article topic with strong buyer intent.

Rules:
- Do not make disease treatment or cure claims.
- Do not make guaranteed results claims.
- Do not invent reviews, testimonials or scientific studies.
- Do not use the product/brand name in the title.
- Give genuinely useful information, not spam.
- Include a natural place where the affiliate product can be mentioned.
- Include this disclosure:
  "I may earn a commission if you buy through links on this page, at no extra cost to you."

Return:
1. SEO title
2. Search intent
3. Short article outline
4. Full article around 700-900 words
5. Suggested affiliate CTA
6. Affiliate disclosure
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
                "content": prompt
            }
        ],
    },
    timeout=120,
)

response.raise_for_status()

content = response.json()["choices"][0]["message"]["content"]

filename = f"content-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.md"

with open(filename, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Created: {filename}")
print(content)
