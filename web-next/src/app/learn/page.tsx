import { readdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import Link from 'next/link';

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
      let value = kv[2].replace(/^["']|["']$/g, '');
      // Handle arrays (like tags)
      if (key === 'tags' && typeof value === 'string') {
        let processedValue: string[] = [];
        if (value.startsWith('[')) {
          try {
            const parsed = JSON.parse(value);
            if (Array.isArray(parsed)) {
              processedValue = parsed.map(item => item.trim().replace(/^["']|["']$/g, ''));
            } else {
              processedValue = [String(parsed).trim().replace(/^["']|["']$/g, '')];
            }
          } catch {
            // If JSON parsing fails, treat as comma-separated
            processedValue = value.split(',').map(item => item.trim().replace(/^["']|["']$/g, ''));
          }
        } else if (value.startsWith('-')) {
          // Handle YAML list format
          processedValue = value
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.startsWith('-'))
            .map(line => line.substring(1).trim());
        } else {
          // Handle comma-separated or plain string
          if (value.includes(',')) {
            processedValue = value.split(',').map(item => item.trim().replace(/^["']|["']$/g, ''));
          } else {
            const trimmed = value.trim();
            if (trimmed) {
              processedValue = [trimmed];
            } else {
              processedValue = [];
            }
          }
        }
        meta[key] = processedValue;
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

export default function LearnIndex() {
  const lessons = readdirSync(CONTENT_DIR)
    .filter(f => f.endsWith('.md') && f !== '_index.md')
    .map(slug => {
      const filePath = join(CONTENT_DIR, slug);
      try {
        const raw = readFileSync(filePath, 'utf8');
        const meta = parseFrontmatter(raw);
        const content = raw.replace(/^---[\s\S]*?---/, '').trim();
        const readingTime = calculateReadingTime(content);
        return { 
          slug: slug.replace(/\.md$/, ''), 
          title: meta.title || slug, 
          difficulty: meta.difficulty || 'medium',
          date: meta.date || '',
          tldr: meta.tldr || '',
          readingTime,
          tags: Array.isArray(meta.tags) ? meta.tags : []
        };
      } catch {
        return null;
      }
    })
    .filter(Boolean);

  const diffColor: Record<string, string> = {
    easy: 'text-green-400',
    medium: 'text-yellow-400',
    hard: 'text-red-400',
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
      <h1 className="text-3xl font-bold tracking-tighter text-center text-white mb-8">Learning Hub</h1>
      <div className="grid gap-4 max-w-4xl mx-auto">
        {lessons.map((lesson: any) => (
          <Link
            key={lesson.slug}
            href={`/learn/${lesson.slug}/`}
            className="bg-[var(--card)]/50 backdrop-blur-sm rounded-xl p-6 border border-[var(--card-border)]/50 hover:bg-[var(--card)] transition-colors"
          >
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                <span className={`text-xs font-medium mt-0.5 inline-block ${diffColor[lesson.difficulty] || 'text-[var(--muted)]'}`}>
                  {lesson.difficulty}
                </span>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">{lesson.title}</h2>
                <div className="flex items-center gap-3 text-sm text-[var(--muted)] mt-1">
                  <span>{lesson.date}</span>
                  {lesson.date && <span>•</span>}
                  <span>{lesson.readingTime} min read</span>
                </div>
                {lesson.tldr && (
                  <p className="text-sm text-[var(--muted)]/70 mt-1">{lesson.tldr}</p>
                )}
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}