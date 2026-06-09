"""Live integration tests: run full generator, verify new features in output."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_new_features_in_generated_output():
    from generator import main
    assert main() == 0
    from config import OUTPUT_DIR as out

    # 1. Visual fingerprint SVG + layer badge on learn page
    learn_html = (out / "learn" / "aml-basics" / "index.html").read_text(encoding="utf-8")
    assert 'viewBox="0 0 120 32"' in learn_html
    assert "Learn" in learn_html

    # 2. Fingerprint + layer badge on research page
    research_html = (out / "blog" / "2026-11-16-2027-data-engineering-predictions" / "index.html").read_text(encoding="utf-8")
    assert 'viewBox="0 0 120 32"' in research_html
    assert "Research" in research_html

    # 3. Fingerprint + layer badge on knowledge page
    knowledge_html = (out / "knowledge" / "dataops-glossary" / "index.html").read_text(encoding="utf-8")
    assert 'viewBox="0 0 120 32"' in knowledge_html
    assert "Knowledge" in knowledge_html

    # 4. Related Lessons section on research page
    assert "Related Lessons" in research_html

    # 5. Related Research section on learn page
    assert "Related Research" in learn_html

    # 6. SM-2 quiz hook on learn page with questions
    assert 'data-quiz-lesson="learn/aml-basics"' in learn_html
    assert "acacia_sm2_v1" in learn_html

    # 7. Learning path cards on /learn/ index
    li_html = (out / "learn" / "index.html").read_text(encoding="utf-8")
    assert "Anti-Money Laundering" in li_html
    assert "Financial Markets" in li_html
    assert "Data Engineering" in li_html

    # 8. Quiz JSON is valid on a learn page with bloom_questions
    import re
    m = re.search(r"data-quiz='({.+?})'", learn_html)
    assert m, "data-quiz attribute found"
    quiz = json.loads(m.group(1))
    assert len(quiz["questions"]) > 0

    # 9. GaC visuals exist on research articles
    gac_count = 0
    for fpath in sorted(out.glob("blog/*/index.html"))[:5]:
        html = fpath.read_text(encoding="utf-8")
        if "gac-timeline" in html or "gac-entities" in html or "gac-numbers" in html:
            gac_count += 1
    assert gac_count >= 1, "At least one research page has GaC visuals"
