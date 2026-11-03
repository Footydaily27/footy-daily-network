# Footy Daily Network website

**Add or edit stories:** go to https://footydailynetwork.com/admin, log in with GitHub, click **New Story**, fill it in and press **Publish**. The site updates by itself in about a minute.

## What's where
- `content/stories/` – one file per story (the editor writes these)
- `content/photos.yml` – Photos page gallery
- `content/founders.yml` – Founders section
- `assets/img/` – all photos (new uploads go into `assets/img/uploads/`)
- `admin/` – the editor (Decap CMS)
- `build.py` – turns the content into the website (Netlify runs it on every change)

## Build on your own computer
```
pip install -r requirements.txt
python3 build.py
```
