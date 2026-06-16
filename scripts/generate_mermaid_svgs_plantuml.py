#!/usr/bin/env python3
"""
Generate SVG images for all Mermaid diagrams.
Uses a simple approach: convert MMD to PlantUML format and use plantuml command.
"""
import os
import re
import subprocess
from pathlib import Path

DOCS_DIR = Path("/root/acaciafund/docs")
OUTPUT_DIR = Path("/root/acaciafund/static/images/generated/knowledge")
DIAGRAMS = [
    "admin_panel",
    "build_sequence",
    "content_model",
    "dataops_pipeline",
    "module_interconnections",
    "pillar_taxonomy",
    "pipeline_quality",
    "rss_ingestion",
    "search_index",
    "source_framework",
    "source_ingestion",
    "system_architecture",
    "user_journey",
]

def remove_title_line(mmd_content):
    """Remove the title line from Mermaid content."""
    lines = mmd_content.strip().split('\n')
    return '\n'.join([l for l in lines if not l.startswith('title:')])

def mmd_to_plantuml_flowchart(mmd_content):
    """Convert Mermaid flowchart to PlantUML format."""
    lines = mmd_content.strip().split('\n')
    plantuml_lines = []
    plantuml_lines.append("@startuml")
    plantuml_lines.append("left to right direction")
    plantuml_lines.append("")
    
    current_subgraph = None
    subgraph_nodes = {}
    
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("style"):
            continue
        
        # Handle subgraph start
        subgraph_match = re.match(r'subgraph\s+(\w+)\s*\["?(.*?)"?\]', line)
        if subgraph_match:
            current_subgraph = subgraph_match.group(1)
            subgraph_label = subgraph_match.group(2).replace('<br/>', '\\n')
            subgraph_nodes[current_subgraph] = []
            plantuml_lines.append(f"package \"{subgraph_label}\" {{")
            continue
        
        # Handle subgraph end
        if line == "end":
            if current_subgraph:
                plantuml_lines.append("}")
                current_subgraph = None
            continue
        
        # Convert node definitions
        node_match = re.match(r'(\w+)\[(.+?)\]', line)
        if node_match:
            node_id = node_match.group(1)
            node_label = node_match.group(2).replace('<br/>', '\\n')
            if current_subgraph:
                subgraph_nodes[current_subgraph].append(node_id)
                plantuml_lines.append(f"  ({node_label})")
            else:
                plantuml_lines.append(f"({node_label}) as {node_id}")
            continue
        
        # Convert edges
        edge_match = re.match(r'(\w+)\s*-+>\s*(\w+)', line)
        if edge_match:
            src = edge_match.group(1)
            dst = edge_match.group(2)
            plantuml_lines.append(f"{src} --> {dst}")
    
    plantuml_lines.append("")
    plantuml_lines.append("@enduml")
    
    return '\n'.join(plantuml_lines)

def mmd_to_plantuml_sequence(mmd_content):
    """Convert Mermaid sequence diagram to PlantUML format."""
    lines = mmd_content.strip().split('\n')
    plantuml_lines = []
    plantuml_lines.append("@startuml")
    plantuml_lines.append("")
    
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("style"):
            continue
        
        # Convert actor
        actor_match = re.match(r'actor\s+(\w+)\s+as\s+(.+)', line)
        if actor_match:
            actor_id = actor_match.group(1)
            actor_label = actor_match.group(2).replace('<br/>', '\\n')
            plantuml_lines.append(f"actor {actor_label} as {actor_id}")
            continue
        
        # Convert participant
        participant_match = re.match(r'participant\s+(\w+)\s+as\s+(.+)', line)
        if participant_match:
            participant_id = participant_match.group(1)
            participant_label = participant_match.group(2).replace('<br/>', '\\n')
            plantuml_lines.append(f"participant {participant_label} as {participant_id}")
            continue
        
        # Convert message
        if "-->" in line or "->" in line or "--" in line:
            plantuml_lines.append(line.replace('<br/>', '\\n'))
    
    plantuml_lines.append("")
    plantuml_lines.append("@enduml")
    
    return '\n'.join(plantuml_lines)

def mmd_to_plantuml_mindmap(mmd_content):
    """Convert Mermaid mindmap to PlantUML format."""
    lines = mmd_content.strip().split('\n')
    plantuml_lines = []
    plantuml_lines.append("@startuml")
    plantuml_lines.append("title")
    
    title_line = lines[0] if lines else ""
    if title_line.startswith("title:"):
        plantuml_lines.append(title_line[7:].strip())
    else:
        plantuml_lines.append("Mindmap")
    
    plantuml_lines.append("end title")
    plantuml_lines.append("")
    plantuml_lines.append("root")
    plantuml_lines.append("  root")
    
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("style"):
            continue
        
        # Count indentation
        indent = len(line) - len(line.lstrip())
        node = line.strip()
        
        # Convert to hierarchy
        if indent == 0:
            plantuml_lines.append(f"    {node}")
        elif indent == 2:
            plantuml_lines.append(f"      {node}")
        elif indent == 4:
            plantuml_lines.append(f"        {node}")
        elif indent == 6:
            plantuml_lines.append(f"          {node}")
        elif indent == 8:
            plantuml_lines.append(f"            {node}")
    
    plantuml_lines.append("")
    plantuml_lines.append("@enduml")
    
    return '\n'.join(plantuml_lines)

def mmd_to_plantuml_class(mmd_content):
    """Convert Mermaid class diagram to PlantUML format."""
    lines = mmd_content.strip().split('\n')
    plantuml_lines = []
    plantuml_lines.append("@startuml")
    plantuml_lines.append("")
    
    current_class = None
    
    for line in lines[1:]:
        line = line.strip()
        if not line or line.startswith("style"):
            continue
        
        # Convert class definition
        class_match = re.match(r'class\s+(\w+)\s*\{', line)
        if class_match:
            class_name = class_match.group(1)
            plantuml_lines.append(f"class {class_name} {{")
            current_class = class_name
            continue
        
        if line == "}" and current_class:
            plantuml_lines.append("}")
            current_class = None
            continue
        
        # Convert relationships
        if "-->" in line or "..>" in line:
            plantuml_lines.append(line.replace('<br/>', '\\n'))
    
    plantuml_lines.append("")
    plantuml_lines.append("@enduml")
    
    return '\n'.join(plantuml_lines)

def generate_svg_with_plantuml(mmd_content, output_path, diagram_name):
    """Generate SVG using PlantUML."""
    # Detect diagram type
    if 'flowchart' in mmd_content and 'sequenceDiagram' not in mmd_content:
        diagram_type = 'flowchart'
        plantuml_content = mmd_to_plantuml_flowchart(mmd_content)
    elif 'sequenceDiagram' in mmd_content:
        diagram_type = 'sequence'
        plantuml_content = mmd_to_plantuml_sequence(mmd_content)
    elif 'classDiagram' in mmd_content:
        diagram_type = 'class'
        plantuml_content = mmd_to_plantuml_class(mmd_content)
    elif 'mindmap' in mmd_content:
        diagram_type = 'mindmap'
        plantuml_content = mmd_to_plantuml_mindmap(mmd_content)
    elif 'stateDiagram' in mmd_content:
        diagram_type = 'state'
        plantuml_content = mmd_to_plantuml_state(mmd_content)
    else:
        diagram_type = 'flowchart'
        plantuml_content = mmd_to_plantuml_flowchart(mmd_content)
    
    print(f"  Detected type: {diagram_type}")
    
    # Save to temp file
    temp_path = Path(f"/tmp/{diagram_name}.puml")
    temp_path.write_text(plantuml_content)
    
    try:
        result = subprocess.run(
            ['/usr/bin/plantuml', '-tsvg', str(temp_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # PlantUML outputs to same directory as input
        svg_path = temp_path.with_suffix('.svg')
        
        if result.returncode == 0 and svg_path.exists():
            # Move to output directory
            svg_path.rename(output_path)
            print(f"  ✓ Generated with PlantUML: {output_path.name}")
            return True
        else:
            print(f"  ✗ PlantUML failed: {result.stderr[:200] if result.stderr else 'No error'}")
            # Print PlantUML content for debugging
            print(f"  PlantUML content:\n{plantuml_content[:500]}")
            return False
            
    except FileNotFoundError:
        print("  ✗ plantuml command not found")
        return False
    except subprocess.TimeoutExpired:
        print("  ✗ PlantUML timed out")
        return False
    finally:
        # Cleanup temp files
        if temp_path.exists():
            temp_path.unlink()
        svg_path = temp_path.with_suffix('.svg')
        if svg_path.exists():
            svg_path.unlink()
        png_path = temp_path.with_suffix('.png')
        if png_path.exists():
            png_path.unlink()

def main():
    """Main function to generate all SVGs."""
    print("=" * 60)
    print("Mermaid Diagram to SVG Converter (via PlantUML)")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for plantuml
    try:
        result = subprocess.run(['/usr/bin/plantuml', '-version'], capture_output=True, text=True)
        if result.returncode == 0 or result.returncode == 254:
            print("✓ PlantUML is available")
        else:
            print("✗ PlantUML not available")
            return 1
    except FileNotFoundError:
        print("✗ plantuml command not found")
        return 1
    
    # Process each diagram
    success_count = 0
    fail_count = 0
    
    for diagram in DIAGRAMS:
        mmd_path = DOCS_DIR / f"{diagram}.mmd"
        svg_path = OUTPUT_DIR / f"{diagram}.svg"
        
        print(f"\nProcessing: {diagram}.mmd")
        
        if not mmd_path.exists():
            print(f"  ✗ File not found: {mmd_path}")
            fail_count += 1
            continue
        
        mmd_content = mmd_path.read_text()
        
        if generate_svg_with_plantuml(mmd_content, svg_path, diagram):
            success_count += 1
        else:
            fail_count += 1
    
    print("\n" + "=" * 60)
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print("=" * 60)
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
