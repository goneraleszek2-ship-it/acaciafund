'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import lunr from 'lunr';

interface SearchBoxProps {
  index: ReturnType<typeof lunr.Index.load> | null;
  setResults: React.Dispatch<React.SetStateAction<any[]>>;
  setLoading: React.Dispatch<React.SetStateAction<boolean>>;
  results: any[];
  loading: boolean;
}

interface SearchResult {
  title: string;
  type: string;
  date: string;
  url: string;
  snippet: string;
}

export default function SearchBox({ index, setResults, setLoading, results, loading }: SearchBoxProps) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (!query.trim() || !index) {
      setResults([]);
      return;
    }

    setLoading(true);
    try {
      const results = index.search(query);
      // Fetch snippets for each result (simplified: we'll just show title and metadata)
      // In a more advanced implementation, we could highlight snippets
      setResults(
        results.map((result: any) => ({
          title: result.matchData.metadata.title?.[''] || 'Untitled',
          type: result.matchData.metadata.type?.[''] || '',
          date: result.matchData.metadata.date?.[''] || '',
          url: result.ref,
          snippet: '' // We don't have snippet in index, but we could store it
        }))
      );
    } catch (err) {
      console.error('Error searching:', err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, index]);

  if (loading) {
    return <div className="text-center py-4">Searching...</div>;
  }

  return (
    <div className="mb-6">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search syntheses and lessons..."
        className="w-full px-4 py-2 border border-[var(--card-border)]/50 rounded-lg bg-[var(--bg-elev)]/50 text-[var(--text)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]"
      />
      {results.length > 0 && (
        <div className="mt-4 space-y-2">
          <h3 className="text-lg font-medium text-[var(--accent)]">
            {results.length} result{results.length !== 1 ? 's' : ''}
          </h3>
          <div className="space-y-3">
            {results.map((result, idx) => (
              <div key={idx} className="p-3 bg-[var(--card)]/50 rounded-lg border border-[var(--card-border)]/50">
                <Link href={result.url} className="no-underline">
                  <h4 className="font-semibold text-white mb-1">{result.title}</h4>
                  <p className="text-sm text-[var(--muted)]">
                    {result.type === 'blog' ? 'Synthesis' : 'Lesson'} •
                    {result.date && `${result.date} • `}
                  </p>
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}
      {results.length === 0 && query.trim() !== '' && (
        <p className="text-center text-[var(--muted)] py-4">
          No results found for "{query}"
        </p>
      )}
    </div>
  );
}