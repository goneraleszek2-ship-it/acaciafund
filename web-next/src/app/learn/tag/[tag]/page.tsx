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
      let value: string | string[] = kv[2].replace(/^["']|["']$/g, '');
      // Handle arrays (like tags, takeaways)
      if ((key === 'tags' || key === 'takeaways') && typeof value === 'string') {
        let parsedValue: string[] = [];
        if (value.startsWith('[')) {
          // Handle array format: ["tag1", "tag2"]
          try {
            parsedValue = JSON.parse(value);
            if (!Array.isArray(parsedValue)) {
              parsedValue = [String(parsedValue)];
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
        value = parsedValue;
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

export async function generateStaticParams() {
  const tagsSet = new Set<string>();
  const files = readdirSync(CONTENT_DIR).filter(f =>
    f.endsWith('.md') && f !== '_index.md'
  );

  for (const file of files) {
    const filePath = join(CONTENT_DIR, file);
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
  const files = readdirSync(CONTENT_DIR).filter(f =>
    f.endsWith('.md') && f !== '_index.md'
  );

  const lessons = files
    .map(file => {
      const filePath = join(CONTENT_DIR, file);
      try {
        const raw = readFileSync(filePath, 'utf8');
        const meta = parseFrontmatter(raw);
        const content = raw.replace(/^---[\s\S]*?---/, '').trim();
        const readingTime = calculateReadingTime(content);
        
        // Check if this lesson has the tag
        const hasTag = Array.isArray(meta.tags) && meta.tags.includes(tag);
        if (!hasTag) return null;
        
        const slug = file.replace(/\.md$/, '');
        return { slug, title: meta.title || slug, difficulty: meta.difficulty || 'medium', date: meta.date || '', readingTime };
      } catch {
        return null;
      }
    })
    .filter(Boolean);

  if (lessons.length === 0) {
    return (
      <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
        <h1 className="text-2xl font-bold tracking-tighter text-center text-white mb-8">
          No lessons found for tag: #{tag}
        </h1>
        <p className="text-center text-[var(--muted)]">
          Try browsing <Link href="/learn/" className="text-[var(--accent)] hover:underline">all lessons</Link> instead.
        </p>
      </div>
    );
  }

  const diffColor: Record<string, string> = {
    easy: 'text-green-400',
    medium: 'text-yellow-400',
    hard: 'text-red-400',
  };

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
      <h1 className="text-2xl font-bold tracking-tighter text-center text-white mb-8">
        Lessons tagged with: <span className="text-[var(--accent)]">#{tag}</span>
      </h1>
      <p className="text-center text-[var(--muted)] mb-8">
        {lessons.length} {lessons.length === 1 ? 'lesson' : 'lessons'} found
      </p>
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
              </div>
            </div>
          </Link>
        ))}
      </div>
      <div className="mt-8 text-center">
        <Link href="/learn/" className="flex h-10 px-4 py-2 bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 rounded-lg transition-colors font-medium">
          Browse all lessons
        </Link>
      </div>
    </div>
  );
}