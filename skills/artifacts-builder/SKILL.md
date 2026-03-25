---
name: artifacts-builder
description: "Builds multi-component HTML artifacts using React 18, TypeScript, Tailwind CSS, and shadcn/ui via automated init and bundle scripts. Produces a single self-contained HTML file from a full React project. Use when creating interactive dashboards, data visualizations, multi-page apps, or any artifact requiring state management, routing, or shadcn/ui components — not for simple single-file HTML/JSX."
license: Complete terms in LICENSE.txt
metadata:
  category: development
  source:
    repository: 'https://github.com/ComposioHQ/awesome-claude-skills'
    path: artifacts-builder
    license_path: artifacts-builder/LICENSE.txt
---

# Artifacts Builder

Creates production-grade, self-contained HTML artifacts from full React + TypeScript projects. Uses `scripts/init-artifact.sh` for scaffolding and `scripts/bundle-artifact.sh` to inline all assets into a single shareable HTML file.

**Stack**: React 18 + TypeScript + Vite + Parcel (bundling) + Tailwind CSS 3.4.1 + shadcn/ui (40+ components)

## Workflow

### Step 1: Initialize Project

```bash
bash scripts/init-artifact.sh <project-name>
```

Creates a configured project with:
- React + TypeScript via Vite (auto-detects Node 18+ and pins Vite version)
- Tailwind CSS with shadcn/ui theming and path aliases (`@/`)
- 40+ pre-installed shadcn/ui components with all Radix UI dependencies
- Parcel bundling configuration via `.parcelrc`

### Step 2: Develop the Artifact

Edit the generated files to build the artifact. Component reference: https://ui.shadcn.com/docs/components

### Step 3: Bundle to Single HTML

```bash
bash scripts/bundle-artifact.sh
```

Produces `bundle.html` — a self-contained file with all JS, CSS, and dependencies inlined. Requires `index.html` in the project root.

The script installs bundling dependencies (parcel, @parcel/config-default, parcel-resolver-tspaths, html-inline), builds with Parcel (no source maps), and inlines all assets.

### Step 4: Share the Artifact

Share `bundle.html` in the conversation so the user can view it directly.

### Step 5: Test (Optional)

Only test if requested or if issues arise. Use available tools (Playwright, Puppeteer, or other skills). Avoid testing upfront to minimize latency between request and delivery.

## Design Guidelines

Avoid generic "AI slop" aesthetics: no excessive centered layouts, purple gradients, uniform rounded corners, or Inter font. Aim for distinctive, intentional design choices.
