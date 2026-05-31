import { z } from 'zod'

// Define the schema for our markdown frontmatter
export const contentFrontmatterSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  date: z.preprocess((arg) => {
    if (arg instanceof Date) return arg.toISOString().split('T')[0];
    return String(arg);
  }, z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Date must be in YYYY-MM-DD format')),
  description: z.string().optional(),
  author: z.string().default('AcaciaFund'),
  // Make categories optional for lesson content which uses tags instead
  categories: z.array(z.enum(['Science', 'Stock', 'AML', 'Markets'])).optional(),
  tags: z.array(z.string()).optional(),
  type: z.enum(['post', 'page', 'lesson']).default('post'),
  draft: z.boolean().default(false)
})

// Define schema for the full content object (frontmatter + body)
export const contentSchema = z.object({
  frontmatter: contentFrontmatterSchema,
  body: z.string(),
  slug: z.string()
})

// Validation function
export const validateContent = (data) => {
  const result = contentSchema.safeParse(data)
  if (!result.success) {
    throw new Error(`Content validation failed: ${result.error.message}`)
  }
  return result.data
}

// Helper to validate frontmatter only
export const validateFrontmatter = (data) => {
  const result = contentFrontmatterSchema.safeParse(data)
  if (!result.success) {
    throw new Error(`Frontmatter validation failed: ${result.error.message}`)
  }
  return result.data
}