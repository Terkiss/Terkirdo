---
name: cluedoc
description: >-
  Document a codebase as a set of interlinked, visual "papers" under .cluedoc/. Operates with default auto_sync: false under Terukirdo governance: generate or synchronize .cluedoc/ visual paper trees only upon the user's explicit request (e.g. "/cluedoc init" or explicit Cluedoc creation/sync instruction) or when explicitly enabled by project policy Opt-In. Never auto-inject sync triggers into AGENTS.md or other SSOT files. Additionally, whenever the user asks a question about how the system works and .cluedoc/ papers already exist, append a short "Reading Guide" pointing at the most relevant existing papers.
license: MIT
metadata:
  author: keunwoo
  version: "0.3.0-terukirdo-v5.7"
---

# Cluedoc

Cluedoc documents a repository by writing a set of **papers** — one focused document per **feature** of the system. Papers are richly visual and cross-reference each other, so a reader can start anywhere and follow links to the context they need.

## Terukirdo Governance & Opt-In Rule (`auto_sync: false`)

Under `Terukirdo_Protocol_v5.7.md` (§9.4) and `.agents/rules/documentation.md`, Cluedoc strictly obeys the following governance rules:

1. **Explicit Opt-In Only (`auto_sync: false` Default):** The default configuration is `auto_sync: false`. Do **not** automatically create or modify `.cluedoc/` files after ordinary code changes unless the user explicitly instructs you to create/update Cluedoc papers or the project policy has explicitly opted in. After code changes when `.cluedoc/` exists, simply report if any Cluedoc papers may be stale and await user approval before updating them.
2. **No Automatic SSOT / Agent-Instructions Injection:** Even when running `init` (e.g., `/cluedoc init`), **never** automatically edit or inject sync-trigger blocks into `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or any project SSOT / agent-instructions file. If persistent synchronization policy registration is desired, propose it only as a candidate agenda item to the user and wait for explicit approval.
3. **Documentation Candidate, Not Completion Evidence:** Cluedoc papers are documentation candidates, never verification evidence. Always verify actual source code and test states before generating or relying on papers.

---

Cluedoc has **one mode**, not two. It organizes papers by **capability**, not by code layout — one unified feature tree spans the whole repository regardless of how the code is packaged. This is why the usual "monorepo vs. single-package" distinction never comes up: Cluedoc does not detect or branch on repo shape. A capability that lives in its own package appears as a feature next to the capabilities it builds on, and a `sources` list (see below) can freely point across package boundaries. Whether the repo is one package or twenty, the documentation is the same kind of capability tree.

## Papers Are Features, Organized as a Hierarchy

The unit of documentation is **one feature**. Features form a hierarchy: large features contain smaller sub-features. Cluedoc mirrors this hierarchy in the folder structure — **higher-level features live in higher folders, lower-level (finer-grained) features live deeper**.

**Where splitting stops (the one-paper rule).** Split a feature into sub-features when it has distinct sub-capabilities that each deserve their own hero visual and description. Stop when a feature can be fully explained in a single focused paper. This is a judgment about *capability*, not a mirror of the code's directory structure.

**Layout.** Everything lives in a `.cluedoc/` folder at the repository root. Every feature — leaf or parent — is a **folder**, and its paper is a `README.md` inside that folder. Sub-features are subfolders.

```
.cluedoc/
├── README.md                  ← ROOT paper: the whole repository/app
├── authentication/
│   ├── README.md              ← the "Authentication" feature paper
│   ├── login/
│   │   └── README.md          ← sub-feature: "Login"
│   └── session-management/
│       ├── README.md          ← sub-feature: "Session Management"
│       └── token-refresh/
│           └── README.md      ← deeper sub-feature: "Token Refresh"
└── billing/
    └── README.md
```

The **root paper** (`.cluedoc/README.md`) is the entry point for the whole repository. It follows the same paper structure as any other, and its Related Work lists the top-level features as children.

Making every feature a folder (even leaves) keeps the structure uniform and lets a leaf grow sub-features later without any rename. Folder names are slugs: lowercase the feature title, replace spaces with hyphens, strip non-alphanumeric characters.

## How Cluedoc Builds Docs — Progressively, Both Directions

When authorized by the user (or Opt-In policy) to document a feature or sync a code change, Cluedoc does **not** document the whole repository in one giant pass. It builds the documentation **progressively**, propagating **both up and down** the feature hierarchy:

- **Upward (what contains this):** scan **where the changed code is used** — call sites, imports, references. This reveals the larger feature the code participates in, and how the change affects that parent.
- **Downward (what this depends on):** scan **what the changed code uses** — the functions and modules it calls. These are its child features/collaborators, and the change may alter how they are described or which ones matter.

When requested to document added or changed code, Cluedoc:

1. **Locates the code** and scans **both directions** — its callers (upward) and its callees (downward).
2. **Infers its purpose** — what capability this code serves, in language-neutral terms.
3. **Places it in the tree** — identifies the parent feature that contains it *and* the child features it builds on, up to a level that already has a paper (or the root), and down to the collaborators worth documenting.
4. **Creates or updates every affected paper** — parent, self, and children alike — placing each at the correct depth in `.cluedoc/`. A small change may touch one leaf; a structural change may ripple across several levels in both directions.

```
   root paper ─────────────► update if the top-level picture shifted
        ▲  upward: "where is this used?" (callers)
        │
   parent feature ─────────► refine to reflect the changed sub-feature
        ▲
        │
   changed code ───────────► create/update its own paper
        │
        ▼
   child features ─────────► update the collaborators it now uses
        │  downward: "what does this use?" (callees)
        ▼
   deeper children ────────► add/refine if new dependencies appeared
```

## The `init` Command — Explicit Starter Bootstrap

`init` is the one-time way to *start* Cluedoc in a repository when the user explicitly runs `/cluedoc init` or asks to initialize Cluedoc.

### Starter Paper Generation (shallow, breadth-first)

Create a starter skeleton under `.cluedoc/`, leaving deeper sub-features for future user-approved updates:

1. **Guard.** If `.cluedoc/` already has papers, do **not** overwrite. Tell the user it is already initialized and ask if they want an explicit sync instead. Only proceed when `.cluedoc/` is absent or empty.
2. **Find the top-level features.** Survey the repository and identify its handful of major capabilities in language-neutral terms (typically 3–7).
3. **Write only two levels:**
   - The **root paper** (`.cluedoc/README.md`) — the whole-repository overview.
   - **One paper per top-level feature** (`.cluedoc/<slug>/README.md`).
   Each is a full paper: frontmatter (`title`, `sources`) plus the six sections and a hero visual, per *The Paper Structure*.
4. **Do not recurse.** Stop at the top level. The root's Related Work links the top-level papers you just created (never link papers you haven't written).
5. **SSOT Protection (No Auto-Wire-Up).** Do **not** modify `AGENTS.md`, `CLAUDE.md`, or any repository policy file during `init`. Report the created `.cluedoc/` papers to the user; if the user wishes to enable ongoing synchronization policy in project rules, present that option as a separate candidate proposal requiring explicit user approval.

## Keeping Papers in Sync (Upon Explicit Request or Opt-In)

When updating `.cluedoc/` under user approval:

- **New feature** → create its folder + `README.md`; add it to its parent's Related Work.
- **Feature grows sub-capabilities** → split it: create subfolders for the new sub-features, move the fine-grained detail down, leave the parent paper as an overview that links to its children.
- **Feature renamed or refocused** → rename the folder (new slug) and update every inbound hyperlink so no reference dangles.
- **Feature removed** → delete its folder and fix or remove links that pointed to it.

After any of these, verify that all Related Work hyperlinks still resolve.

## Abstract Prose, Anchored to Code

Papers are **about** the code but must never **contain** the code. The reading experience stays abstract and human-readable; the link to the implementation lives in structured metadata, out of the prose.

**In the prose — describe, don't quote.** Write about behavior, responsibilities, data, and concepts in plain domain language. Do **not** put into the body of a paper:
- Code snippets or excerpts
- Function, class, method, variable, or type names written as code symbols
- File paths, directory names, or line numbers
- Language- or framework-specific implementation trivia

Name concepts the way a user or designer would ("the option's *value source*", "the *parse loop*"), not the way the compiler would (`getOptionValueSource()`). If you feel the urge to paste code to explain something, draw a visual instead.

**In the frontmatter — anchor to code.** Each `README.md` carries a `sources` list in YAML frontmatter pointing at the files or directories that realize the feature. This is the *only* place raw paths appear, and it is metadata, not narrative:

```markdown
---
title: Option Parsing
sources:
  - lib/option.js
  - lib/command.js   # option registration & the parse loop
---
```

Keep `sources` at the granularity of files or directories (not symbols or line numbers) so it survives ordinary refactors. **`sources` may overlap across papers** because one file often contributes to several features.

## The Paper Structure

Every doc Cluedoc produces is a *paper* with YAML frontmatter (`title`, `sources`) followed by exactly these sections, in order:

1. **Hero visual** — a diagram that captures the essence of the subject at a glance (Mermaid or CLI graphic). Opens the paper before any prose.
2. **Abstract** — a short paragraph: what this part of the system is and why it exists.
3. **Introduction** — the problem it solves and the context a reader needs to start.
4. **Related Work** — hyperlinks to *other Cluedoc papers* that give the reader context.
5. **Description** — the substance: how the subject works, its behavior, structure, and important details. Heavy use of visuals.
6. **Conclusion** — what to take away; where the reader might go next.

## Visuals Are Mandatory

Papers must be **visual**. Never explain a system or concept in prose alone when a visual would make it clearer:
- **Mermaid diagrams** — for structure, flows, relationships, state, sequences (`flowchart TD`, `sequenceDiagram`, `stateDiagram-v2`, `classDiagram`, `erDiagram`).
- **CLI-style text graphics** — for directory trees, ASCII boxes-and-arrows, tables, layouts.

## Related Work = the Link Graph

Related Work carries **all** cross-paper links, including hierarchy links:
- The **parent feature** paper (the folder above).
- **Child sub-feature** papers (the folders below).
- Any **non-adjacent** papers that provide useful context, anywhere in the tree.

Guidelines:
- Prefer linking to Cluedoc papers over re-explaining shared concepts.
- Every listed reference must be a working relative hyperlink (e.g. `../README.md`, `./login/README.md`).
- **Link only papers that already exist. Never create a dead link to a planned-but-unwritten paper.**

## Reading Guide — Recommend Papers When Answering Questions

Whenever the user asks a question about **how the system works** — a feature, a flow, an architectural decision, "where does X happen", "how does Y work" — answer the question first, then **append a short "Reading Guide"** that points them at the Cluedoc papers most worth reading to go deeper on that question.

**When to append a guide.** Only when both hold:
- The question is about understanding the system (its behavior, structure, or design) — not a pure coding task, a shell command, or a question unrelated to this repository.
- A `.cluedoc/` folder with papers actually exists. If it does not, say nothing about a reading guide, and never invent papers or links.

**How to build the guide.**
1. **Map the question to features.** Identify which capabilities the question touches, then find the existing papers that cover them.
2. **Pick the entry point, then the path.** Recommend the single best paper to start from, followed by 1–4 papers that build context around it in a suggested reading sequence.
3. **Say why each matters.** One concise clause per entry explaining what the reader gets from it.
4. **Link only papers that exist**, using working relative hyperlinks from the repository root (e.g. `.cluedoc/authentication/README.md`).

**Format.** Close the answer with a compact section, for example:

```markdown
### Reading Guide
1. [Authentication](.cluedoc/authentication/README.md) — start here for the overall login flow your question is about.
2. [Session Management](.cluedoc/authentication/session-management/README.md) — how the session your request creates is tracked afterward.
3. [Token Refresh](.cluedoc/authentication/session-management/token-refresh/README.md) — the specific mechanism behind the expiry behavior you asked about.
```
