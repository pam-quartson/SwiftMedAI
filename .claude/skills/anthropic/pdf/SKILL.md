---
name: pdf-skill
description: "Generate and manipulate PDF documents. Use this skill when formal technical reports, certifications, or regulatory documentation are required."
---

# PDF Documentation Skill

This skill allows Claude to generate formal, non-editable documents. It focuses on fixed layouts, brand compliance, and multi-page report generation.

## Guiding Principles
- **Formal Positioning**: Use professional fonts (e.g., Helvetica, Times) and standard margins.
- **Fixed Layout**: Ensure tables and images do not break across pages unintentionally.
- **Compliance**: Include timestamps, versioning, and secure headers for regulatory reports.

## Core Workflows
1. **Template Definition**: Define the header (Brand Logo), footer (Page #), and body areas.
2. **Component Assembly**: Insert technical summaries, charts, and clinical notes.
3. **Rendering**: Use Python libraries (e.g., `fpdf`, `reportlab`) to render the final document.
4. **Metadata**: Set the document properties (Author, Title, Security Level).

## Regulatory Specialization
For drone missions, ensure the PDF contains:
- **Flight Log Summary**: ID, Path, and Duration.
- **Clinical Sign-off**: Name of clinician and authorization timestamp.
- **Payload Report**: Final state of individual items in the Omnicell cabinet.
