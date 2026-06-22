# Seymour — Daily Contribution Workflow

## How It Works

1. **You drive.** You think. You talk.
2. **Siri captures.** Voice → text → Telegram → Hermes.
3. **Hermes processes.** I categorize, file, and integrate each contribution.
4. **Seeds grow.** Over time, contributions become Ponderable entries.

## Contribution Types

### Type A: Seed
A raw observation, idea, or fragment. Gets filed under a topic.

```
SEED: [topic]
[text]
```

### Type B: Essay Fragment
A longer piece of writing. Gets appended to a Ponderable draft.

```
ESSAY: [PONDERABLE # or NEW]
[text]
```

### Type C: Reference
A book, article, meme, or cultural artifact to reference.

```
REF: [PONDERABLE #]
[source title] — [why it matters]
```

### Type D: Pull Quote
A quote from MGS2, philosophy, or other source.

```
QUOTE: [source]
"[text]"
[why it fits Seymour]
```

### Type E: Clipart Request
A description of what kind of clipart would fit a Ponderable.

```
ART: [PONDERABLE #]
[description of desired clipart]
```

### Type F: Organizational
Structural notes about the series, format, or cross-references.

```
ORG: [topic]
[text]
```

## Filing System

Each contribution is appended to the relevant file:

| Contribution | Filed To |
|-------------|----------|
| Seed | `ponderables/seeds/[topic].md` |
| Essay | `ponderables/PONDERABLE-XXX/draft.md` |
| Reference | `ponderables/PONDERABLE-XXX/references.md` |
| Pull Quote | `research/pull-quotes.md` |
| Clipart Request | `ponderables/PONDERABLE-XXX/clipart-requests.md` |
| Organizational | `research/organization.md` |

## Processing Rules

1. **Every contribution gets acknowledged** with what I did with it
2. **Seeds get tagged** with potential Ponderable numbers
3. **Essays get word-counted** and progress tracked
4. **References get cross-referenced** to existing Ponderables
5. **Pull quotes get categorized** by theme
6. **Daily summary** sent at end of session

## Current Ponderables

| # | Title | Status | Words |
|---|-------|--------|-------|
| 001 | The Mimetic War | Outline | 0/8000 |
| 002 | TBD | Seeds only | 0 |

## Cross-Reference Index

As Ponderables accumulate, this index tracks connections:

```
PONDERABLE-001 "The Mimetic War"
  → References: Dawkins 1976, MGS2 Colonel, PONDERABLE-003
  → Themes: imitation, cultural evolution, information overload
  → Clipart: [pending]
```
