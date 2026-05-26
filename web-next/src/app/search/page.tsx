'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import SearchBox from '@/components/SearchBox';
import lunr from 'lunr';

export default function SearchPage() {
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [index, setIndex] = useState<any>(null);

  useEffect(() => {
    // Load the search index
    async function loadIndex() {
      try {
        const res = await fetch('/search/index.json');
        if (!res.ok) throw new Error('Failed to load search index');
        const indexData = await res.json();
        setIndex(lunr.Index.load(indexData));
      } catch (err) {
        console.error('Error loading search index:', err);
      }
    }

    loadIndex();
  }, []);

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--text)] py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold tracking-tighter text-center text-white mb-8">
          Search
        </h1>
        <SearchBox 
          index={index}
          setResults={setResults}
          setLoading={setLoading}
          results={results}
          loading={loading}
        />
      </div>
    </div>
  );
}