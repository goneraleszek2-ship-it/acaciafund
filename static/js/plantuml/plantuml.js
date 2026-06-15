// PlantUML renderer using plantuml-server API
// Renders PlantUML diagrams by encoding and fetching SVG from plantuml.com

function renderPlantUML(element) {
    const code = element.textContent.trim();
    if (!code) return;
    
    // Encode PlantUML source
    const encoded = btoa(unescape(encodeURIComponent(code)));
    
    // Fetch SVG from plantuml-server
    fetch(`http://www.plantuml.com/plantuml/svg/${encoded}`)
        .then(response => response.text())
        .then(svg => {
            element.innerHTML = svg;
            element.classList.add('rendered');
        })
        .catch(err => {
            console.error('PlantUML render error:', err);
            element.innerHTML = `<pre style="color:red">Render failed: ${err.message}</pre>`;
        });
}

// Auto-render all PlantUML diagrams on page load
document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.plantuml');
    elements.forEach(renderPlantUML);
});
