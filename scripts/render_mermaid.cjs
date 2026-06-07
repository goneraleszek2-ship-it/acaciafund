const fs = require('fs');
const path = require('path');
const mermaid = require('mermaid');

// Minimal DOM for mermaid to work in Node.js
const { JSDOM } = require('jsdom');

async function renderMermaid() {
  const docsDir = path.join(__dirname, '..', 'docs');
  const outDir = path.join(__dirname, '..', 'static', 'images', 'diagrams');
  fs.mkdirSync(outDir, { recursive: true });

  mermaid.initialize({
    startOnLoad: false,
    theme: 'dark',
    themeVariables: {
      background: '#0f172a',
      primaryColor: '#1e3a5f',
      secondaryColor: '#2d5a8e',
      tertiaryColor: '#0f172a',
      primaryBorderColor: '#d97706',
      secondaryBorderColor: '#64748b',
      tertiaryBorderColor: '#334155',
      lineColor: '#64748b',
      textColor: '#e2e8f0',
      mainBkg: '#1e293b',
      nodeBorder: '#475569',
      clusterBkg: '#0f172a',
      clusterBorder: '#334155',
      titleColor: '#f1f5f9',
      edgeLabelBackground: '#1e293b',
    },
  });

  const mmdFiles = fs.readdirSync(docsDir).filter(f => f.endsWith('.mmd'));
  console.log(`Found ${mmdFiles.length} .mmd files`);

  for (const mmdFile of mmdFiles) {
    const mmdPath = path.join(docsDir, mmdFile);
    const svgName = mmdFile.replace('.mmd', '.svg');
    const svgPath = path.join(outDir, svgName);
    const mmdContent = fs.readFileSync(mmdPath, 'utf-8');

    try {
      const { svg } = await mermaid.render('mermaid-' + mmdFile.replace('.mmd', ''), mmdContent);
      fs.writeFileSync(svgPath, svg, 'utf-8');
      console.log(`  ✓ ${mmdFile} → ${svgName}`);
    } catch (err) {
      console.error(`  ✗ ${mmdFile}: ${err.message}`);
    }
  }
}

renderMermaid().catch(err => { console.error(err); process.exit(1); });
