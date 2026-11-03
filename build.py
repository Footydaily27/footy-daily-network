#!/usr/bin/env python3
"""Build the Footy Daily Network static site.

Content lives in content/ (edited through the /admin editor):
  content/stories/*.md   one file per story (front matter + text)
  content/photos.yml     the Photos page gallery
  content/founders.yml   founders section

Run:  pip install -r requirements.txt && python3 build.py
"""
import json, os, html, re, datetime, shutil, hashlib, glob
import yaml, markdown
from PIL import Image, ImageOps
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE_URL = 'https://footydailynetwork.com'
NAME = 'Footy Daily Network'
TAGLINE = 'Captured Moments: The Game Beyond the Scoreline'
EMAIL = 'footydailynetwork@gmail.com'
PHONES = ['678-793-4952', '404-308-6239']

LOGO = '2025/08/footydaily-network-1.jpg'

def as_list(v):
    if not v: return []
    return [v] if isinstance(v, str) else [x for x in v if x]

def load_md(path):
    raw = open(path, encoding='utf-8').read()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', raw, re.S)
    fm, body = (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, raw)
    return fm, body

def load_stories():
    out = []
    for f in glob.glob(os.path.join(ROOT, 'content', 'stories', '*.md')):
        fm, body = load_md(f)
        if fm.get('draft'): continue
        body_html = markdown.markdown(body, extensions=['extra', 'sane_lists'])
        text = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', body_html))).strip()
        excerpt = (fm.get('excerpt') or '').strip() or (text[:200].rsplit(' ', 1)[0] + '…' if len(text) > 200 else text)
        gallery = [{'src': g, 'alt': ''} for g in as_list(fm.get('gallery'))]
        inline = re.findall(r'<img[^>]+src="([^"]+)"', body_html)
        cover = fm.get('cover') or (gallery[0]['src'] if gallery else (inline[0] if inline else '/assets/img/' + LOGO))
        d = fm.get('date')
        d = d.isoformat()[:10] if hasattr(d, 'isoformat') else str(d)[:10]
        out.append({
            'slug': os.path.splitext(os.path.basename(f))[0], 'title': str(fm.get('title', 'Untitled')),
            'date': d, 'league': fm.get('league') or 'MLS', 'author': fm.get('author') or NAME,
            'tags': as_list(fm.get('tags')), 'cover': cover, 'excerpt': excerpt, 'words': len(text.split()),
            'body': body_html, 'gallery': gallery, 'n_inline': len(inline), 'old_link': fm.get('old_url') or '',
        })
    return out

stories = sorted(load_stories(), key=lambda s: s['date'], reverse=True)
PHOTOS = [{'src': p} for p in as_list((yaml.safe_load(open(os.path.join(ROOT, 'content', 'photos.yml'))) or {}).get('photos'))]
FOUNDERS = (yaml.safe_load(open(os.path.join(ROOT, 'content', 'founders.yml'))) or {}).get('founders', [])
VER = lambda f: hashlib.md5(open(os.path.join(ROOT, f), 'rb').read()).hexdigest()[:8]
esc = lambda s: html.escape(s or '', quote=True)

def _rel(p):
    """'/assets/img/x/y.jpg' or 'x/y.jpg' -> 'x/y.jpg' (path inside assets/img)."""
    p = (p or '').split('?')[0]
    return p[len('/assets/img/'):] if p.startswith('/assets/img/') else p.lstrip('/')

def _resized(rel, folder, size, quality):
    """Make (once) a resized JPEG copy of assets/img/<rel> in assets/<folder>/. Returns public path or None."""
    src = os.path.join(ROOT, 'assets', 'img', rel)
    out_rel = re.sub(r'\.[A-Za-z0-9]+$', '.jpg', rel)
    out = os.path.join(ROOT, 'assets', folder, out_rel)
    if not os.path.exists(out):
        if not os.path.exists(src): return None
        try:
            im = ImageOps.exif_transpose(Image.open(src)).convert('RGB')
            if max(im.size) <= size and folder == 'large': return None
            im.thumbnail((size, size))
            os.makedirs(os.path.dirname(out), exist_ok=True)
            im.save(out, 'JPEG', quality=quality, optimize=True, progressive=True)
        except Exception as e:
            print('  ! could not resize', rel, e); return None
    return f'/assets/{folder}/{out_rel}'

def img(p):
    """Full-size image for heroes and the lightbox (new uploads get an optimized 1800px copy)."""
    rel = _rel(p)
    if not rel.startswith('uploads/'): return f'/assets/img/{rel}'
    return _resized(rel, 'large', 1800, 82) or f'/assets/img/{rel}'

def thumb(p):
    rel = _rel(p)
    return _resized(rel, 'thumb', 760, 72) or img(p)

def fdate(d):
    return datetime.date.fromisoformat(d).strftime('%b %-d, %Y')

def photos_in(s):
    return len(s['gallery']) + s['n_inline']

def read_time(s):
    return max(1, round(s['words'] / 220))

LEAGUE_ORDER = ['MLS', 'MLS NEXT Pro', 'NWSL', 'USL', 'U.S. Open Cup', 'Concacaf', 'UPSL', 'College', 'High School', 'Youth', 'Features']
counts = Counter(s['league'] for s in stories)
leagues = [l for l in LEAGUE_ORDER if counts[l]] + [l for l in counts if l not in LEAGUE_ORDER]
lslug = lambda l: re.sub(r'[^a-z0-9]+', '-', l.lower()).strip('-')

BALL = '''<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="14.5" fill="#fff" stroke="#0b0b0c" stroke-width="2"/><path fill="#0b0b0c" d="M16 9.2l5 3.6-1.9 5.9h-6.2L11 12.8zM16 2.5v6.7M21 12.8l6.6-2.2M19.1 18.7l4 5.4M12.9 18.7l-4 5.4M11 12.8L4.4 10.6" stroke="#0b0b0c" stroke-width="1.6"/></svg>'''
BRAND = f'<a class="brand" href="/" aria-label="{NAME} home"><span class="brand-name">Footy<b>Daily</b><small>Network</small></span></a>'
NAV = [('/', 'Home'), ('/stories/', 'Stories'), ('/photos/', 'Photos'), ('/team/', 'Founders'), ('/about/', 'About')]

def head(title, desc, path, image=None):
    full = f'{title} | {NAME}' if title != NAME else f'{NAME} — {TAGLINE}'
    ogimg = SITE_URL + (image or img(LOGO))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE_URL}{path}">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{ogimg}">
<meta property="og:url" content="{SITE_URL}{path}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b0b0c">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/style.css?v={VER('assets/css/style.css')}">
</head>
<body>'''

def header(active):
    links = ''.join(f'<a href="{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    tick = ''.join(f'<a href="/stories/{s["slug"]}/">{esc(s["title"])}</a>' for s in stories[:10])
    return f'''
<header class="site-header">
  <div class="wrap">
    {BRAND}
    <nav class="nav" aria-label="Main">{links}<a href="/contact/">Contact</a></nav>
    <button class="menu-btn" aria-label="Open menu" aria-expanded="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg></button>
  </div>
</header>
<div class="ticker" aria-label="Latest stories"><div class="ticker-inner"><span class="ticker-label">Latest</span><div class="ticker-track">{tick}{tick}</div></div></div>
<main>'''

def footer():
    lg = ''.join(f'<li><a href="/stories/?league={esc(l)}">{esc(l)}</a></li>' for l in leagues[:7])
    return f'''
</main>
<footer class="site-footer">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        {BRAND}
        <p>{TAGLINE}. Match reports, photography and stories from grassroots to the pros.</p>
      </div>
      <div><h4>Coverage</h4><ul>{lg}</ul></div>
      <div><h4>Get in touch</h4><ul>
        <li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
        {''.join(f'<li><a href="tel:{p.replace("-", "")}">{p}</a></li>' for p in PHONES)}
        <li><a href="/contact/">Contact us →</a></li>
      </ul></div>
    </div>
    <div class="foot-bottom"><span>© {datetime.date.today().year} {NAME}. All photos © their photographers.</span><span><a href="/stories/">Stories</a> · <a href="/photos/">Photos</a> · <a href="/team/">Founders</a> · <a href="/about/">About</a> · <a href="/contact/">Contact</a></span></div>
  </div>
</footer>
<script src="/assets/js/main.js?v={VER('assets/js/main.js')}" defer></script>
</body>
</html>'''

CAM = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 7h3l2-3h6l2 3h3v13H4z"/><circle cx="12" cy="13" r="4"/></svg>'

def card(s, eager=False):
    text = esc(f"{s['title']} {s['league']} {s['excerpt']} {' '.join(s['tags'])}".lower())
    return f'''<a class="card" href="/stories/{s['slug']}/" data-league="{esc(s['league'])}" data-text="{text}">
  <div class="card-img"><img src="{thumb(s['cover'])}" alt="" loading="{'eager' if eager else 'lazy'}"><span class="pill">{esc(s['league'])}</span><span class="count">{CAM}{photos_in(s)}</span></div>
  <div class="meta"><span>{fdate(s['date'])}</span><span>{read_time(s)} min read</span></div>
  <h3>{esc(s['title'])}</h3>
  <p>{esc(s['excerpt'])}</p>
</a>'''

def filters(with_search=True):
    chips = f'<button class="chip" data-filter="all" aria-pressed="true">All<span class="n">{len(stories)}</span></button>'
    chips += ''.join(f'<button class="chip" data-filter="{esc(l)}">{esc(l)}<span class="n">{counts[l]}</span></button>' for l in leagues)
    srch = '<input class="search" type="search" placeholder="Search teams, players…" aria-label="Search stories" data-search>' if with_search else ''
    return f'<div class="filters">{chips}{srch}</div>'

def write(path, content):
    out = os.path.join(ROOT, path.strip('/'), 'index.html') if path != '/' else os.path.join(ROOT, 'index.html')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, 'w').write(content)

# ---------------- Home ----------------
lead, side = stories[0], stories[1:3]
side_html = ''.join(f'''<a href="/stories/{s['slug']}/"><img src="{thumb(s['cover'])}" alt=""><div class="hero-copy"><span class="pill">{esc(s['league'])}</span><h2>{esc(s['title'])}</h2></div></a>''' for s in side)
strip = ''.join(f'<a href="{img(g["src"])}" data-lightbox="home"><img src="{thumb(g["src"])}" alt="Matchday photo" loading="lazy"></a>' for g in PHOTOS[:12])
def founder_card(f):
    return f'''<article class="founder">
  <a class="founder-img" href="https://www.instagram.com/{f['handle']}/" target="_blank" rel="noopener"><img src="{thumb(f['photo'])}" alt="{esc(f['name'])}" loading="lazy"></a>
  <div class="founder-copy">
    <span class="pill">{esc(f.get('role') or 'Co-Founder')}</span>
    <h3>{esc(f['name'])}</h3>
    {''.join(f'<p>{esc(x.strip())}</p>' for x in str(f.get('bio', '')).split(chr(10)*2) if x.strip())}
    <a class="link-arrow" href="https://www.instagram.com/{f['handle']}/" target="_blank" rel="noopener">@{f['handle']} on Instagram</a>
  </div>
</article>'''
founders_html = ''.join(founder_card(f) for f in FOUNDERS)
total_photos = sum(photos_in(s) for s in stories)
home = head(NAME, f'{TAGLINE}. Match reports and photography from MLS, NWSL, USL, MLS NEXT Pro, UPSL, college and youth soccer.', '/') + header('/') + f'''
<section class="hero">
  <div class="wrap hero-grid">
    <a class="hero-main" href="/stories/{lead['slug']}/">
      <img src="{img(lead['cover'])}" alt="" fetchpriority="high">
      <div class="hero-copy">
        <span class="pill">Latest · {esc(lead['league'])}</span>
        <h1>{esc(lead['title'])}</h1>
        <p>{esc(lead['excerpt'])}</p>
        <div class="meta"><span>{fdate(lead['date'])}</span><span>By {esc(lead['author'])}</span><span>{photos_in(lead)} photos</span></div>
      </div>
    </a>
    <div class="hero-side">{side_html}</div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><div><h2>From the Pitch</h2><p>Match reports, player features and stories from youth to professional soccer.</p></div><a class="link-arrow" href="/stories/">All {len(stories)} stories</a></div>
    {filters(with_search=False)}
    <div class="grid" data-story-list data-limit="9">{''.join(card(s) for s in stories[3:])}</div>
    <p class="empty" data-empty hidden>No stories in this category yet.</p>
  </div>
</section>

<section class="section dark">
  <div class="wrap">
    <div class="section-head"><div><h2>Through Our Lens</h2><p>Our latest matchday photography — the intensity, the passion and the moments that define the game.</p></div><a class="link-arrow" href="/photos/">See all photos</a></div>
    <div class="strip">{strip}</div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head"><div><h2>Meet the Founders</h2><p>The two storytellers who started Footy Daily Network.</p></div><a class="link-arrow" href="/team/">Our story</a></div>
    <div class="founders">{founders_html}</div>
  </div>
</section>

<section class="cta">
  <div class="wrap">
    <div><h2>Want your match covered?</h2><p>Clubs, academies and leagues — book Footy Daily Network for photography, video and match reports.</p></div>
    <a class="btn" href="/contact/">Get in touch →</a>
  </div>
</section>''' + footer()
write('/', home)

# ---------------- Stories index ----------------
idx = head('Stories', 'Every match report and feature from Footy Daily Network.', '/stories/') + header('/stories/') + f'''
<section class="page-head"><div class="wrap"><div class="eyebrow">From the Pitch</div><h1>Stories</h1><p>{len(stories)} match reports and features, {total_photos:,} photos — from MLS and NWSL to UPSL, college, high school and academy soccer.</p></div></section>
<section class="section"><div class="wrap">
  {filters()}
  <div class="grid" data-story-list>{''.join(card(s, i < 6) for i, s in enumerate(stories))}</div>
  <p class="empty" data-empty hidden>No stories match that search.</p>
</div></section>''' + footer()
write('/stories/', idx)

# ---------------- Story pages ----------------
def render_body(s):
    """Markdown HTML -> article HTML: images become zoomable figures, links open in a new tab."""
    h = s['body']
    def fig(m):
        tag = m.group(1)
        src = re.search(r'src="([^"]+)"', tag).group(1)
        alt = (re.search(r'alt="([^"]*)"', tag) or [None, ''])[1]
        return f'<figure><a href="{img(src)}" data-lightbox="story"><img src="{img(src)}" alt="{alt}" loading="lazy"></a></figure>'
    h = re.sub(r'<p>\s*(<img[^>]+>)\s*</p>', fig, h)
    h = re.sub(r'<p><em>(.*?)</em></p>', r'<p class="caption">\1</p>', h)
    h = re.sub(r'<a href="(https?://[^"]+)"(?![^>]*target)', r'<a href="\1" target="_blank" rel="noopener"', h)
    return h, s['gallery']

for i, s in enumerate(stories):
    body, gallery = render_body(s)
    path = f'/stories/{s["slug"]}/'
    url = SITE_URL + path
    share_q = html.escape(f'{s["title"]} {url}')
    initials = ''.join(w[0] for w in s['author'].split()[:2]).upper() or 'F'
    gal_html = ''
    if gallery:
        tiles = ''.join(f'<a href="{img(g["src"])}" data-lightbox="story"><img src="{thumb(g["src"])}" alt="{esc(g["alt"]) or "Match photo"}" loading="lazy"></a>' for g in gallery)
        gal_html = f'''<section class="photo-gallery"><div class="wrap">
  <div class="section-head"><div><h2>Match Gallery</h2><p>{len(gallery)} photos · tap any photo to view full screen.</p></div></div>
  <div class="masonry">{tiles}</div></div></section>'''
    related = [x for x in stories if x['league'] == s['league'] and x is not s][:3]
    related += [x for x in stories if x is not s and x not in related][:3 - len(related)]
    page = head(s['title'], s['excerpt'], path, img(s['cover'])) + header('/stories/') + f'''
<section class="article-hero">
  <img src="{img(s['cover'])}" alt="" fetchpriority="high">
  <div class="wrap">
    <div class="crumbs"><a href="/stories/">Stories</a> / <a href="/stories/?league={esc(s['league'])}">{esc(s['league'])}</a></div>
    <h1>{esc(s['title'])}</h1>
    <div class="meta"><span>{fdate(s['date'])}</span><span>{read_time(s)} min read</span><span>{photos_in(s)} photos</span></div>
  </div>
</section>
<article class="article">
  <div class="byline"><span class="avatar">{esc(initials)}</span><div><strong>{esc(s['author'])}</strong><small>Footy Daily Network · {fdate(s['date'])}</small></div></div>
  {body}
  <div class="share"><span>Share</span>
    <a href="https://twitter.com/intent/tweet?text={share_q}" target="_blank" rel="noopener">X</a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={url}" target="_blank" rel="noopener">Facebook</a>
    <a href="https://wa.me/?text={share_q}" target="_blank" rel="noopener">WhatsApp</a>
    <button data-copy>Copy link</button>
  </div>
</article>
{gal_html}
<section class="section"><div class="wrap">
  <div class="section-head"><div><h2>More Stories</h2></div><a class="link-arrow" href="/stories/">All stories</a></div>
  <div class="grid">{''.join(card(r) for r in related)}</div>
</div></section>''' + footer()
    write(path, page)

# ---------------- Photos ----------------
pics = ''.join(f'<a href="{img(g["src"])}" data-lightbox="photos"><img src="{thumb(g["src"])}" alt="Matchday photo" loading="lazy"></a>' for g in PHOTOS)
write('/photos/', head('Photos', 'Matchday photography from Footy Daily Network.', '/photos/') + header('/photos/') + f'''
<section class="page-head"><div class="wrap"><div class="eyebrow">Through Our Lens</div><h1>Photos</h1><p>A collection of our latest matchday photography, capturing the intensity, passion and moments that define the game. Every story also has its own full match gallery.</p></div></section>
<section class="section"><div class="wrap"><div class="masonry">{pics}</div></div></section>''' + footer())

# ---------------- Team ----------------
write('/team/', head('Founders', 'Meet David Levinsohn and Andrew Khai, the founders of Footy Daily Network.', '/team/') + header('/team/') + f'''
<section class="page-head"><div class="wrap"><div class="eyebrow">Meet the Founders</div><h1>Who We Are</h1><p>Footy Daily Network was started by two photographers with one idea: give soccer the spotlight it deserves, from the grassroots level to the professional stage.</p></div></section>
<section class="section"><div class="wrap"><div class="founders">{founders_html}</div></div></section>
<section class="cta"><div class="wrap"><div><h2>Shoot with us</h2><p>Photographer, videographer or writer who loves the game? We're always looking for new contributors.</p></div><a class="btn" href="/contact/">Get in touch →</a></div></section>''' + footer())

# ---------------- About ----------------
write('/about/', head('About', 'Our mission is to give soccer the spotlight it deserves — from the grassroots level to the professional stage.', '/about/') + header('/about/') + f'''
<section class="page-head"><div class="wrap"><div class="eyebrow">About Us</div><h1>The Game Beyond<br>the Scoreline</h1></div></section>
<section class="section"><div class="wrap two-col">
  <div class="prose">
    <p class="lead">At Footy Daily Network, our mission is to give soccer the spotlight it deserves — from the grassroots level to the professional stage.</p>
    <p>We started with a simple idea: to capture the energy of the game and share the stories behind the players, teams, and moments that inspire fans everywhere.</p>
    <p>We cover <strong>youth soccer</strong> with the same passion as the <strong>professional game</strong>, showcasing athletes, sharing highlights, and creating a space where the next generation of stars can be seen. Whether it's a local match or a major event, our goal is to bring fans closer to the action through photography, video, and news.</p>
    <p>Soccer isn't just a sport — it's a culture, a community, and a passion. Footy Daily Network is here to capture it all, one post at a time.</p>
    <div class="stats">
      <div class="stat"><b>{len(stories)}</b><span>Stories</span></div>
      <div class="stat"><b>{total_photos + len(PHOTOS):,}</b><span>Photos</span></div>
      <div class="stat"><b>{len(leagues)}</b><span>Leagues covered</span></div>
    </div>
    <a class="btn red" href="/contact/">Work with us →</a>
  </div>
  <img src="{img(stories[1]['cover'])}" alt="" style="border-radius:10px;aspect-ratio:4/5;object-fit:cover;width:100%">
</div></section>''' + footer())

# ---------------- Contact ----------------
phones = ''.join(f'<a href="tel:{p.replace("-", "")}">{p}</a>' for p in PHONES)
write('/contact/', head('Contact', 'Book coverage, collaborate, or get in touch with Footy Daily Network.', '/contact/') + header('/contact/') + f'''
<section class="page-head"><div class="wrap"><div class="eyebrow">Contact Us</div><h1>Let's Talk</h1><p>Have questions, want to book coverage, or collaborate? We'd love to hear from you. We aim to respond within 1–2 business days.</p></div></section>
<section class="section"><div class="wrap two-col">
  <form class="contact" name="contact" method="POST" action="/contact/thanks/" data-netlify="true" netlify-honeypot="company">
    <input type="hidden" name="form-name" value="contact">
    <p hidden><label>Leave blank <input name="company"></label></p>
    <div class="row2">
      <label>Name<input name="name" required autocomplete="name"></label>
      <label>Email<input name="email" type="email" required autocomplete="email"></label>
    </div>
    <div class="row2">
      <label>Club / organization<input name="organization"></label>
      <label>Reason<select name="reason"><option>Book match coverage</option><option>Collaboration</option><option>Join the team</option><option>Photo request</option><option>Other</option></select></label>
    </div>
    <label>Message<textarea name="message" required></textarea></label>
    <div><button class="btn red" type="submit">Send message →</button></div>
  </form>
  <aside class="contact-card">
    <h3>Direct contact</h3>
    <small>Email</small><a href="mailto:{EMAIL}">{EMAIL}</a>
    <small>Phone</small>{phones}
  </aside>
</div></section>''' + footer())

write('/contact/thanks/', head('Thanks', 'Message sent.', '/contact/thanks/') + header('/contact/') + '''
<section class="page-head"><div class="wrap"><div class="eyebrow">Message sent</div><h1>Thank you!</h1><p>We got your message and will get back to you within 1–2 business days.</p><p style="margin-top:24px"><a class="btn red" href="/stories/">Read the latest stories →</a></p></div></section>''' + footer())

# 404
open(os.path.join(ROOT, '404.html'), 'w').write(head('Page not found', 'Page not found', '/404') + header('') + '''
<section class="page-head"><div class="wrap"><div class="eyebrow">404</div><h1>Offside!</h1><p>That page doesn't exist. Try the latest stories instead.</p><p style="margin-top:24px"><a class="btn red" href="/stories/">See stories →</a></p></div></section>''' + footer())

# ---------------- Favicon, redirects, sitemap ----------------
open(os.path.join(ROOT, 'assets', 'favicon.svg'), 'w').write(BALL.replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"'))

redir = ['# Old WordPress URLs -> new pages (Netlify / Cloudflare Pages format)',
         '/from-the-pitch-2/* /stories/ 301', '/about-us/* /about/ 301',
         '/photography/* /team/ 301', '/contact-us/* /contact/ 301']
for s in stories:
    old = re.sub(r'^https?://[^/]+', '', s['old_link'])
    if old and old != f'/stories/{s["slug"]}/':
        redir.append(f'{old} /stories/{s["slug"]}/ 301')
        redir.append(f'{old.rstrip("/")} /stories/{s["slug"]}/ 301')
open(os.path.join(ROOT, '_redirects'), 'w').write('\n'.join(redir) + '\n')

urls = ['/', '/stories/', '/photos/', '/team/', '/about/', '/contact/'] + [f'/stories/{s["slug"]}/' for s in stories]
open(os.path.join(ROOT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
    ''.join(f'  <url><loc>{SITE_URL}{u}</loc></url>\n' for u in urls) + '</urlset>\n')
open(os.path.join(ROOT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n')

print(f'Built {len(stories)} stories, {len(urls)} pages.')
