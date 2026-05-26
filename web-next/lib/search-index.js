console.log('SEARCH INDEX SCRIPT STARTING');

const fs = require('fs');
const path = require('path');
const lunr = require('lunr');

console.log('Modules loaded');

const BLOG_DIR = path.join(process.cwd(), '../content/pl/blog');
const LEARN_DIR = path.join(process.cwd(), '../content/pl/learn');
const OUTPUT_DIR = path.join(process.cwd(), 'public/search');

console.log('Directories defined:', { BLOG_DIR, LEARN_DIR, OUTPUT_DIR });

function parseFrontmatter(raw) {
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const lines = match[1].split('\n');
  const meta = {};
  for (const line of lines) {
    const kv = line.match(/^(\w+):\s*(.+)$/);
    if (kv) meta[kv[1]] = kv[2].replace(/^["']|["']$/g, '');
  }
  return meta;
}

// Simple HTML tag stripper using regex
function stripTags(html) {
  return html.replace(/<[^>]*>/g, ' ');
}

function generateSearchIndex() {
  console.log('Starting search index generation...');
  console.log('BLOG_DIR:', BLOG_DIR);
  console.log('LEARN_DIR:', LEARN_DIR);
  console.log('OUTPUT_DIR:', OUTPUT_DIR);
  
  // Ensure output directory exists
  if (!fs.existsSync(OUTPUT_DIR)) {
    console.log('Creating output directory:', OUTPUT_DIR);
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  } else {
    console.log('Output directory already exists');
  }

  const documents = [];

  // Index blog posts
  console.log('Indexing blog posts...');
  const blogDirs = fs.readdirSync(BLOG_DIR).filter(dir => 
    fs.statSync(path.join(BLOG_DIR, dir)).isDirectory()
  );
  console.log('Found', blogDirs.length, 'blog directories');

  for (const slug of blogDirs) {
    const filePath = path.join(BLOG_DIR, slug, 'index.md');
    try {
      const raw = fs.readFileSync(filePath, 'utf8');
      const meta = parseFrontmatter(raw);
      const content = raw.replace(/^---[\s\S]*?---/, '').trim();
      
      // Strip HTML tags from content for better search
      const plainContent = stripTags(content);
      
      documents.push({
        id: `blog-${slug}`,
        title: meta.title || slug,
        content: plainContent,
        tags: Array.isArray(meta.tags) ? meta.tags.join(' ') : (meta.tags || ''),
        type: 'blog',
        date: meta.date || '',
        url: `/blog/${slug}/`
      });
    } catch (err) {
      console.error(`Error processing blog post ${slug}:`, err.message);
    }
  }

  // Index learn lessons
  console.log('Indexing learn lessons...');
  const learnFiles = fs.readdirSync(LEARN_DIR).filter(file => 
    file.endsWith('.md') && file !== '_index.md'
  );
  console.log('Found', learnFiles.length, 'learn files');

  for (const file of learnFiles) {
    const filePath = path.join(LEARN_DIR, file);
    try {
      const raw = fs.readFileSync(filePath, 'utf8');
      const meta = parseFrontmatter(raw);
      const content = raw.replace(/^---[\s\S]*?---/, '').trim();
      
      // Strip HTML tags from content for better search
      const plainContent = stripTags(content);
      
      documents.push({
        id: `learn-${file.replace(/\.md$/, '')}`,
        title: meta.title || file.replace(/\.md$/, ''),
        content: plainContent,
        tags: Array.isArray(meta.tags) ? meta.tags.join(' ') : (meta.tags || ''),
        type: 'learn',
        date: meta.date || '',
        url: `/learn/${file.replace(/\.md$/, '')}/`
      });
    } catch (err) {
      console.error(`Error processing learn lesson ${file}:`, err.message);
    }
  }

  // Build the index
  console.log('Building lunr index with', documents.length, 'documents...');
  const index = lunr(function () {
    this.ref('id');
    this.field('title', { boost: 10 });
    this.field('content');
    this.field('tags');
    this.field('type');
    this.field('date');

    documents.forEach(doc => {
      this.add(doc);
    });
  });

  // Save index to file
  console.log('Saving search index...');
  const indexJSON = index.toJSON();
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'index.json'),
    JSON.stringify(indexJSON)
  );

  console.log(`Generated search index with ${documents.length} documents`);
  console.log('Index saved to:', path.join(OUTPUT_DIR, 'index.json'));
}

console.log('About to call generateSearchIndex()');
generateSearchIndex();
console.log('SEARCH INDEX SCRIPT COMPLETED');