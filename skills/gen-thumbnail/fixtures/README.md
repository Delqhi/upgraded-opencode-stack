# Thumbnail Quality Rubric

This directory contains the fixture and rubric for evaluating `/gen-thumbnail` output.

## Files

- `reference-blog-01.png` — target composition reference image
- `rubric.json` — objective scoring criteria
- This README

## Rubric Criteria

The `rubric.json` defines 8 criteria that a generated thumbnail must satisfy:

1. **aspect_ratio**: Must be exactly 16:9 (1920x1080 pixels)
2. **mascot_position**: Character occupies ~40% of left side; 3D spherical white character with green mask, holding money fan
3. **text_layout**: Large angled text on right side: "AUTO" (white) + "PROFIT?" (yellow)
4. **sub_badge**: Dark rounded rectangle with text "AI AGENT MAKES MONEY ALONE" placed at bottom
5. **laptop_element**: Bottom-right: laptop with green chart and "$$$"
6. **arrow_element**: Yellow curved arrow connecting text area to laptop
7. **background**: Dark background with green glow, no logos or watermarks
8. **overall_composition**: Professional YouTube thumbnail quality

## Usage

When generating thumbnails, programmatically validate each criterion against the output. The reference image serves as the visual benchmark for composition, color, and layout.
