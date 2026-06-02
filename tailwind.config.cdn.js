module.exports = {
  content: ['./templates/**/*.j2'],
  theme: { extend: { typography: { DEFAULT: { css: { maxWidth: '72ch' } } } } },
  plugins: [require('@tailwindcss/typography')],
}
