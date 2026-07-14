# Asset Pipeline

The asset pipeline handles image generation, topic icons, OG images, and static file copying.

## Components

### Topic Icons (`core/visuals.py`)

Content items with tags get up to 3 SVG topic icons rendered on their card. The mapping is:

```
Tags → resolve_topic_icon(tag) → SVG path data
```

- Primary match: exact tag match in `TOPIC_ICONS`
- Secondary match: subtopic keywords in `SUBTOPIC_CATEGORIES`
- Tertiary match: substring match against topic keys
- Fallback: `generate_fallback_svg()`

### OG Images (`core/visuals.py:generate_og_image()`)

Open Graph images are generated for social sharing:

```python
def generate_og_image(title, pillar, slug, output_dir):
    # Renders SVG with title + pillar branding
    # Saves to dist/static/og/{slug}.png
    # Returns URL path
```

- Dimensions: 1200×630px (standard OG)
- Pillar-colored background
- Title text overlay
- Generated on first build, cached thereafter

### Thumbnails (`core/visuals.py:generate_thumbnail_svg()`)

Card thumbnails are SVG-based:

```python
def generate_thumbnail_svg(topic_key, pillar):
    # Returns SVG string for inline use in cards
```

### Featured Images (`build.py:resolve_featured_image()`)

Content items can have featured images resolved through a pipeline:

```python
def resolve_featured_image(raw_path: str) -> str:
    # 1. Check if path is a known Unsplash image
    # 2. Check if path is a local file in content/
    # 3. Fall back to generated placeholder
```

### Section Images (`build.py:inject_section_images()`)

Body content can have section-specific images injected:

```python
def inject_section_images(body_html, section_images, article=None):
    # Matches section headings to images
    # Injects <img> tags after matching headings
```

### Unsplash Image Cache (`scripts/fetch_images.py`)

`scripts/fetch_images.py` maintains a curated set of known Unsplash images used by the build:

```python
# From build_taxonomies.py
from scripts.fetch_images import CURATED_KNOWN

section_images = CURATED_KNOWN.get(slug, [])
```

### Static Assets (`core/assets.py`)

Static files (CSS, JS, fonts, images) are managed by the asset manager:

```python
from core.assets import create_asset_manager
manager = create_asset_manager(PIPELINE_STATIC_DIR, STATIC_DST_DIR)
manager.copy_all()
```

Assets copied from `static/` → `dist/static/`:

| Pattern | Examples |
|---------|---------|
| `static/css/*.css` | `main.css`, `admin.css` |
| `static/js/*.js` | `search.js`, `graph.js`, `fuse.js` |
| `static/img/*` | Logos, icons, favicon |
| `static/fonts/*` | Custom fonts |

## Image Generation Performance

- OG images: ~0.5s per image (PIL-based PNG rendering)
- Thumbnails: ~0.05s per icon (inline SVG, no file I/O)
- Section images: ~0.01s per injection (string replacement)

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Missing OG image | `static/og/` dir missing | Clear cache and rebuild |
| Broken topic icon | Tag not in `TOPIC_ICONS` | Add icon mapping or check tag spelling |
| Placeholder images everywhere | Unsplash API rate limit | Check `CURATED_KNOWN` in `fetch_images.py` |
| SVGs not rendering | Missing path data in `TOPIC_ICONS` | Add SVG path data to `resolve_topic_icon` |

> **See also:** [Build Overview](build-overview.md), [Troubleshooting](troubleshooting.md)
