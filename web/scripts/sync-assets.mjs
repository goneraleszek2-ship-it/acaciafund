import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const WEB_ROOT = path.resolve(HERE, '..');
const REPO_ROOT = path.resolve(WEB_ROOT, '..');
const PUBLIC_DIR = path.join(WEB_ROOT, 'public');
const STATIC_DIR = path.join(REPO_ROOT, 'static');
const BLOG_DIR = path.join(REPO_ROOT, 'content', 'pl', 'blog');

function copyDir(src, dest) {
  if (!fs.existsSync(src)) return;
  fs.rmSync(dest, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.cpSync(src, dest, { recursive: true });
}

function syncBlogAssets() {
  if (!fs.existsSync(BLOG_DIR)) return;
  for (const entry of fs.readdirSync(BLOG_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const srcDir = path.join(BLOG_DIR, entry.name);
    const destDir = path.join(PUBLIC_DIR, 'blog', entry.name);
    const files = fs.readdirSync(srcDir, { withFileTypes: true })
      .filter((file) => file.isFile() && file.name !== 'index.md')
      .map((file) => file.name);
    if (!files.length) continue;
    fs.mkdirSync(destDir, { recursive: true });
    for (const fileName of files) {
      fs.copyFileSync(path.join(srcDir, fileName), path.join(destDir, fileName));
    }
  }
}

fs.mkdirSync(PUBLIC_DIR, { recursive: true });
copyDir(STATIC_DIR, PUBLIC_DIR);
syncBlogAssets();
