---
name: pptx-skill
description: "Generate, edit, and structure professional PowerPoint presentations (.pptx). Use this skill when the user needs to draft a pitch deck, status report, or technical presentation."
---

# PowerPoint Generation Skill

This skill allows Claude to create and manipulate PowerPoint presentations. It focuses on layout management, slide generation, and high-contrast design for professional pitches.

## Guiding Principles
- **Clarity First**: Prioritize readability and high-impact visual hierarchy.
- **Consistency**: Maintain uniform fonts, colors, and layout across all slides.
- **Automation**: Use Python scripts (e.g., `python-pptx`) to generate the actual file structure.

## Core Workflows
1. **Outline Draft**: Start by defining the slide-by-slide narrative.
2. **Layout Selection**: Match the slide content to a specific layout (Title, Content, Two-Column, etc).
3. **Asset Integration**: Place images, charts, and icons in strategic positions.
4. **Final Export**: Generate the `.pptx` file and provide a download link.

## Pitch Deck Specialization
When building a pitch deck (like 'Code & Capital'), ensure:
- **Slide 1**: Hook / Vision
- **Slide 2**: The Problem (Crisis/Cost)
- **Slide 3**: The Solution (SwiftMedAI)
- **Slides 7-10**: Market Traction, Competition, and Financial Impact (ROI).

## Technical Implementation
- Use placeholders for images if not provided.
- Ensure all text fits within the safe area.
- Add notes for the presenter in the slide notes field.
