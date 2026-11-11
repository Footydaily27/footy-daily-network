# Footy Daily Network website

**Add or edit stories:** go to https://footydailynetwork.com/admin (Pages CMS), sign in with GitHub, open **Stories**, click **New entry**, fill it in and press **Save**. The site updates by itself in about a minute.

## What's where
- `content/stories/` – one file per story (the editor writes these)
- `content/photos.yml` – Photos page gallery
- `content/founders.yml` – Founders section
- `assets/img/` – all photos (new uploads go into `assets/img/uploads/`)
- `.pages.yml` – editor settings (Pages CMS); `admin/` just forwards to it
- `build.py` – turns the content into the website (GitHub runs it on every change via .github/workflows/deploy.yml, then publishes it free on GitHub Pages)

## Build on your own computer
```
pip install -r requirements.txt
python3 build.py
```
