# Claude prompt — SIH26170 professional dashboard

Paste everything below into Claude Code after giving it the repository. Work on
a separate branch or copy so backend code cannot be silently overwritten.

---

You are the senior product designer and frontend engineer for SIH26170, an
engineering decision-support system for early anomaly detection during
electronic component burn-in screening.

Before writing code, read:

- `outputs/SIH26170_TECH_STACK_LOCK.md`
- `src/sih26170/contracts.py`
- `src/sih26170/decision.py`
- the FastAPI OpenAPI schema or Pydantic response models, when present

## Non-negotiable stack

- React 19
- TypeScript strict mode
- Vite production build
- Tailwind CSS 4 using semantic theme variables
- shadcn/ui using the `new-york` style
- Recharts via the shadcn chart wrapper
- Lucide icons
- TanStack Table only for the component result table
- Native `fetch` through one typed API client; do not add Redux

The production build is served as static files by FastAPI. Do not introduce
Next.js, a Node production server, server-side rendering, a database, remote
fonts, CDN assets or a cloud API.

## Product states

### Initial

- Compact top bar: product name “Burn-In Sentinel”, subtitle “SIH26170”, model
  readiness indicator and model version
- Page title: “Component screening”
- One CSV upload panel with drag/drop and file picker
- Expandable required-column guide
- “Download verified sample CSV” secondary action
- Text: “Measurements are processed locally for this demonstration.”

### Processing

- Disable repeated submissions
- Show one honest indeterminate indicator: “Validating and scoring components”
- Do not show fake percentages or fabricated processing stages
- Keep filename, size and checkpoint visible

### Success

Show, in order:

1. Dataset strip: filename, source badge, batch count, component count,
   checkpoint and inference duration
2. Four summary cards: Accept, Monitor, Retest and Engineer review
3. Two-column workspace: sortable component table left; selected detail right
4. Component chart with:
   - observed values as a solid line and markers;
   - approved limit as a labelled horizontal rule;
   - future prediction as a distinct marker;
   - prediction interval as a translucent band;
   - visible units and time axis;
   - no smoothing that invents measurements
5. Recommendation block with action, uncertainty wording and reasons
6. Technical-evidence accordion with anomaly score, robust score, model score,
   predicted value, interval, feature contributions and version identifiers

### Error

Display a readable summary and, when supplied, a table containing row, column,
rejected value and correction. Never show a stack trace. Preserve the selected
filename so the user knows what failed.

## Visual system

Create a restrained industrial reliability console.

- Background around `#F4F6F8`
- White surfaces
- Deep slate text around `#172033`
- Navy primary around `#19466F`
- Restrained teal accent around `#0F766E`
- Green for Accept
- Amber for Monitor
- Orange for Retest
- Red for Engineer review
- Slate for neutral states
- Radius 8–10 px
- Subtle cool-gray borders
- Shadows only for major floating overlays
- System/bundled sans-serif and tabular numerals for measurements
- Consistent 4/8 px spacing scale

Do not use gradients, glassmorphism, neon/glow, decorative blobs, emojis,
oversized headings, giant empty cards, fake terminals, animated chart entrances,
marketing copy or excessive pills. It must resemble test-engineering software.

Color cannot be the only status signal. Use an icon and visible label. Meet
keyboard navigation, focus visibility, semantic HTML and WCAG AA contrast.

## Engineering rules

- Generate API types from OpenAPI; do not invent backend fields.
- Keep all requests in `src/lib/api`.
- Keep calculations out of React; it presents backend results only.
- No hard-coded counts, scores, predictions or explanations in production.
- Test mocks live under test-only fixtures that production cannot import.
- Make states explicit: idle, selected, submitting, success and error.
- Use `AbortController`, a 20-second timeout and a clear retry action.
- Clear the previous result when a new upload begins.
- Centralize value/unit formatting.
- Never reinterpret SHAP values as physical causes.
- Persistently show “Synthetic demonstration data” when the response says so.

## Components

- `AppShell`
- `ModelStatus`
- `CsvUploadPanel`
- `DatasetSummaryStrip`
- `DecisionSummaryCards`
- `ComponentResultsTable`
- `ComponentTrajectoryChart`
- `RecommendationPanel`
- `ReasonList`
- `TechnicalEvidence`
- `ValidationErrorPanel`
- `EmptySelectionState`

Keep each component narrow. Do not generate one enormous page component.

## Tests required

- Upload keyboard and drag/drop behavior
- Valid response renders counts correctly
- Selecting a table row updates component detail
- Prediction interval and upper limit come from the response
- Validation response renders field-level errors
- Synthetic-data badge cannot be omitted
- Previous results disappear when another upload starts
- Production build passes TypeScript strict mode
- One Playwright test uploads the verified CSV and sees the expected result from
  the real local API

## Completion response

Report:

1. files changed;
2. exact setup, test and production-build commands;
3. screenshots at 1440×900 and 1024×768;
4. accessibility checks;
5. any missing backend field;
6. confirmation that production has no mock-data path.

Do not modify ML algorithms or silently rename response fields. If a contract
is incomplete, document the missing field and use a typed temporary adapter
clearly marked for removal.

---

