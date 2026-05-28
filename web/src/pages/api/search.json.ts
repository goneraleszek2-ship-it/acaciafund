import { loadBlogPosts } from '../../lib/content.js';

export async function GET() {
  const posts = loadBlogPosts();
  // Map to searchable fields with boosted importance for title and tags
  const searchIndex = posts.map(post => ({
    id: post.slug,
    title: post.title,
    category: post.category,
    tags: post.tags,
    summary: post.summary,
    url: `/${post.lang}/blog/${post.slug}/`,
    lang: post.lang,
    // For fuzzy search, we'll create a combined searchable string
    searchableText: `${post.title} ${post.tags.join(' ')} ${post.summary} ${post.category}`
  }));

  return new Response(JSON.stringify(searchIndex, null, 2) + '\n', {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
}