import type { NextConfig } from 'next';
import { withMDX } from '@next/mdx';

const nextConfig: NextConfig = {
  // Configure `pageExtensions` to include MDX files
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'md', 'mdx'],
  // If you want to use `output: 'export'` for static export
  output: 'export',
};

export default withMDX(nextConfig);
