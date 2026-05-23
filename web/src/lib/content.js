import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import matter from 'gray-matter';
import { marked } from 'marked';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');
const CONTENT_ROOT = path.join(ROOT, 'content');
const REGISTRY_PATH = path.join(ROOT, 'registry', 'index.json');

marked.setOptions({ breaks: true });

function exists(filePath) {
  try { return fs.existsSync(filePath); } catch { return false; }
}

function walk(dir) {
  if (!exists(dir)) return [];
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  const out = [];
  for (const entry of entries) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}

function stripMarkdown(text) {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/[#>*_~-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function extractBayesDemo(content) {
  const match = content.match(/{{<\s*bayes\s+([^>]+?)\s*>}}/i);
  if (!match) return null;
  const attrs = Object.fromEntries(
    [...match[1].matchAll(/([a-zA-Z0-9_-]+)="([^"]+)"/g)].map((m) => [m[1], m[2]])
  );
  return {
    prior: attrs.prior || '0.5',
    like: attrs.like || '0.7',
  };
}

function parseMarkdown(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const parsed = matter(raw);
  const bayesDemo = extractBayesDemo(parsed.content);
  const cleanedContent = parsed.content.replace(/{{<\s*bayes\s+[^>]+\s*>}}/gi, '').trim();
  const html = marked.parse(cleanedContent);
  const slug = path.basename(path.dirname(filePath));
  const baseName = path.basename(filePath);
  const section = path.basename(path.dirname(path.dirname(filePath)));
  return { filePath, slug, baseName, section, data: parsed.data || {}, html, raw: parsed.content, excerpt: stripMarkdown(cleanedContent).slice(0, 220), bayesDemo };
}

export function loadRegistry() {
  if (!exists(REGISTRY_PATH)) {
    return { counts: { pages: 0, runs: 0, pillars: {} }, latest_by_pillar: {}, pages: [], runs: [] };
  }
  return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
}

export function loadBlogPosts() {
  const posts = [];
  
  // Check both language directories for blog posts
  const languageDirs = ['pl', 'en'];
  
  for (const lang of languageDirs) {
    const blogRoot = path.join(CONTENT_ROOT, lang, 'blog');
    if (!exists(blogRoot)) continue;
    
    const langPosts = walk(blogRoot)
      .filter((filePath) => path.basename(filePath) === 'index.md' && !path.basename(path.dirname(filePath)).startsWith('_'))
      .map((filePath) => {
        const parsed = parseMarkdown(filePath);
        const slug = path.basename(path.dirname(filePath));
        const data = parsed.data;
        const thumbnail = data.thumbnail || data.featured_image || data.og_image || '';
        return {
          ...parsed,
          slug,
          title: data.title || slug,
          date: data.date || slug.slice(0, 10),
          category: Array.isArray(data.categories) ? data.categories[0] || 'Post' : (data.categories || 'Post'),
          tags: Array.isArray(data.tags) ? data.tags : [],
          thumbnail,
          imageUrl: thumbnail ? `/${lang}/blog/${slug}/${thumbnail}` : (data.image || ''),
          summary: data.description || parsed.excerpt,
          lang: lang
        };
      });
    
    posts.push(...langPosts);
  }
  
  return posts
    .sort((a, b) => String(b.date).localeCompare(String(a.date)) || a.slug.localeCompare(b.slug));
}

export function getBlogPost(slug) {
  return loadBlogPosts().find((post) => post.slug === slug) || null;
}

export function loadLessons() {
  const lessons = [];
  
  // Check both language directories for lessons
  const languageDirs = ['pl', 'en'];
  
  for (const lang of languageDirs) {
    const lessonsRoot = path.join(CONTENT_ROOT, lang, 'learn');
    if (!exists(lessonsRoot)) continue;
    
    const langLessons = walk(lessonsRoot)
      .filter((filePath) => filePath.endsWith('.md') && !path.basename(filePath).startsWith('_'))
      .map((filePath) => {
        const parsed = parseMarkdown(filePath);
        const data = parsed.data;
        return {
          ...parsed,
          slug: path.basename(filePath, '.md'),
          title: data.title || path.basename(filePath, '.md'),
          difficulty: data.difficulty || '',
          tags: Array.isArray(data.tags) ? data.tags : [],
          sqi: data.sqi || 0,
          summary: data.description || parsed.excerpt,
          bayesDemo: parsed.bayesDemo,
          lang: lang
        };
      });
    
    lessons.push(...langLessons);
  }
  
  return lessons
    .sort((a, b) => a.slug.localeCompare(b.slug));
}

export function getLesson(slug) {
  return loadLessons().find((lesson) => lesson.slug === slug) || null;
}

export function loadSectionPage(section) {
  const candidates = [
    path.join(CONTENT_ROOT, section, '_index.md'),
    path.join(CONTENT_ROOT, section, 'index.md'),
  ];
  const filePath = candidates.find(exists);
  if (!filePath) return null;
  const parsed = parseMarkdown(filePath);
  return {
    ...parsed,
    section,
    title: parsed.data.title || section,
    summary: parsed.data.description || parsed.excerpt,
  };
}

export function loadHomepageData() {
  const registry = loadRegistry();
  const posts = loadBlogPosts();
  return {
    registry,
    latestByPillar: registry.latest_by_pillar || {},
    latestPosts: posts.slice(0, 6),
    posts,
    lessons: loadLessons(),
  };
}
