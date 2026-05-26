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
      let value = kv[2].replace(/^["']|["']$/g, '');
        // Handle arrays (like tags)
        if (key === 'tags' && typeof value === 'string') {
          let parsedValue: string[] = [];
          if (value.startsWith('[')) {
            try {
              const parsed = JSON.parse(value);
              if (Array.isArray(parsed)) {
                parsedValue = parsed.map(item => item.trim().replace(/^["']|["']$/g, ''));
              } else {
                parsedValue = [String(parsed).trim().replace(/^["']|["']$/g, '')];
              }
            } catch {
              // If JSON parsing fails, treat as comma-separated
              parsedValue = value.split(',').map(item => item.trim().replace(/^["']|["']$/g, ''));
            }
          } else if (value.startsWith('-')) {
            // Handle YAML list format
            parsedValue = value
              .split('\n')
              .map(line => line.trim())
              .filter(line => line.startsWith('-'))
              .map(line => line.substring(1).trim());
          } else {
            // Handle comma-separated
            parsedValue = value.split(',').map(item => item.trim());
          }
          meta[key] = parsedValue;
        } else {
          meta[key] = value;
        }
    }
  }
  return meta;
}

function calculateReadingTime(text: string): number {
  const wordsPerMinute = 200;
  const wordCount = text.trim().split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}

export async function generateStaticParams() {
  const tagsSet = new Set<string>();
  const dirs = readdirSync(CONTENT_DIR).filter(d =>
    statSync(join(CONTENT_DIR, d)).isDirectory()
  );

  for (const slug of dirs) {
    const filePath = join(CONTENT_DIR, slug, 'index.md');
    try {
      const raw = readFileSync(filePath, 'utf8');
      const meta = parseFrontmatter(raw);
      if (Array.isArray(meta.tags)) {
        meta.tags.forEach((tag: string) => tagsSet.add(tag));
      }
    } catch {
      // Skip files that can't be read
    }
  }

  return Array.from(tagsSet).map(tag => ({ tag }));
}

export default async function TagPage({ params }: { params: Promise<{ tag: string }> }) {
  const { tag } = await params;
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
        
        // Check if this post has the tag
        const hasTag = Array.isArray(meta.tags) && meta.tags.includes(tag);
        if (!hasTag) return null;
        
        return { 
          slug, 
          title: meta.title || slug, 
          date: meta.date || '', 
          description: meta.description || '', 
          readingTime 
        };
      } catch {
        return null;
      }
    });

  // Filter out nulls and assert the type
  const posts = rawPosts.filter((post): post is { 
    slug: string; 
    title: string; 
    date: string; 
    description: string; 
    readingTime: number 
  } => post !== null);

  const sortedPosts = posts.sort((a, b) => b.date.localeCompare(a.date));

  if (sortedPosts.length === 0) {
    return (
      <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
        <h1 className="text-2xl font-bold tracking-tighter text-center text-white mb-8">
          No content found for tag: #{tag}
        </h1>
        <p className="text-center text-[var(--muted)]">
          Try browsing <Link href="/blog/" className="text-[var(--accent)] hover:underline">all syntheses</Link> instead.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
      <h1 className="text-2xl font-bold tracking-tighter text-center text-white mb-8">
        Content tagged with: <span className="text-[var(--accent)]">#{tag}</span>
      </h1>
      <p className="text-center text-[var(--muted)] mb-8">
        {sortedPosts.length} {sortedPosts.length === 1 ? 'synthesis' : 'syntheses'} found
      </p>
      <div className="grid gap-4 max-w-4xl mx-auto">
        {sortedPosts.map((post: any) => (
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
          </Link>
        ))}
      </div>
      <div className="mt-8 text-center">
        <Link href="/blog/" className="flex h-10 px-4 py-2 bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 rounded-lg transition-colors font-medium">
          Browse all syntheses
        </Link>
      </div>
    </div>
  );
}