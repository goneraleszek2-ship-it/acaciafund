import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import Link from 'next/link';

const CONTENT_DIR = join(process.cwd(), '../content/pl/blog');

function parseFrontmatter(raw: string) {
  const match = raw.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return {};
  const lines = match[1].split('\n');
  const meta: Record<string, string | string[]> = {};
  for (const line of lines) {
    const kv = line.match(/^(\w+):\s*(.+)$/);
    if (kv) {
      const key = kv[1];
      let value: string | string[] = kv[2].replace(/^["']|["']$/g, '');
      // Handle arrays (like tags, takeaways)
      if ((key === 'tags' || key === 'takeaways') && typeof value === 'string') {
        // Try to parse as JSON array
        if (value.startsWith('[')) {
          try {
            const parsed = JSON.parse(value);
            if (Array.isArray(parsed)) {
              value = parsed.map(item => String(item));
            }
          } catch {
            // ignore, keep as string
          }
        } else if (value.startsWith('-')) {
          // Handle YAML list format
          value = value
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.startsWith('-'))
            .map(line => line.substring(1).trim());
        } else {
          // Handle comma-separated
          if (value.includes(',')) {
            value = value.split(',').map(item => item.trim()).filter(Boolean);
          }
        }
      }
      meta[key] = value;
    }
  }
  return meta;
}

function calculateReadingTime(text: string): number {
  const wordsPerMinute = 200;
  const wordCount = text.trim().split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}

// Define the type for a blog post
type BlogPost = {
  slug: string;
  title: string;
  date: string;
  description: string;
  readingTime: number;
  tags: string[];
};

export default function BlogIndex() {
  const dirs = readdirSync(CONTENT_DIR).filter(d =>
    statSync(join(CONTENT_DIR, d)).isDirectory()
  );

  const rawPosts = dirs
    .map(slug => {
      const filePath = join(CONTENT_DIR, slug, 'index.md');
      try {
        const raw = readFileSync(filePath, 'utf8');
        const meta = parseFrontmatter(raw);
        const content = raw.replace(/^---[\s\S]*?---/, '').trim();
        const readingTime = calculateReadingTime(content);
        return { 
          slug, 
          title: meta.title || slug, 
          date: meta.date || '',
          description: meta.description || '',
          readingTime,
          tags: Array.isArray(meta.tags) ? meta.tags : []
        };
      } catch {
        return null;
      }
    });

  // Filter out nulls and assert the type to BlogPost[]
  const posts = rawPosts.filter((post): post is BlogPost => post !== null);

  const sortedPosts = posts.sort((a, b) => b.date.localeCompare(a.date));

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
      <h1 className="text-3xl font-bold tracking-tighter text-center text-white mb-8">All Syntheses</h1>
      <div className="grid gap-4 max-w-4xl mx-auto">
        {posts.map((post: BlogPost) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}/`}
            className="bg-[var(--card)]/50 backdrop-blur-sm rounded-xl p-6 border border-[var(--card-border)]/50 hover:bg-[var(--card)] transition-colors"
          >
            <h2 className="text-lg font-semibold text-white">{post.title}</h2>
            <div className="flex items-center gap-3 text-sm text-[var(--muted)] mt-1">
              <span>{post.date}</span>
              {post.date && <span>•</span>}
              <span>{post.readingTime} min read</span>
            </div>
            {post.description && <p className="text-sm text-[var(--muted)]/70 mt-1">{post.description}</p>}
            {post.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {post.tags.map((tag: string) => (
                  <span key={tag} className="px-2 py-0.5 bg-[var(--card)]/50 text-xs rounded text-[var(--muted)]">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </Link>
        ))}
      </div>
    </div>
  );
}