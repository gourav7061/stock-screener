# Workflows Directory

This directory contains **Markdown SOPs** (Standard Operating Procedures) that define how to use the WAT framework.

Each workflow file describes:

1. **Objective** — What problem this workflow solves or what task it accomplishes
2. **Required Inputs** — Data, parameters, or preconditions needed to run it
3. **Tools Used** — Which Python scripts from `../tools/` are called and in what order
4. **Expected Outputs** — Where results land (cloud services, local files, etc.)
5. **Edge Cases** — Known quirks, rate limits, error conditions, and recovery steps

## Workflow Template

```markdown
# [Workflow Name]

## Objective
[What does this workflow accomplish?]

## Required Inputs
- [Input 1]
- [Input 2]

## Tools Used
1. `tools/[script_name].py` — [what it does]
2. `tools/[script_name2].py` — [what it does]

## Expected Outputs
- [Output location / deliverable]

## Edge Cases & Gotchas
- [Known issue 1 and how to handle it]
- [Known issue 2 and how to handle it]
```

## Adding Your First Workflow

When you're ready to create a new workflow:
1. Create a new `.md` file in this directory (e.g., `scrape_website.md`, `generate_report.md`)
2. Follow the template above
3. Reference the exact Python script paths in `../tools/` that it relies on
4. Update this README with a one-line description of what the workflow does

## Reference

- See `../CLAUDE.md` for the WAT framework architecture overview
- See `../tools/` for available Python scripts and their purposes
