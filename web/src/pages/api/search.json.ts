import { loadBlogPosts } from '../../lib/content.js';

export async function GET() {
  const posts = loadBlogPosts();
  // Map to searchable fields
  const searchIndex = posts.map(post => ({
    id: post.slug,
    title: post.title,
    category: post.category,
    tags: post.tags,
    summary: post.summary,
    url: `/${post.lang}/blog/${post.slug}/`,
    lang: post.lang
  }));

  return new Response(JSON.stringify(searchIndex, null, 2) + '\n', {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
  });
}