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

export function estimateReadingTime(text) {
  const wordsPerMinute = 200;
  const wordCount = text.trim().split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}

export function generateTagBadgeSVG(tag) {
  // Simple color mapping for common tags
  const colorMap = {
    aml: '#38bdf8',
    stock: '#fbbf24',
    science: '#a855f7',
    compliance: '#60a5fa',
    regtech: '#34d399',
    'financial-crime': '#f87171',
    technology: '#fdba74',
    'ai-artificial-intelligence': '#f472b6',
    blockchain: '#8b5cf6',
    'machine-learning': '#ec4899'
  };
  
  const color = colorMap[tag.toLowerCase().replace(/\s+/g, '-')] || '#6b7280';
  
  return `
    <svg width="60" height="20" xmlns="http://www.w3.org/2000/svg">
      <rect width="60" height="20" rx="3" fill="${color}" fill-opacity="0.1" stroke="${color}" stroke-opacity="0.2"/>
      <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="${color}" font-size="10" font-weight="500">
        ${tag}
      </text>
    </svg>
  `;
}

export function generateSimpleSparkline(dataPoints) {
  if (!dataPoints || dataPoints.length === 0) return '';
  
  const width = 60;
  const height = 20;
  const padding = 2;
  const plotWidth = width - 2 * padding;
  const plotHeight = height - 2 * padding;
  
  // Normalize data points to 0-1 range
  const minVal = Math.min(...dataPoints);
  const maxVal = Math.max(...dataPoints);
  const range = maxVal - minVal || 1;
  const normalized = dataPoints.map(val => (val - minVal) / range);
  
  // Create SVG path for line
  const points = normalized.map((val, idx) => {
    const x = padding + (idx / (normalized.length - 1)) * plotWidth;
    const y = height - padding - val * plotHeight;
    return `${x},${y}`;
  }).join(' ');
  
  return `
    <svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
      <polyline fill="none" stroke="var(--accent-2)" stroke-width="1.5" points="${points}" />
    </svg>
  `;
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
  // Extract headings (h1-h3) from raw markdown for table of contents
  const headingRegex = /^(#{1,3})\s+(.+)$/gm;
  const headings = [];
  let match;
  while ((match = headingRegex.exec(raw)) !== null) {
    const level = match[1].length;
    const text = match[2].trim();
    headings.push({ level, text });
  }
  return { filePath, slug, baseName, section, data: parsed.data || {}, html, raw: parsed.content, excerpt: stripMarkdown(cleanedContent).slice(0, 220), bayesDemo, headings };
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
