#!/usr/bin/env python3
"""
Build Cache System for AcaciaFund.
Implements mtime/SHA-256 based incremental builds to reduce build time from 18.9s to <10s.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional


CACHE_FILE = Path('.build_cache.json')
CACHE_VERSION = '1.0'


class BuildCache:
    """Incremental build cache using file hashes and mtimes.
    
    Separates content hash (source markdown) from layout hash (templates)
    to enable proper incremental builds.
    """
    
    def __init__(self, cache_file: Optional[Path] = None):
        self.cache_file = cache_file or CACHE_FILE
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.templates_hash: Optional[str] = None
        self.content_templates_hash: Optional[str] = None  # Hash of content-affecting templates only
        self.load()
    
    def load(self) -> None:
        """Load cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                
                if data.get('version') == CACHE_VERSION:
                    self.cache = data.get('entries', {})
                    self.templates_hash = data.get('templates_hash')
                    self.content_templates_hash = data.get('content_templates_hash')
                    print(f"📦 Cache loaded: {len(self.cache)} entries")
                else:
                    print("⚠️  Cache version mismatch, clearing cache")
                    self.cache = {}
                    self.templates_hash = None
                    self.content_templates_hash = None
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  Cache load error: {e}, clearing cache")
                self.cache = {}
                self.templates_hash = None
                self.content_templates_hash = None
        else:
            print("ℹ️  No existing cache found")
    
    def save(self) -> None:
        """Save cache to disk."""
        data = {
            'version': CACHE_VERSION,
            'generated_at': time.time(),
            'templates_hash': self.templates_hash,
            'content_templates_hash': self.content_templates_hash,
            'entries': self.cache
        }
        
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Cache saved: {len(self.cache)} entries")
    
    def compute_file_hash(self, filepath: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content string."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def compute_templates_hash(self, template_dir: Path, content_only: bool = False) -> str:
        """Compute combined hash of templates.
        
        Args:
            template_dir: Directory containing templates
            content_only: If True, only hash templates that affect content rendering
                         (article templates), not layout/global templates
        """
        combined = hashlib.sha256()
        
        # Content-affecting templates (change → content needs rebuild)
        content_templates = {
            'blog_post.j2', 'learn_article.j2', 'knowledge_article.j2',
            'category_index.j2', 'pillar_index.j2', 'layout.j2'
        }
        
        # All templates (change → full rebuild including taxonomies)
        all_templates = content_templates | {
            'tag_index.j2', 'admin_dashboard.j2', 'admin_gallery.j2',
            'search.j2', 'feed.xml', 'index.j2', '404.html'
        }
        
        templates_to_hash = content_templates if content_only else all_templates
        
        for template_file in template_dir.rglob('*.j2'):
            relative_path = template_file.relative_to(template_dir)
            if relative_path.name in templates_to_hash:
                file_hash = self.compute_file_hash(template_file)
                combined.update(f"{relative_path}:{file_hash}".encode())
        
        # Also hash core modules that affect rendering
        core_dir = Path('core')
        if core_dir.exists():
            for py_file in core_dir.glob('*.py'):
                file_hash = self.compute_file_hash(py_file)
                combined.update(f"{py_file}:{file_hash}".encode())
        
        result = combined.hexdigest()
        if content_only:
            self.content_templates_hash = result
        else:
            self.templates_hash = result
        return result
    
    def needs_rebuild(self, filepath: Path, content: Optional[str] = None,
                      is_content: bool = True) -> bool:
        """Check if a file needs to be rebuilt.

        Args:
            filepath: Output file path
            content: Content hash string (from _get_content_hash) or raw content
            is_content: If True, compare content_templates_hash only;
                        if False, compare full templates_hash
        """
        path_key = str(filepath)

        if path_key not in self.cache:
            return True

        cached = self.cache[path_key]

        # Content items: only content-affecting template changes trigger rebuild
        if is_content:
            ref_hash = self.content_templates_hash or self.templates_hash
            cached_hash = cached.get('content_templates_hash') or cached.get('templates_hash')
        else:
            ref_hash = self.templates_hash
            cached_hash = cached.get('templates_hash')

        if ref_hash and cached_hash and cached_hash != ref_hash:
            return True

        # Check content hash
        if content:
            current_hash = self.compute_content_hash(content)
            if cached.get('content_hash') != current_hash:
                return True
        else:
            if filepath.exists():
                current_hash = self.compute_file_hash(filepath)
                if cached.get('file_hash') != current_hash:
                    return True

        return False
    
    def update_entry(self, filepath: Path, content: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None,
                     is_content: bool = True) -> None:
        """Update cache entry for a file.

        Args:
            filepath: Output file path
            content: Content hash string or raw content
            metadata: Additional metadata dict
            is_content: If True, store content_templates_hash; else store templates_hash
        """
        path_key = str(filepath)

        entry = {
            'updated_at': time.time(),
        }

        if is_content:
            if self.content_templates_hash:
                entry['content_templates_hash'] = self.content_templates_hash
            elif self.templates_hash:
                entry['templates_hash'] = self.templates_hash
        else:
            if self.templates_hash:
                entry['templates_hash'] = self.templates_hash

        if content:
            entry['content_hash'] = self.compute_content_hash(content)
        elif filepath.exists():
            entry['file_hash'] = self.compute_file_hash(filepath)

        if metadata:
            entry.update(metadata)

        self.cache[path_key] = entry
    
    def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries. If pattern provided, only invalidate matching entries."""
        if pattern:
            invalidated = sum(1 for key in list(self.cache.keys()) if pattern in key)
            self.cache = {k: v for k, v in self.cache.items() if pattern not in k}
        else:
            invalidated = len(self.cache)
            self.cache = {}
        
        return invalidated
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'total_entries': len(self.cache),
            'templates_hash': self.templates_hash,
            'cache_file': str(self.cache_file),
            'cache_size_kb': self.cache_file.stat().st_size / 1024 if self.cache_file.exists() else 0
        }


def get_cache() -> BuildCache:
    """Get singleton cache instance."""
    return BuildCache()


def check_template_changes(template_dir: Path, cache: BuildCache) -> bool:
    """Check if any templates have changed since last build."""
    current_hash = cache.compute_templates_hash(template_dir, content_only=False)
    
    if cache.templates_hash is None:
        print("🔄 First build, templates will be hashed")
        return True
    
    if current_hash != cache.templates_hash:
        print("🔄 Templates changed, full rebuild required")
        return True
    
    return False


def get_worker_pool() -> Optional[Any]:
    """Get multiprocessing pool with optimal worker count for ARM."""
    try:
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        # Use 75% of CPUs for better responsiveness on mobile ARM
        worker_count = max(1, int(cpu_count * 0.75))
        return multiprocessing.Pool(processes=worker_count)
    except Exception:
        return None


def parallel_map(func, items, pool=None):
    """Parallel map with fallback to sequential execution."""
    if pool is None:
        return [func(item) for item in items]
    
    try:
        return pool.map(func, items)
    except Exception:
        # Fallback to sequential on error
        return [func(item) for item in items]
