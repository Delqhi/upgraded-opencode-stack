# /gen-thumbnail Fixtures & Rubric

This directory contains reference materials and evaluation criteria for the `/gen-thumbnail` skill.

## Contents
- `reference-blog-01.png`: Reference image showcasing the desired style.
- `rubric.json`: Scoring criteria to objectively evaluate generated thumbnails.

## Evaluation Criteria
- `aspect_ratio`: must be 16:9 (1920x1080)
- `mascot_position`: character should occupy ~40% left side
- `text_layout`: large angled text on right side ("AUTO" white, "PROFIT?" yellow)
- `sub_badge`: dark rounded rectangle with sub-text at bottom
- `laptop_element`: laptop with green chart and "$$$" bottom-right
- `arrow_element`: yellow curved arrow connecting text to laptop
- `background`: dark with green glow, no logos/watermarks
- `overall_composition`: professional YouTube thumbnail quality

Use `rubric.json` to score generated outputs programmatically or manually.
