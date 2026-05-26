import marked from 'marked';

/**
 * Custom marked renderer that wraps images in a link to the image itself
 * (opening in a new tab). This makes images clickable.
 */
export function renderMarkdownWithClickableImages(markdown) {
  const renderer = new marked.Renderer();

  const originalImage = renderer.image;
  renderer.image = (href, title, alt) => {
    // Wrap the image in a link that opens the image in a new tab
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" style="display: inline-block;">${originalImage.call(renderer, href, title, alt)}</a>`;
  };

  return marked.parse(markdown, { renderer });
}

export default renderMarkdownWithClickableImages;