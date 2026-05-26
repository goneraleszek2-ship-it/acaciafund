import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import Quiz from '@/components/Quiz';
import { marked } from 'marked';

const CONTENT_DIR = join(process.cwd(), '../content/pl/learn');

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

export const generateStaticParams = () => {
  const entries = readdirSync(CONTENT_DIR);
  return entries
    .filter(f => f.endsWith('.md') && f !== '_index.md')
    .map(f => ({ slug: f.replace(/\.md$/, '') }));
};

export default async function LearnPage({ params }: { params: { slug: string } }) {
  const { slug } = await params;
  const filePath = join(CONTENT_DIR, `${slug}.md`);
  let rawContent = '';
  try {
    rawContent = readFileSync(filePath, 'utf8');
  } catch {
    rawContent = '# Lesson not found\n\n---\n';
  }
  
  const meta = parseFrontmatter(rawContent);
  let content = rawContent.replace(/^---[\s\S]*?---/, '').trim();
  // Wrap images in a link to themselves: ![alt](url) => [![alt](url)](url)
  const processedMarkdown = content.replace(/!\[(.*?)\]\((.*?)\)/g, '[$&]($2)');
  const renderedContent = marked(processedMarkdown);
  const readingTime = calculateReadingTime(content);
  
  return (
    <article className="prose lg:prose-xl mx-auto py-8 prose-invert">
      <header className="mb-6">
        <h1 className="text-2xl font-bold tracking-tighter text-white">{meta.title || slug}</h1>
          <div className="flex flex-wrap gap-4 text-sm text-[var(--muted)]">
            <span>{meta.date || ''}</span>
            {meta.date && <span>•</span>}
            <span>{readingTime} min read</span>
            {meta.difficulty && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium">
                {meta.difficulty === 'easy' && <span className="bg-green-900/20 text-green-400">Easy</span>}
                {meta.difficulty === 'medium' && <span className="bg-yellow-900/20 text-yellow-400">Medium</span>}
                {meta.difficulty === 'hard' && <span className="bg-red-900/20 text-red-400">Hard</span>}
              </span>
            )}
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
        <blockquote className="mb-6 p-4 border-l-4 border-[var(--accent-2)]/50 bg-[var(--accent-2)]/5">
          <p className="text-[var(--muted)] italic">{meta.tldr}</p>
        </blockquote>
      )}
      
      <div dangerouslySetInnerHTML={{ __html: renderedContent }} />
      
      {meta.takeaways && (
        <section className="mt-8 pt-4 border-t border-[var(--card-border)]/50">
          <h3 className="text-lg font-semibold text-[var(--accent-2)] mb-4">Key Takeaways</h3>
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
      
      <section className="mt-8 pt-4 border-t border-[var(--card-border)]/50">
        <h3 className="text-lg font-semibold text-[var(--accent-2)] mb-4">Quiz</h3>
        <Quiz />
      </section>
    </article>
  );
}