---
name: xlsx-skill
description: "Create, edit, and analyze Excel spreadsheets (.xlsx). Use this skill for data analysis, mission logging, and financial projections."
---

# Excel Data Analysis Skill

This skill allows Claude to manipulate complex spreadsheets. It emphasizes standard formatting, formula integrity, and data visualization via pivot tables or charts.

## Guiding Principles
- **Data Integrity**: Always verify formulas and cross-references.
- **Scannability**: Use bold headers, alternating row colors, and conditional formatting.
- **Portability**: Ensure the resulting file uses standard libraries (e.g., `openpyxl`, `pandas`).

## Core Workflows
1. **Schema Design**: Define column headers and data types.
2. **Data Insertion**: Populate rows from mission logs or simulated data.
3. **Calculations**: Apply formulas for ROIs, averages, and deltas (e.g., `-86% ground response time`).
4. **Formatting**: Apply filters, freeze panes, and professional styling.

## Mission Log Specialization
For SwiftMedAI log generation:
- **Sheet 1**: Live Mission Data (ID, Target, ETA, Status, Clinician).
- **Sheet 2**: Impact Benchmarks (Ground vs. Drone, Cost Savings).
- **Sheet 3**: Technical Logs (Battery, GPS, Signal Strength).
