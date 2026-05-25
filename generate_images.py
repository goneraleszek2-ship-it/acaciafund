import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys

# Configuration
BLOG_DIRS = [
    Path("content/pl/blog"),
    Path("content/en/blog")
]
IMAGE_SIZE = (1200, 630)  # width, height
FONT_SIZE_TITLE = 48
FONT_SIZE_DATE = 36
MARGIN = 60
LINE_SPACING = 1.2

# Category to color mapping (RGB)
CATEGORY_COLORS = {
    "AML": (59, 105, 153),      # #3B6999
    "Science": (47, 133, 90),   # #2F855A
    "Stocks": (217, 119, 6),    # #D97706
    # Default for unknown categories
    "default": (107, 114, 128)  # #6B7280
}

def get_category_color(categories):
    """Return RGB color for the first category, or default."""
    if not categories:
        return CATEGORY_COLORS["default"]
    # Take the first category
    cat = categories[0].strip()
    return CATEGORY_COLORS.get(cat, CATEGORY_COLORS["default"])

def extract_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL | re.MULTILINE)
    if not match:
        return {}
    fm_text = match.group(1)
    fm = {}
    for line in fm_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            fm[key] = value
    return fm

def parse_categories(cats_str):
    """Parse categories string like '["AML", "Science"]' or 'AML'."""
    if not cats_str:
        return []
    # Remove brackets and quotes, split by comma
    cleaned = cats_str.strip('[]')
    if not cleaned:
        return []
    # Split by comma and clean each item
    parts = [part.strip().strip('\"\'') for part in cleaned.split(',')]
    return [p for p in parts if p]

def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def generate_image_for_post(post_dir):
    """Generate a featured image for a blog post directory."""
    index_file = post_dir / "index.md"
    if not index_file.exists():
        return False

    # Read the markdown file
    try:
        content = index_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  Error reading {index_file}: {e}")
        return False

    # Extract frontmatter
    fm = extract_frontmatter(content)
    if not fm:
        print(f"  No frontmatter found in {index_file}")
        return False

    title = fm.get('title', 'Untitled')
    date_str = fm.get('date', '')
    categories_str = fm.get('categories', '')
    tags_str = fm.get('tags', '')  # Not used for color, but could be

    # Parse categories
    categories = parse_categories(categories_str)
    # Get color based on first category
    bg_color = get_category_color(categories)

    # Determine text color (black or white based on background brightness)
    # Simple brightness formula: (R*299 + G*587 + B*114) / 1000
    r, g, b = bg_color
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)

    # Create image
    img = Image.new('RGB', IMAGE_SIZE, color=bg_color)
    draw = ImageDraw.Draw(img)

    # Load fonts (use default if custom not available)
    try:
        # Try to use a DejaVu font if available, otherwise default
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", FONT_SIZE_TITLE)
        font_date = ImageFont.truetype("DejaVuSans.ttf", FONT_SIZE_DATE)
    except IOError:
        font_title = ImageFont.load_default()
        font_date = ImageFont.load_default()

    # Calculate max width for text
    max_width = IMAGE_SIZE[0] - 2 * MARGIN

    # Wrap title
    title_lines = wrap_text(title, font_title, max_width, draw)
    # Calculate total height of title block
    line_height = font_title.getbbox("Ay")[3] - font_title.getbbox("Ay")[1]  # approximate
    title_block_height = len(title_lines) * line_height * LINE_SPACING

    # Date text
    date_text = date_str  # Already in YYYY-MM-DD format from frontmatter
    date_bbox = draw.textbbox((0, 0), date_text, font=font_date)
    date_width = date_bbox[2] - date_bbox[0]
    date_height = date_bbox[3] - date_bbox[1]

    # Vertical layout: title in upper half, date at bottom
    # We'll leave some margin at top and bottom
    y_text = MARGIN
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        w = bbox[2] - bbox[0]
        x = (IMAGE_SIZE[0] - w) // 2
        draw.text((x, y_text), line, fill=text_color, font=font_title)
        y_text += int(line_height * LINE_SPACING)

    # Date at bottom
    y_date = IMAGE_SIZE[1] - MARGIN - date_height
    x_date = (IMAGE_SIZE[0] - date_width) // 2
    draw.text((x_date, y_date), date_text, fill=text_color, font=font_date)

    # Save image
    image_path = post_dir / "featured.jpg"
    try:
        img.save(image_path, "JPEG", quality=85)
        print(f"  Generated image: {image_path}")
        return True
    except Exception as e:
        print(f"  Error saving image {image_path}: {e}")
        return False

def update_frontmatter(post_dir):
    """Update the frontmatter to set the image path."""
    index_file = post_dir / "index.md"
    try:
        content = index_file.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  Error reading {index_file} for update: {e}")
        return False

    # Determine the relative path from site root
    # We need to convert the post_dir to a path like:
    #   /pl/blog/2026-03-06-aml/featured.jpg
    # or /en/blog/2026-03-06-science/featured.jpg
    # We know the post_dir is under content/<lang>/blog/<slug>/
    # We want to convert to /<lang>/blog/<slug>/featured.jpg
    parts = list(post_dir.parts)
    try:
        # Find the index of 'content'
        content_idx = parts.index('content')
        lang = parts[content_idx + 1]  # 'pl' or 'en'
        # The next part after lang should be 'blog'
        slug = parts[content_idx + 2]  # the blog post directory name
        # Construct the path
        image_path = f"/{lang}/blog/{slug}/featured.jpg"
    except (ValueError, IndexError):
        # Fallback: use a relative path from the post directory
        image_path = "./featured.jpg"

    # Replace the image line in frontmatter
    # We look for a line that starts with 'image:' (possibly with spaces) and replace its value
    lines = content.split('\n')
    in_frontmatter = False
    for i, line in enumerate(lines):
        if line.strip() == '---':
            if not in_frontmatter:
                in_frontmatter = True
            else:
                # End of frontmatter
                break
        if in_frontmatter and line.strip().startswith('image:'):
            # Replace the value after the colon
            key, _ = line.split(':', 1)
            lines[i] = f'{key}: "{image_path}"'
            break
    else:
        # If we didn't find an image line, we need to add it before the closing ---
        # Find the line with the closing ---
        for i, line in enumerate(lines):
            if line.strip() == '---' and i > 0:  # not the first ---
                # Insert before this line
                lines.insert(i, f'image: "{image_path}"')
                break

    new_content = '\n'.join(lines)
    try:
        index_file.write_text(new_content, encoding='utf-8')
        print(f"  Updated frontmatter in {index_file} with image: {image_path}")
        return True
    except Exception as e:
        print(f"  Error writing {index_file}: {e}")
        return False

def main():
    print("Starting image generation for blog posts...")
    total_posts = 0
    posts_with_image = 0
    posts_updated = 0

    for blog_dir in BLOG_DIRS:
        if not blog_dir.exists():
            print(f"Directory {blog_dir} does not exist, skipping.")
            continue

        # Iterate over subdirectories (each blog post)
        for post_dir in blog_dir.iterdir():
            if not post_dir.is_dir():
                continue
            total_posts += 1
            index_file = post_dir / "index.md"
            if not index_file.exists():
                continue

            # Check if image is already set (non-empty)
            try:
                content = index_file.read_text(encoding='utf-8')
                fm = extract_frontmatter(content)
                image_val = fm.get('image', '')
                if image_val and image_val.strip() != '':
                    posts_with_image += 1
                    continue  # Skip if image already set
            except Exception as e:
                print(f"  Error checking image in {index_file}: {e}")
                continue

            print(f"Processing: {post_dir}")
            # Generate image
            if generate_image_for_post(post_dir):
                # Update frontmatter
                if update_frontmatter(post_dir):
                    posts_updated += 1
                else:
                    print(f"  Failed to update frontmatter for {post_dir}")
            else:
                print(f"  Failed to generate image for {post_dir}")

    print("\n--- Summary ---")
    print(f"Total blog posts: {total_posts}")
    print(f"Posts already with image: {posts_with_image}")
    print(f"Posts updated with new image: {posts_updated}")
    print(f"Posts still without image: {total_posts - posts_with_image - posts_updated}")

if __name__ == "__main__":
    main()
