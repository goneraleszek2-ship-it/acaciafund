import { loadBlogPosts, loadRegistry } from '../../lib/content.js';

export async function GET() {
  const registry = loadRegistry();
  const posts = loadBlogPosts();
  const counts = { AML: 0, Markets: 0, Science: 0 };

  for (const post of posts) {
    if (Object.prototype.hasOwnProperty.call(counts, post.category)) {
      counts[post.category] += 1;
    }
  }

  const payload = {
    site: {
      title: 'AcaciaFund',
      url: 'https://acaciafund.org/',
      language: 'pl',
      buildDate: new Date().toISOString(),
    },
    stats: {
      totalPosts: posts.length,
      pillars: {
        AML: { count: counts.AML },
        Markets: { count: counts.Markets },
        Science: { count: counts.Science },
      },
    },
    recentPosts: posts.slice(0, 10).map((post) => ({
      title: post.title,
      url: `/blog/${post.slug}/`,
      date: String(post.date).slice(0, 10),
      category: post.category,
      sqi: post.sqi || 0,
    })),
    registry: {
      latestRunId: registry.latest_run_id || '',
      generatedAt: registry.generated_at || '',
      counts: registry.counts || { pages: 0, runs: 0, pillars: {} },
    },
  };

  return new Response(JSON.stringify(payload, null, 2) + '\n', {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
}
