"""CMS Admin Server — lightweight HTTP server for content management.

Serves the static site and provides:
  - Admin HTML pages (Jinja2 rendered with live registry data)
  - JSON API endpoints for CRUD operations on registry.json
  - Build trigger (non-blocking, runs in background thread)

Usage:
    python3 scripts/serve_cms.py [--port 8000] [--bind 0.0.0.0]
"""
import json
import os
import re
import sys
import html as html_mod
import threading
import mimetypes
import io
import hashlib
import uuid
import copy
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse, parse_qs

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = ROOT / "dist"
UPLOADS = ROOT / "static" / "uploads"
THUMBS = UPLOADS / "thumbs"
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

sys.path.insert(0, str(ROOT))
from scripts.cms_api import CMS, CONTENT_TYPES, PILLARS, DIFFICULTIES
from core.urls import slug_to_url


def build_preview_html(item: Dict[str, Any]) -> str:
    """Generate a simple HTML preview from item data."""
    title = html_mod.escape(item.get("title", "Untitled"))
    body = item.get("body_html", "")
    desc = html_mod.escape(item.get("description", ""))
    pillar = item.get("pillar", "aml")
    pillar_label = PILLARS.get(pillar, pillar)
    ct = item.get("content_type", "research")
    ct_label = CONTENT_TYPES.get(ct, ct)

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Preview</title>
<link rel="stylesheet" href="/css/design-system.css">
<style>
  body {{ max-width: 66ch; margin: 2rem auto; padding: 0 1rem; }}
  .preview-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.7rem; font-weight: 600; background: #d97706; color: #fff; margin-bottom: 0.5rem; }}
  .prose-body {{ font-size: 1.0625rem; line-height: 1.7; }}
</style>
</head>
<body>
<div class="preview-badge">{pillar_label} / {ct_label}</div>
<h1>{title}</h1>
<p style="color:#666;font-size:0.95rem">{desc}</p>
<hr style="margin:1.5rem 0;border:none;border-top:1px solid #ddd">
<div class="prose-body">{body}</div>
</body></html>"""


class CMSHandler(SimpleHTTPRequestHandler):
    cms = CMS()
    template_cache: Dict[str, str] = {}

    def __init__(self, *args, **kwargs):
        self._jinja_env = None
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        if self.path.startswith("/static/") or self.path.endswith((".css", ".js", ".woff2", ".png", ".webp")):
            return
        super().log_message(format, *args)

    @property
    def jinja_env(self):
        if self._jinja_env is None:
            import jinja2
            loader = jinja2.FileSystemLoader(str(ROOT / "templates"))
            self._jinja_env = jinja2.Environment(
                loader=loader,
                autoescape=False,
                cache_size=50,
            )
        return self._jinja_env

    def _asset_filter(self, path: str) -> str:
        """Resolve asset paths — for the CMS server we just pass through since dist/ is built."""
        import hashlib
        local = (DIST / path.lstrip("/")).resolve()
        if local.exists() and local.is_file():
            h = hashlib.md5(local.read_bytes()).hexdigest()[:8]
            return f"/{path}?v={h}"
        return f"/{path}"

    def render_admin(self, template_name: str, **extra: Any) -> str:
        env = self.jinja_env
        env.filters.setdefault("asset", self._asset_filter)
        tmpl = env.get_template(f"admin/{template_name}")
        ctx = {
            "site_name": "AcaciaFund CMS",
            "year": "2026",
            "slug_to_url": slug_to_url,
            "content": {"title": "AcaciaFund CMS"},
        }
        ctx.update(extra)
        return tmpl.render(**ctx)

    def _get_query_param(self, name: str) -> str:
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        vals = params.get(name, [])
        return vals[0] if vals else ""

    def send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def serve_static_or_404(self, path: str):
        """Try to serve a static file from dist/ or return 404."""
        local = (DIST / path.lstrip("/")).resolve()
        if local.exists() and local.is_file() and str(local).startswith(str(DIST)):
            self.send_response(200)
            suffix = local.suffix
            ctype = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".svg": "image/svg+xml",
                ".png": "image/png",
                ".webp": "image/webp",
                ".woff2": "font/woff2",
                ".ico": "image/x-icon",
            }.get(suffix, "application/octet-stream")
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(local.stat().st_size))
            self.end_headers()
            with open(local, "rb") as f:
                self.wfile.write(f.read())
            return
        self.send_error(404, "Not Found")

    def do_GET(self):
        path = self.path.split("?")[0]
        params = {}
        if "?" in self.path:
            for part in self.path.split("?", 1)[1].split("&"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    from urllib.parse import unquote_plus
                    params[k] = unquote_plus(v)

        # Admin CMS pages
        if path == "/admin/cms_list.html":
            pillar = params.get("pillar", "")
            ct = params.get("content_type", "")
            search = params.get("search", "")
            page = int(params.get("page", "1"))
            limit = 50
            offset = (page - 1) * limit
            items, total = self.cms.list(pillar=pillar or None, content_type=ct or None, search=search or None, limit=limit, offset=offset)
            total_pages = max(1, (total + limit - 1) // limit)
            html = self.render_admin(
                "cms_list.html",
                active_page="cms_list",
                items=items,
                total=total,
                page=page,
                total_pages=total_pages,
                search_query=search,
                pillar_filter=pillar,
                type_filter=ct,
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/admin/cms_editor.html":
            slug = params.get("slug", "")
            is_new = not slug
            if slug:
                item = self.cms.get(slug)
                if not item:
                    self.send_error(404, "Content not found")
                    return
            else:
                item = {
                    "slug": "",
                    "title": "",
                    "description": "",
                    "body_html": "",
                    "pillar": "aml",
                    "content_type": "research",
                    "tags": [],
                    "date_str": "",
                    "difficulty": "",
                }

            # Load concept names for autocomplete
            concepts = self.cms.list_concepts()
            concept_names = [c.get("label", "") for c in concepts]

            preview_html = build_preview_html(item) if item and item.get("body_html", "").strip() else ""
            html = self.render_admin(
                "cms_editor.html",
                active_page="cms_editor",
                item=item,
                is_new=is_new,
                preview_html=preview_html,
                concept_names=concept_names,
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Media library page
        if path == "/admin/cms_media.html":
            html = self.render_admin(
                "cms_media.html",
                active_page="cms_media",
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Serve uploaded media
        if path.startswith("/uploads/"):
            local = (UPLOADS / path.lstrip("/uploads/")).resolve()
            if local.exists() and local.is_file() and str(local).startswith(str(UPLOADS)):
                self.send_response(200)
                ctype, _ = mimetypes.guess_type(str(local))
                self.send_header("Content-Type", ctype or "application/octet-stream")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.send_header("Content-Length", str(local.stat().st_size))
                self.end_headers()
                with open(local, "rb") as f:
                    self.wfile.write(f.read())
                return
            self.send_error(404, "Not Found")
            return

        # CMS Dashboard
        if path == "/admin/cms_dashboard.html":
            html = self.render_admin(
                "cms_dashboard.html",
                active_page="cms_dashboard",
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        # Admin static (CSS/JS/images from dist)
        if path.startswith("/admin/") or path.startswith("/css/") or path.startswith("/js/") or path.startswith("/fonts/") or path.startswith("/images/"):
            if path.startswith("/admin/"):
                # Try admin template first, fall through to static
                pass
            self.serve_static_or_404(path)
            return

        # Existing admin pages (from build)
        if path.startswith("/admin/") and path.endswith(".html"):
            self.serve_static_or_404(path)
            return

        # Export endpoint
        if path == "/api/cms/export":
            all_items, _ = self.cms.list(limit=9999)
            slugs_param = self._get_query_param("slugs")
            if slugs_param:
                selected = set(s.strip() for s in slugs_param.split(","))
                all_items = [i for i in all_items if i.get("slug") in selected]
            body = json.dumps(all_items, indent=2, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Disposition", 'attachment; filename="cms_export.json"')
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Media list endpoint (GET)
        if path == "/api/cms/media/list":
            try:
                UPLOADS.mkdir(parents=True, exist_ok=True)
                files = []
                for f in sorted(UPLOADS.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                    if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS:
                        files.append({
                            "filename": f.name,
                            "url": f"/uploads/{f.name}",
                            "size": f.stat().st_size,
                            "modified": f.stat().st_mtime,
                        })
                self.send_json({"ok": True, "files": files})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})
            return

        # Stats API
        if path == "/api/cms/stats":
            self.send_json({"ok": True, **self.cms.stats()})
            return

        # Versions API
        if path == "/api/cms/versions":
            slug = params.get("slug", "")
            if not slug:
                self.send_json({"ok": False, "error": "Missing slug parameter"})
                return
            versions = self.cms.list_versions(slug)
            self.send_json({"ok": True, "versions": versions})
            return

        # Suggest API (autocomplete)
        if path == "/api/cms/suggest":
            q = params.get("q", "").strip()
            pillar = params.get("pillar", "")
            ct = params.get("content_type", "")
            if len(q) < 2:
                self.send_json({"ok": True, "results": []})
                return
            items, _ = self.cms.list(search=q, pillar=pillar or None, content_type=ct or None, limit=20)
            results = [{"slug": i.get("slug", ""), "title": (i.get("title", "") or "").strip(), "pillar": i.get("pillar", ""), "content_type": i.get("content_type", "")} for i in items]
            self.send_json({"ok": True, "results": results})
            return

        # Root — redirect to admin
        if path == "/" or path == "":
            self.send_response(302)
            self.send_header("Location", "/admin/cms_list.html")
            self.end_headers()
            return

        # Static site pages
        self.serve_static_or_404(path)

    def do_POST(self):
        path = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length else b""

        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" in ctype:
            # Store raw for multipart handlers
            self._raw_body = raw_body
            data = {}
        else:
            try:
                data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except (json.JSONDecodeError, UnicodeDecodeError):
                data = {}

        # Save endpoint (create or update)
        if path == "/api/cms/save":
            slug = data.get("slug", "").strip()
            if not slug:
                self.send_json({"ok": False, "error": "Slug is required"})
                return

            existing = self.cms.get(slug)
            fields = ["title", "description", "body_html", "pillar", "content_type", "difficulty", "date_str", "tags"]
            updates = {k: data.get(k) for k in fields if k in data}

            if existing:
                result = self.cms.update(slug, updates)
            else:
                result = self.cms.create(data)

            if result:
                preview = build_preview_html(result)
                self.send_json({"ok": True, "slug": result.get("slug", slug), "preview_html": preview})
            else:
                self.send_json({"ok": False, "error": "Save failed"})
            return

        # Delete endpoint
        if path == "/api/cms/delete":
            slug = data.get("slug", "")
            ok = self.cms.delete(slug)
            self.send_json({"ok": ok, "error": None if ok else "Not found"})
            return

        # Duplicate endpoint
        if path == "/api/cms/duplicate":
            slug = data.get("slug", "")
            if not slug:
                self.send_json({"ok": False, "error": "Slug required"})
                return
            item = self.cms.get(slug)
            if not item:
                self.send_json({"ok": False, "error": "Not found"})
                return
            new_item = copy.deepcopy(item)
            new_slug = slug + "-copy"
            n = 1
            while self.cms.get(new_slug):
                n += 1
                new_slug = f"{slug}-copy-{n}"
            new_item["slug"] = new_slug
            new_item["title"] = (new_item.get("title") or "Untitled") + " (Copy)"
            new_item["date_str"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            result = self.cms.create(new_item)
            self.send_json({"ok": True, "new_slug": result.get("slug", new_slug)})
            return

        # Media upload endpoint
        if path == "/api/cms/media/upload":
            content_type = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in content_type:
                self.send_json({"ok": False, "error": "Expected multipart/form-data"}, 400)
                return

            try:
                raw = getattr(self, '_raw_body', b"")
                boundary = content_type.split("boundary=")[-1].strip()
                # Find the file part
                parts = raw.split(b"--" + boundary.encode())
                filename = None
                data = None
                for part in parts:
                    if b"Content-Disposition" not in part:
                        continue
                    # Extract filename
                    fn_match = re.search(rb'filename="([^"]*)"', part)
                    if not fn_match:
                        continue
                    filename = fn_match.group(1).decode("utf-8", errors="replace")
                    # Find blank line separating headers from body
                    header_end = part.find(b"\r\n\r\n")
                    if header_end == -1:
                        continue
                    data = part[header_end + 4:].rstrip(b"\r\n--")
                    break

                if not filename or not data:
                    self.send_json({"ok": False, "error": "No file found in upload"})
                    return

                ext = Path(filename).suffix.lower()
                if ext not in ALLOWED_EXTENSIONS:
                    self.send_json({"ok": False, "error": f"Unsupported file type: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"})
                    return

                if len(data) > MAX_UPLOAD_SIZE:
                    self.send_json({"ok": False, "error": f"File too large. Max {MAX_UPLOAD_SIZE // 1024 // 1024}MB"})
                    return

                stem = Path(filename).stem
                safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', stem)[:60]
                unique = f"{safe_stem}_{uuid.uuid4().hex[:8]}{ext}"
                dest = UPLOADS / unique

                UPLOADS.mkdir(parents=True, exist_ok=True)
                with open(dest, "wb") as f:
                    f.write(data)

                self.send_json({"ok": True, "filename": unique, "url": f"/uploads/{unique}", "size": len(data)})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)})
            return

        # Media delete endpoint
        if path == "/api/cms/media/delete":
            filename = data.get("filename", "")
            if not filename:
                self.send_json({"ok": False, "error": "filename required"})
                return
            target = (UPLOADS / filename).resolve()
            if target.exists() and target.is_file() and str(target).startswith(str(UPLOADS)):
                target.unlink()
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": "Not found"})
            return

        # Build endpoint (non-blocking — runs in background thread)
        if path == "/api/cms/build":
            if hasattr(self.__class__, '_build_running') and self.__class__._build_running:
                self.send_json({"ok": False, "error": "Build already in progress"})
                return
            self.__class__._build_running = True

            def _run_build():
                try:
                    self.cms.build()
                finally:
                    self.__class__._build_running = False

            t = threading.Thread(target=_run_build, daemon=True)
            t.start()
            self.send_json({"ok": True, "message": "Build started in background"})
            return

        # Restore version endpoint
        if path == "/api/cms/restore":
            slug = data.get("slug", "")
            timestamp = data.get("timestamp", "")
            if not slug or not timestamp:
                self.send_json({"ok": False, "error": "slug and timestamp required"})
                return
            result = self.cms.restore_version(slug, timestamp)
            if result:
                preview = build_preview_html(result)
                self.send_json({"ok": True, "slug": slug, "preview_html": preview})
            else:
                self.send_json({"ok": False, "error": "Version not found or restore failed"})
            return

        self.send_json({"ok": False, "error": "Unknown endpoint"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="AcaciaFund CMS Admin Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    parser.add_argument("--bind", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    args = parser.parse_args()

    server = HTTPServer((args.bind, args.port), CMSHandler)
    print(f"\n{'='*55}")
    print(f"  AcaciaFund CMS Server")
    print(f"  Admin: http://{args.bind}:{args.port}/admin/cms_list.html")
    print(f"  API:   http://{args.bind}:{args.port}/api/cms/")
    print(f"  Site:  http://{args.bind}:{args.port}/")
    print(f"{'='*55}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
