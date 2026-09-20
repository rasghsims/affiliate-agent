import os
import re
import time
import html
import json
import requests
from pathlib import Path
from datetime import datetime, timezone

# =========================================================
# SETTINGS
# =========================================================
API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL = "openrouter/free"
SITE_NAME = "StrongerYears"
SITE_URL = "https://rasghsims.github.io/affiliate-agent"
CONTENT_DIR = "content"
PINTEREST_DIR = os.path.join(CONTENT_DIR, "pinterest")
PINTEREST_BOARD = "Healthy Aging & Strength"
PINTEREST_SIZE = (1000, 1500)

AFFILIATE_LINK = "https://www.advancedbionutritionals.com/DS24/Advanced-Amino/Muscle-Mass-Loss/HD.htm#aff=Healthy_w0rld"
DISCLOSURE = "I may earn a commission if you buy through links on this page, at no extra cost to you."

HERO_IMAGE = "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=2200&q=85"
CARD_IMAGES = [
    "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1200&q=82",
]

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
# AI
# =========================================================
def ask_ai(prompt, temperature=0.65):
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
                    "You write trustworthy, original wellness education for US adults 50+. "
                    "Never invent studies, statistics, doctors, testimonials, reviews or guarantees. "
                    "Do not diagnose, treat, cure, prevent or reverse disease. Avoid fear, fake urgency, "
                    "miracle language and unsupported medical claims. Give practical, useful information."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }
    last_error = None
    for attempt in range(4):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=90)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as exc:
            last_error = exc
            print(f"AI request failed ({attempt + 1}/4): {exc}")
            if attempt < 3:
                time.sleep(5 * (attempt + 1))
    raise last_error

# =========================================================
# HELPERS
# =========================================================
def clean(text):
    return re.sub(r"```(?:json|markdown|html)?|```", "", text, flags=re.I).strip()


def slugify(text):
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return re.sub(r"-+", "-", text).strip("-")[:80]


def existing_articles():
    items = []
    os.makedirs(CONTENT_DIR, exist_ok=True)
    for name in os.listdir(CONTENT_DIR):
        if not name.endswith(".html"):
            continue
        path = os.path.join(CONTENT_DIR, name)
        try:
            data = open(path, encoding="utf-8").read()
            m = re.search(r"<title>(.*?)</title>", data, re.I | re.S)
            if m:
                title = re.sub(r"\s+", " ", html.unescape(m.group(1))).strip()
                title = re.sub(r"\s*\|\s*" + re.escape(SITE_NAME) + r"$", "", title, flags=re.I)
                items.append((title, name))
        except Exception:
            pass
    return sorted(items, key=lambda x: x[1], reverse=True)


def markdown_to_html(text):
    out, para, in_list = [], [], False

    def flush():
        nonlocal para
        if para:
            joined = " ".join(x.strip() for x in para).strip()
            if joined:
                out.append(f"<p>{html.escape(joined)}</p>")
            para = []

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            flush(); continue
        if s.startswith("### "):
            flush(); close_list(); out.append(f"<h3>{html.escape(s[4:])}</h3>"); continue
        if s.startswith("## "):
            flush(); close_list(); out.append(f"<h2>{html.escape(s[3:])}</h2>"); continue
        if s.startswith("# "):
            flush(); close_list(); continue
        if re.match(r"^[-*]\s+", s):
            flush()
            if not in_list:
                out.append("<ul>"); in_list = True
            item = re.sub(r"^[-*]\s+", "", s)
            out.append(f"<li>{html.escape(item)}</li>")
            continue
        close_list(); para.append(s)
    flush(); close_list()
    return "\n".join(out)


def extract_json(raw):
    raw = clean(raw)
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.S)
        if m:
            return json.loads(m.group(0))
        raise ValueError("AI did not return valid JSON")

# =========================================================
# ARTICLE GENERATION
# =========================================================
def generate_article(topic, old_titles):
    prompt = f"""
Create a genuinely useful, original SEO article for this topic:
{topic}

Audience: adults 50+ in the United States interested in healthy aging, strength,
mobility, recovery and nutrition.

Return ONLY valid JSON with these keys:
"title": a compelling natural title (not clickbait),
"description": an accurate meta description under 155 characters,
"keyword": one primary search phrase,
"body": markdown article.

Article requirements:
- 1200-1600 words.
- Strong opening that answers the reader's intent quickly.
- Use H2/H3 headings, short paragraphs and a practical checklist.
- Explain the role of exercise, adequate nutrition, protein/amino acids and recovery carefully.
- Supplements must be presented as optional, not replacements for balanced nutrition.
- No disease treatment/cure/prevention claims.
- No invented studies, statistics, experts, testimonials or reviews.
- No guaranteed outcomes, miracle language, fake scarcity or fear marketing.
- End with a natural optional section for readers who want to learn more about amino-acid nutrition.

Avoid titles substantially similar to these existing titles:
{old_titles[:40]}
"""
    data = extract_json(ask_ai(prompt))
    title = str(data.get("title", topic)).strip()
    desc = str(data.get("description", "Practical guidance for strength, mobility, recovery and healthy aging.")).strip()
    keyword = str(data.get("keyword", "healthy aging muscle strength")).strip()
    body = str(data.get("body", "")).strip()
    if not body:
        raise ValueError("AI returned an empty article")
    return title, desc[:155], keyword, body

# =========================================================
# PINTEREST ASSET GENERATION
# =========================================================
def pinterest_copy(title, description, keyword):
    pin_title = title.strip()[:100]
    pin_description = re.sub(r"\s+", " ", f"{description.strip()} Explore practical ideas for strength, recovery and healthy aging. Read the full guide at StrongerYears.").strip()[:500]
    return pin_title, pin_description

def _wrap_text(draw, text, font, max_width):
    words=text.split(); lines=[]; current=""
    for word in words:
        test=word if not current else current+" "+word
        if draw.textbbox((0,0),test,font=font)[2] <= max_width: current=test
        else:
            if current: lines.append(current)
            current=word
    if current: lines.append(current)
    return lines

def create_pinterest_pin(title, description, keyword, slug):
    from PIL import Image, ImageDraw, ImageFont
    Path(PINTEREST_DIR).mkdir(parents=True, exist_ok=True)
    image_path=Path(PINTEREST_DIR)/f"{slug}.png"; json_path=Path(PINTEREST_DIR)/f"{slug}.json"
    pin_title,pin_description=pinterest_copy(title,description,keyword)
    W,H=PINTEREST_SIZE; img=Image.new("RGB",(W,H),"#0b1715"); draw=ImageDraw.Draw(img)
    for y in range(H):
        t=y/H; draw.line([(0,y),(W,y)],fill=(int(8+10*t),int(25+42*t),int(20+20*t)))
    draw.ellipse((620,-160,1160,380),fill="#17382c"); draw.ellipse((-180,1060,420,1660),fill="#132b23"); draw.ellipse((720,1030,1110,1420),outline="#b7f36b",width=4)
    bp="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"; rp="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    def font(size,bold=False):
        path=bp if bold else rp
        return ImageFont.truetype(path,size) if os.path.exists(path) else ImageFont.load_default()
    brand=font(42,True); eyebrow=font(24,True); titlef=font(68,True); body=font(29); tip=font(27,True); small=font(22)
    draw.text((75,70),"StrongerYears",font=brand,fill="#b7f36b"); draw.text((75,145),"HEALTHY AGING • STRENGTH • VITALITY",font=eyebrow,fill="#d8e6df")
    y=230
    for line in _wrap_text(draw,pin_title,titlef,850)[:5]: draw.text((75,y),line,font=titlef,fill="#ffffff"); y+=78
    tips=["Stay active","Eat enough protein","Prioritize recovery","Keep the routine simple"]; y=780
    for i,t in enumerate(tips,1):
        draw.rounded_rectangle((75,y,925,y+105),radius=24,fill="#f4f3ed"); draw.ellipse((100,y+28,148,y+76),fill="#b7f36b"); draw.text((116,y+34),str(i),font=small,fill="#10201b"); draw.text((180,y+31),t,font=tip,fill="#10201b"); y+=125
    draw.text((75,1320),"Read the full guide →",font=font(34,True),fill="#b7f36b"); draw.text((75,1390),"Practical ideas for staying strong as you age.",font=body,fill="#d8e6df")
    img.save(image_path,"PNG",optimize=True)
    metadata={"title":pin_title,"description":pin_description,"url":f"{SITE_URL}/content/{slug}.html","board":PINTEREST_BOARD,"image":str(image_path).replace("\\","/"),"format":"PNG","width":W,"height":H,"created_at":datetime.now(timezone.utc).isoformat()}
    json_path.write_text(json.dumps(metadata,indent=2),encoding="utf-8"); print("Pinterest Pin created:",image_path); print("Pinterest metadata created:",json_path); return image_path,json_path

def build_pinterest_index():
    Path(PINTEREST_DIR).mkdir(parents=True,exist_ok=True); items=[]
    for meta_file in sorted(Path(PINTEREST_DIR).glob("*.json"),reverse=True):
        try: items.append(json.loads(meta_file.read_text(encoding="utf-8")))
        except Exception: pass
    Path(PINTEREST_DIR,"index.json").write_text(json.dumps(items[:100],indent=2),encoding="utf-8"); print("Pinterest queue updated:",len(items),"assets")

# =========================================================
# PAGE BUILDERS
# =========================================================
def article_html(title, description, keyword, body_html, related):
    safe_title = html.escape(title)
    safe_desc = html.escape(description, quote=True)
    slug = slugify(title)
    canonical = f"{SITE_URL}/content/{slug}.html"
    related_html = "".join(
        f'<a class="related" href="{html.escape(name)}"><span>READ NEXT</span><b>{html.escape(t)}</b><em>→</em></a>'
        for t, name in related[:3]
    )
    return f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title} | {SITE_NAME}</title>
<meta name="description" content="{safe_desc}">
<meta name="keywords" content="{html.escape(keyword, quote=True)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{safe_title}"><meta property="og:description" content="{safe_desc}">
<meta property="og:type" content="article"><meta property="og:url" content="{canonical}">
<style>
*{{{{box-sizing:border-box}}}}html{{{{scroll-behavior:smooth}}}}body{{{{margin:0;background:#f4f3ed;color:#10201b;font-family:Arial,Helvetica,sans-serif;line-height:1.75}}}}nav{{{{padding:24px 7%;display:flex;justify-content:space-between;background:#0b1715;color:#fff;position:relative;z-index:2}}}}.logo{{{{font-size:21px;font-weight:800;letter-spacing:-1px}}}}.logo span{{{{color:#b7f36b}}}}nav a{{{{color:#fff;text-decoration:none;font-size:13px}}}}.hero{{{{min-height:500px;position:relative;display:flex;align-items:end;overflow:hidden;color:#fff;background:#10201b}}}}.hero img{{{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}}}.shade{{{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,18,14,.9),rgba(5,18,14,.18)),linear-gradient(0deg,rgba(5,18,14,.7),transparent)}}}}.hero-content{{{{position:relative;z-index:1;max-width:1100px;width:100%;margin:auto;padding:80px 7%}}}}.eyebrow{{{{color:#b7f36b;text-transform:uppercase;letter-spacing:3px;font-size:11px;font-weight:800}}}}h1{{{{max-width:900px;font-size:clamp(44px,7vw,82px);line-height:.97;letter-spacing:-4px;margin:18px 0}}}}.article{{{{max-width:820px;margin:auto;padding:75px 7% 90px}}}}.article p{{{{font-size:18px}}}}.article h2{{{{margin-top:58px;font-size:34px;line-height:1.1;letter-spacing:-1px}}}}.article h3{{{{margin-top:34px;font-size:23px}}}}.article li{{{{margin:10px 0}}}}.cta{{{{margin-top:70px;padding:44px;border-radius:28px;background:#0b1715;color:#fff}}}}.cta h2{{{{margin-top:0;font-size:34px}}}}.cta p{{{{color:rgba(255,255,255,.72)}}}}.button{{{{display:inline-block;margin-top:14px;padding:15px 23px;border-radius:999px;background:#b7f36b;color:#10201b;text-decoration:none;font-weight:800}}}}.disclosure{{{{margin-top:20px;font-size:11px;opacity:.5}}}}.related-wrap{{{{margin-top:70px}}}}.related{{{{display:grid;grid-template-columns:100px 1fr 30px;gap:18px;align-items:center;padding:22px 0;border-top:1px solid #d5d6ce;text-decoration:none}}}}.related span{{{{font-size:10px;font-weight:800;letter-spacing:2px;color:#68736e}}}}.related b{{{{font-size:18px}}}}.related em{{{{font-style:normal;font-size:24px}}}}footer{{{{padding:45px 7%;text-align:center;background:#07110f;color:#fff;font-size:12px}}}}@media(max-width:650px){{{{h1{{{{letter-spacing:-2px}}}}.article{{{{padding-top:50px}}}}.cta{{{{padding:30px 24px}}}}.related{{{{grid-template-columns:1fr 25px}}.related span{{{{display:none}}}}}}
</style></head><body>
<nav><div class="logo">Stronger<span>Years</span></div><a href="../index.html">Home</a></nav>
<header class="hero"><img src="{HERO_IMAGE}" alt="Active older adult outdoors"><div class="shade"></div><div class="hero-content"><div class="eyebrow">Strength · Vitality · Healthy aging</div><h1>{safe_title}</h1></div></header>
<main class="article"><div>{body_html}</div>
<section class="cta"><h2>Want to explore the nutrition side?</h2><p>Amino acids are one part of the broader nutrition conversation around maintaining muscle and supporting an active lifestyle.</p><a class="button" href="{AFFILIATE_LINK}" target="_blank" rel="nofollow sponsored">Explore the Formula →</a><div class="disclosure">{DISCLOSURE}</div></section>
<div class="related-wrap"><h2>More from StrongerYears</h2>{related_html}</div></main>
<footer>© {datetime.now().year} {SITE_NAME}</footer></body></html>'''


def build_homepage(articles):
    cards = []
    for i, (title, name) in enumerate(articles[:8]):
        img = CARD_IMAGES[i % len(CARD_IMAGES)]
        cards.append(f'''<a class="card" href="content/{html.escape(name)}"><div class="pic"><img src="{img}" alt="{html.escape(title)}" loading="lazy"></div><div class="cardbody"><small>GUIDE</small><h3>{html.escape(title)}</h3><span>Read guide →</span></div></a>''')
    cards_html = "".join(cards)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{SITE_NAME} — Age well. Live strong.</title><meta name="description" content="Practical guides for strength, mobility, recovery, nutrition and healthy aging."><link rel="canonical" href="{SITE_URL}/"><meta property="og:title" content="{SITE_NAME} — Age well. Live strong."><meta property="og:description" content="Practical guides for strength, mobility, recovery, nutrition and healthy aging."><meta property="og:type" content="website"><style>
*{{{{box-sizing:border-box}}}}body{{{{margin:0;background:#f4f3ed;color:#10201b;font-family:Arial,Helvetica,sans-serif}}}}.nav{{{{position:absolute;z-index:3;width:100%;padding:25px 6%;display:flex;justify-content:space-between;color:#fff}}.logo{{{{font-size:22px;font-weight:800;letter-spacing:-1px}}}}.logo span{{{{color:#b7f36b}}}}.nav a{{{{color:#fff;text-decoration:none;font-size:13px}}}}.hero{{{{height:92vh;min-height:620px;position:relative;display:flex;align-items:center;overflow:hidden;color:#fff}}}}.hero>img{{{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;animation:zoom 12s ease-out forwards}}}}.shade{{{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(5,18,14,.92),rgba(5,18,14,.18) 78%),linear-gradient(0deg,rgba(5,18,14,.55),transparent 55%)}}}}.hero-content{{{{position:relative;z-index:1;max-width:1150px;width:100%;margin:auto;padding:100px 6%}}}}.eyebrow{{{{color:#b7f36b;text-transform:uppercase;letter-spacing:4px;font-size:11px;font-weight:800}}}}h1{{{{font-size:clamp(58px,9vw,122px);line-height:.86;letter-spacing:-6px;max-width:950px;margin:20px 0}}}}.lead{{{{max-width:580px;font-size:19px;line-height:1.6;color:rgba(255,255,255,.78)}}}}.button{{{{display:inline-block;margin-top:24px;padding:16px 25px;border-radius:999px;background:#b7f36b;color:#10201b;text-decoration:none;font-weight:800}}}}section{{{{max-width:1200px;margin:auto;padding:100px 6%}}}}.intro{{{{display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:end}}}}.intro h2{{{{font-size:clamp(42px,5vw,70px);line-height:.95;letter-spacing:-3px;margin:0}}.intro p{{{{font-size:18px;line-height:1.7;color:#66716c}}}}.grid{{{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}}}.card{{{{background:#fff;border-radius:28px;overflow:hidden;text-decoration:none;color:inherit;transition:transform .25s ease,box-shadow .25s ease}}}}.card:hover{{{{transform:translateY(-6px);box-shadow:0 20px 50px rgba(0,0,0,.10)}}}}.pic{{{{height:330px;overflow:hidden}}}}.pic img{{{{width:100%;height:100%;object-fit:cover;transition:transform .6s ease}}}}.card:hover img{{{{transform:scale(1.05)}}}}.cardbody{{{{padding:28px}}}}.cardbody small{{{{font-size:10px;letter-spacing:3px;font-weight:800;color:#718079}}}}.cardbody h3{{{{font-size:28px;line-height:1.1;letter-spacing:-1px;margin:13px 0 25px}}}}.cardbody span{{{{font-size:13px;font-weight:800}}}}.dark{{{{max-width:none;background:#0b1715;color:#fff}}}}.darkinner{{{{max-width:1200px;margin:auto;padding:110px 6%;display:grid;grid-template-columns:1fr 1fr;gap:70px;align-items:center}}}}.dark h2{{{{font-size:clamp(45px,6vw,80px);line-height:.9;letter-spacing:-4px;margin:0}}.dark p{{{{color:rgba(255,255,255,.68);font-size:18px;line-height:1.7}}}}.disclosure{{{{font-size:11px;opacity:.5;margin-top:18px}}}}footer{{{{padding:50px 6%;background:#07110f;color:#fff;text-align:center;font-size:12px}}}}@keyframes zoom{{{{from{{{{transform:scale(1.06)}}}}to{{{{transform:scale(1)}}}}}}@media(max-width:750px){{{{.intro,.darkinner,.grid{{{{grid-template-columns:1fr}}}}h1{{{{letter-spacing:-3px}}}}.pic{{{{height:260px}}}}section{{{{padding:70px 6%}}}}}}
</style></head><body><nav class="nav"><div class="logo">Stronger<span>Years</span></div><a href="#guides">Guides</a></nav><header class="hero"><img src="{HERO_IMAGE}" alt="Active older adult outdoors"><div class="shade"></div><div class="hero-content"><div class="eyebrow">A better way to age</div><h1>Age well.<br>Live strong.</h1><p class="lead">Clear, practical ideas for strength, mobility, recovery and nutrition — without the hype.</p><a class="button" href="#guides">Explore the guides ↓</a></div></header><section><div class="intro"><h2>Strength is something you can keep building.</h2><p>Getting older does not mean giving up an active life. The basics still matter: regular movement, useful nutrition, recovery and habits you can actually repeat. StrongerYears turns those ideas into simple, readable guides.</p></div></section><section id="guides"><div class="grid">{cards_html}</div></section><div class="dark"><div class="darkinner"><h2>Make your everyday habits work harder.</h2><div><p>Explore practical nutrition ideas, including the role amino acids can play alongside a balanced diet and an active lifestyle.</p><a class="button" href="{AFFILIATE_LINK}" target="_blank" rel="nofollow sponsored">Explore the Formula →</a><div class="disclosure">{DISCLOSURE}</div></div></div></div><footer>© {datetime.now().year} {SITE_NAME}</footer></body></html>'''

# =========================================================
# SITEMAP
# =========================================================
def build_sitemap(articles):
    today = datetime.now(timezone.utc).date().isoformat()
    urls = [f"{SITE_URL}/"] + [f"{SITE_URL}/content/{name}" for _, name in articles]
    body = "\n".join(f"<url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n'''
    open("sitemap.xml", "w", encoding="utf-8").write(xml)
    print(f"Sitemap updated: {len(urls)} URLs")

# =========================================================
# MAIN
# =========================================================
def main():
    os.makedirs(CONTENT_DIR, exist_ok=True)
    current = existing_articles()
    old_titles = [t.lower() for t, _ in current]
    print("Existing articles:", len(current))

    topic = TOPICS[len(current) % len(TOPICS)]
    for offset in range(len(TOPICS)):
        candidate = TOPICS[(len(current) + offset) % len(TOPICS)]
        try:
            title, desc, keyword, body = generate_article(candidate, old_titles)
            if title.lower() in old_titles:
                print("Duplicate title returned; trying another topic")
                continue
            slug = slugify(title)
            filename = f"{slug}.html"
            related = current[:3]
            page = article_html(title, desc, keyword, markdown_to_html(body), related)
            with open(os.path.join(CONTENT_DIR, filename), "w", encoding="utf-8") as f:
                f.write(page)
            create_pinterest_pin(title, desc, keyword, slug)
            build_pinterest_index()
            print("Generated article:", title)
            print("Pinterest-ready Pin:", f"{PINTEREST_DIR}/{slug}.png")
            print("Pinterest destination:", f"{SITE_URL}/content/{slug}.html")
            break
        except Exception as exc:
            print("Generation failed:", exc)
    else:
        print("No new article generated.")

    build_pinterest_index()
    current = existing_articles()
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(build_homepage(current))
    build_sitemap(current)
    print("Homepage updated.")
    print("Agent finished successfully.")


if __name__ == "__main__":
    main()
