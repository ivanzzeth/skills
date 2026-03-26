# Stage 1: DISCOVER — Market & User Research

## Goal

Validate that a real market opportunity exists before investing time building anything.

## Workflow

### Step 1: Define the hypothesis

Ask the user:
- What problem are you trying to solve?
- Who has this problem? (rough user profile)
- Why do you think this is worth solving now?

Write the hypothesis into `01-discovery.md`.

### Step 2: Market research & competitive analysis

Invoke `/competitive-intelligence-analyst`.

For each competitor, document:
- What they do well
- What they do poorly
- Pricing model
- Target audience overlap

Also research the broader market:
- Market size and trends
- Existing solutions and their limitations
- Recent industry shifts that create opportunity

Append market findings under **Market Landscape** and competitor findings under **Competitors**.

### Step 3: User psychology

Invoke `/marketing-psychology` to understand:
- What motivates the target user?
- What are their fears/frustrations?
- What triggers a purchase decision?

Append to `01-discovery.md` under **Key Insights**.

### Step 4: Synthesize

Write a **1-paragraph summary** at the top of `01-discovery.md`:
- The opportunity in one sentence
- The differentiation angle
- The biggest risk/unknown

## Gate 1 Checklist

Before advancing to DEFINE, confirm:

- [ ] Target user persona described (who, what role, what context)
- [ ] At least 3 competitors analyzed
- [ ] Market gap or differentiation angle identified
- [ ] User pain point articulated (not just a feature idea)
- [ ] One-paragraph opportunity summary written

Run `bash scripts/lifecycle.sh gate <product>` to verify.
Then `bash scripts/lifecycle.sh advance <product>` to proceed.
