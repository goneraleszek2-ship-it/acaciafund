import { marked } from 'marked';
import { readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { readFile } from 'node:fs/promises';

const CONTENT_DIR = join(process.cwd(), '../content/pl/learn');

export const generateStaticParams = () => {
  const dirs = readdirSync(CONTENT_DIR);
  return dirs
    .filter(dirName => statSync(join(CONTENT_DIR, dirName)).isDirectory())
    .map(dirName => ({ slug: dirName }));
};

export default async function LearnPost({ params }: { params: { slug: string } }) {
  const { slug } = await params;
  const filePath = join(CONTENT_DIR, slug, 'index.md');
  const content = await readFile(filePath, 'utf8');
  return (
    <article className="prose lg:prose-xl mx-auto py-8">
      <div dangerouslySetInnerHTML={{ __html: marked(content) }} />
    </article>
  );
}
