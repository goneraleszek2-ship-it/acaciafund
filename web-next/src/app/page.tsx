import Link from "next/link";
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

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

function getAllPosts() {
  const dirs = readdirSync(CONTENT_DIR).filter(d =>
    statSync(join(CONTENT_DIR, d)).isDirectory()
  );

   const posts = dirs
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
     })
     .filter((post): post is { 
       slug: string; 
       title: string; 
       date: string; 
       description: string; 
       readingTime: number;
       tags: string[]
     } => post !== null)
     .sort((a, b) => {
       const dateA = a.date || '';
       const dateB = b.date || '';
       return dateB.localeCompare(dateA);
     });

  return posts;
}

export default function Home() {
  const latestPosts = getAllPosts().slice(0, 3);

  return (
    <div className="min-h-[100vh] flex flex-col bg-gradient-to-br from-black/90 to-black/100 text-[var(--text)] antialiased">
      {/* Hero Section */}
      <section className="flex-0 flex flex-col items-center justify-center py-16 px-6 sm:py-24 sm:px-8 bg-gradient-to-br from-black via-black/90 to-black/100">
        <div className="flex w-[100px] h-[20px] items-center justify-center">
          <span className="text-2xl font-bold text-[var(--accent)]">◆</span>
        </div>
        <h1 className="mt-4 text-4xl font-bold tracking-tighter text-white sm:text-5xl">
          Daily synthesis for AML, markets and science.
        </h1>
        <p className="mt-2 max-w-2xl text-center text-[var(--muted)] sm:text-lg">
          AcaciaFund turns HN and arXiv into structured research, with metadata, manifests, and local-first learning. This Astro version is the clean cutover path from Hugo to a smaller, more reliable deployment model.
        </p>
        <div className="mt-6 flex flex-wrap gap-4 justify-center">
          <Link href="/blog/" className="flex h-10 px-4 py-2 bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 rounded-lg transition-colors font-medium">
            Explore synthesis
          </Link>
          <Link href="/learn/" className="flex h-10 px-4 py-2 bg-[var(--accent-2)]/20 text-[var(--accent-2)] hover:bg-[var(--accent-2)]/30 rounded-lg transition-colors font-medium">
            Open learning hub
          </Link>
          <Link href="/about/" className="flex h-10 px-4 py-2 bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 rounded-lg transition-colors font-medium">
            About AcaciaFund
          </Link>
        </div>
      </section>

      {/* Pillars Section */}
      <section className="py-16 px-6 sm:py-24 sm:px-8">
        <h2 className="mb-6 text-3xl font-bold tracking-tighter text-center text-white">
          Pillars of Research
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          <div className="bg-[var(--card)]/50 backdrop-blur-sm rounded-2xl p-6 border border-[var(--card-border)]/50">
            <h3 className="mt-2 text-xl font-semibold text-[var(--accent-2)]">AML</h3>
            <p className="mt-2 text-[var(--muted)]">Compliance, financial crime and regulatory intelligence.</p>
            <p className="mt-1 text-xs text-[var(--muted)]/70">Latest bundle: 2026-05-23-aml</p>
          </div>
          <div className="bg-[var(--card)]/50 backdrop-blur-sm rounded-2xl p-6 border border-[var(--card-border)]/50">
            <h3 className="mt-2 text-xl font-semibold text-[var(--accent)]">Markets</h3>
            <p className="mt-2 text-[var(--muted)]">Semiconductors, capital markets and supply-chain signals.</p>
            <p className="mt-1 text-xs text-[var(--muted)]/70">Latest bundle: 2026-05-23-stock</p>
          </div>
          <div className="bg-[var(--card)]/50 backdrop-blur-sm rounded-2xl p-6 border border-[var(--card-border)]/50">
            <h3 className="mt-2 text-xl font-semibold text-[var(--accent-2)]">Science</h3>
            <p className="mt-2 text-[var(--muted)]">Complex systems, cognition and frontier research.</p>
            <p className="mt-1 text-xs text-[var(--muted)]/70">Latest bundle: 2026-05-23-science</p>
          </div>
        </div>
      </section>

      {/* Latest Syntheses Section */}
      <section className="py-16 px-6 sm:py-24 sm:px-8 bg-[var(--bg-elev)]/50">
        <h2 className="mb-6 text-3xl font-bold tracking-tighter text-center text-white">
          Latest syntheses
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          {latestPosts.map((post) => (
            <div key={post.slug} className="bg-[var(--card)]/50 backdrop-blur-sm rounded-2xl p-6 border border-[var(--card-border)]/50">
              <h3 className="mt-2 text-xl font-semibold text-white">{post.title}</h3>
              <p className="mt-2 text-[var(--muted)]">{post.description}</p>
              <Link href={`/blog/${post.slug}/`} className="inline-flex mt-4 items-center gap-2 text-[var(--accent)] font-medium hover:underline">
                Read synthesis
                <span className="transition-transform duration-200 group-hover:translate-x-0.5">--&gt;</span>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="py-16 px-6 sm:py-24 sm:px-8 text-center">
        <h2 className="mb-4 text-2xl font-bold tracking-tighter text-white">Join the research revolution</h2>
        <p className="mb-6 max-w-xl text-[var(--muted)]">
          Become part of a community that values judgment over prediction, privacy over surveillance, and learning over noise.
        </p>
        <div className="flex flex-wrap gap-4 justify-center">
          <Link href="/blog/" className="flex h-10 px-4 py-2 bg-[var(--accent)]/20 text-[var(--accent)] hover:bg-[var(--accent)]/30 rounded-lg transition-colors font-medium">
            Explore all research
          </Link>
          <Link href="/learn/" className="flex h-10 px-4 py-2 bg-[var(--accent-2)]/20 text-[var(--accent-2)] hover:bg-[var(--accent-2)]/30 rounded-lg transition-colors font-medium">
            Start learning
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 sm:py-16 sm:px-8 border-t border-[var(--card-border)]/50">
        <p className="text-center text-[var(--muted)] text-sm">
          AcaciaFund · static-first research and learning platform
        </p>
      </footer>
    </div>
  );
}