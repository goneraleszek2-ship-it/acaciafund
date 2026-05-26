import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import Link from 'next/link';
import { marked } from 'marked';

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

// Helper to get all posts metadata
function getAllPosts() {
  const posts = readdirSync(CONTENT_DIR)
    .filter(dirName => statSync(join(CONTENT_DIR, dirName)).isDirectory())
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
          tags: Array.isArray(meta.tags) ? meta.tags : [],
          frontmatter: meta
        };
      } catch {
        return null;
      }
    })
    .filter(Boolean);
  return posts;
}

// Function to find related posts based on shared tags
function getRelatedPosts(currentSlug: string, allPosts: any[], limit = 2) {
  const currentPost = allPosts.find(p => p.slug === currentSlug);
  if (!currentPost) return [];
  
  const currentTags = new Set(Array.isArray(currentPost.tags) ? currentPost.tags : []);
  
  // Score posts by number of shared tags
  const scored = allPosts
    .filter(p => p.slug !== currentSlug) // Exclude current post
    .map(post => {
      const postTags = new Set(Array.isArray(post.tags) ? post.tags : []);
      let sharedTags = 0;
      postTags.forEach(tag => {
        if (currentTags.has(tag)) sharedTags++;
      });
      return { ...post, sharedTags };
    })
    .filter(post => post.sharedTags > 0) // Only those with at least one shared tag
    .sort((a, b) => b.sharedTags - a.sharedTags) // Most shared tags first
    .slice(0, limit);
  
  return scored;
}

export const generateStaticParams = () => {
  const dirs = readdirSync(CONTENT_DIR);
  return dirs
    .filter(dirName => statSync(join(CONTENT_DIR, dirName)).isDirectory())
    .map(dirName => ({ slug: dirName }));
};

export default async function BlogPost({ params }: { params: { slug: string } }) {
  const { slug } = await params;
  const filePath = join(CONTENT_DIR, slug, 'index.md');
  let rawContent = '';
  try {
    rawContent = readFileSync(filePath, 'utf8');
  } catch {
    rawContent = '# Post not found\n\n---\n';
  }
  
  const meta = parseFrontmatter(rawContent);
  let content = rawContent.replace(/^---[\s\S]*?---/, '').trim();
  // Wrap images in a link to themselves: ![alt](url) => [![alt](url)](url)
  const processedMarkdown = content.replace(/!\[(.*?)\]\((.*?)\)/g, '[$&]($2)');
  const renderedContent = marked(processedMarkdown);
  const readingTime = calculateReadingTime(content);
  
  // Get all posts for related content
  const allPosts = getAllPosts();
  const relatedPosts = getRelatedPosts(slug, allPosts, 2);
  
  return (
    <article className="prose lg:prose-xl mx-auto py-8 prose-invert">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tighter text-white">{meta.title || slug}</h1>
          <div className="flex flex-wrap gap-4 text-sm text-[var(--muted)]">
            <span>{meta.date || ''}</span>
            {meta.date && <span>•</span>}
            <span>{readingTime} min read</span>
            {Array.isArray(meta.tags) && (
              <div className="flex flex-wrap gap-1">
                {meta.tags.map((tag: string) => (
                  <span key={tag} className="px-2 py-0.5 bg-[var(--card)]/50 text-xs rounded text-[var(--muted)]">
                    #{tag}
                  </span>
                ))}
              </div>
            )}
          </div>
      </header>
      
      {meta.tldr && (
        <blockquote className="mb-6 p-4 border-l-4 border-[var(--accent)]/50 bg-[var(--accent)]/5">
          <p className="text-[var(--muted)] italic">{meta.tldr}</p>
        </blockquote>
      )}
      
      <div dangerouslySetInnerHTML={{ __html: renderedContent }} />
      
      {meta.takeaways && (
        <section className="mt-8 pt-4 border-t border-[var(--card-border)]/50">
          <h3 className="text-lg font-semibold text-[var(--accent)] mb-4">Key Takeaways</h3>
          <ul className="list-disc list-inside space-y-2 text-[var(--muted)]">
            {Array.isArray(meta.takeaways) ? 
              meta.takeaways.map((takeaway, index) => (
                <li key={index}>{takeaway}</li>
              )) : 
              null
            }
          </ul>
        </section>
      )}
      
      {relatedPosts.length > 0 && (
        <section className="mt-10 pt-6 border-t border-[var(--card-border)]/50">
          <h3 className="text-lg font-semibold text-[var(--accent)] mb-4">Related Syntheses</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            {relatedPosts.map((post: any) => (
              <Link
                key={post.slug}
                href={`/blog/${post.slug}/`}
                className="bg-[var(--card)]/50 backdrop-blur-sm rounded-xl p-4 border border-[var(--card-border)]/50 hover:bg-[var(--card)] transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    <span className="text-xs font-medium">{post.date}</span>
                  </div>
                  <div>
                    <h4 className="font-semibold text-white">{post.title}</h4>
                    <p className="text-sm text-[var(--muted)]/70 mt-1">
                      {post.date} • {post.readingTime} min read
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}
    </article>
  );
}