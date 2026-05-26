const marked = require('marked');

/**
 * Render markdown with clickable images (wrapping images in a link to the image itself).
 * @param {string} markdown - The markdown string to render.
 * @returns {string} The rendered HTML.
 */
function renderMarkdownWithClickableImages(markdown) {
  // First, wrap images in a link to themselves: ![alt](url) => [![alt](url)](url)
  const processedMarkdown = markdown.replace(/!\[(.*?)\]\((.*?)\)/g, '[$&]($2)');

  // Then, render the markdown to HTML
  return marked(processedMarkdown);
}

module.exports = renderMarkdownWithClickableImages;