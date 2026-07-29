# Study Management Platform — Discovery Document

Working discovery document for a solo-founder study management platform. This document surfaces tradeoffs, makes direct recommendations where marked, and keeps open decisions open. It is not a pitch deck.

## Founder Context

- Personal workflow tool, not a broad SaaS product; speed to first value dominates architectural completeness.
- Self-hosted or free-tier hosting only; no multi-tenant design up front.
- Content is 60%+ executable snippets overall, but the code ratio varies by domain from 5% to 95%.
- Two equally severe pain points: (1) forgetting materials exist, (2) search failing to resurface them.
- Code versioning: new versions kept alongside old ones for comparison, never edited in place. Inline testing of small snippets is acceptable; full in-platform execution is not a primary requirement.
- These constraints are referenced briefly below where relevant rather than restated in each section.

---

## 1. Problem & Workflow Friction

The founder's workflow breaks in two concrete places.

**Failure mode 1 — forgetting materials exist.** The founder creates notes, code snippets, screenshots, and reference links across notebooks, files, and browser tabs. Over time these artifacts become invisible because they lack a stable identity, a topic anchor, and a retrieval surface. The material exists on disk but not in memory. The platform addresses this by giving every study item a persistent identity, topic metadata, and a searchable body, then surfacing recent, related, and version-linked materials through a unified index. The recovery path should not depend on remembering a perfect keyword.

**Failure mode 2 — search failing to resurface them.** Three sub-failures compound this: (a) the founder searches and gets irrelevant or buried results, (b) the result set is overwhelming and unmanageable, and (c) the founder does not know what keyword to search for in the first place. Each sub-failure has a different root cause and a different fix cost, which is why they need to be addressed separately rather than as one monolithic "improve search" goal. The platform addresses each through a combination of weighted indexing, faceted filtering, and discovery aids (recent items, related topics, browseable clusters).

---

## 2. Content & Organization Model

**[RECOMMEND]** Use one unified organizational and search model rather than separate models per content mix. The core object should be a material with typed blocks and metadata; rendering can vary by content type, but discovery should stay consistent across code-heavy and prose-heavy domains. Separate models would fragment search behavior, make cross-material relationships harder to express, and create more maintenance than a solo founder can absorb in an MVP timeline. A unified model also means the founder does not need to decide "which bucket does this belong in" every time they capture something — the same capture path works for a 5% code note and a 95% code snippet.

**[RECOMMEND]** The hardest challenge across mixed content types is normalizing relevance signals without flattening what makes each type useful. Code wants exact token matching, version awareness, and syntax-adjacent signals (language, imports, function names). Prose wants semantic similarity and topic labels. Images need surrounding context and alt text to be discoverable at all. This matters because the product only works if a single search surface can rank all of them plausibly enough to resurface old material instead of hiding it in type-specific silos. If the search model treats code and prose identically, code snippets get lost among prose notes; if it treats them too differently, cross-material discovery breaks.

---

## 3. Code Storage & Retrieval

**[RECOMMEND]** Model a real linear version chain from day one, but keep the structure simple. Each canonical snippet gets a stable identity with immutable versions underneath it, each version pointing to its parent. The MVP should expose a timeline view with version number, short change summary, tags, and a compare action against the previous or selected version.

Concrete structure the founder can sketch out:

| Component | Attributes | Purpose |
| --- | --- | --- |
| Snippet (canonical) | id, title, topic links, current_head_version_id, created_at | Stable identity for a snippet that evolves over time |
| Version | id, snippet_id, parent_version_id, version_number, content, language, change_note, test_status, created_at | Immutable snapshot; never edited in place |
| Diff view | from_version_id, to_version_id | Compare any two versions; show added/removed lines |
| Iteration tag | label (draft, tuned, reference, deprecated) | Quick visual signal of where a version sits in its evolution |

The version chain is the right call here because the founder's core promise is comparison over time. Flat storage plus a naming convention (e.g., `snippet_v2.py`) is a temporary UI trick, not a storage model — if version comparison is deferred too long, the history becomes harder to model and harder to trust. Since the founder is already committing to never-edit-in-place, the storage model should reflect that discipline rather than papering over it.

---

## 4. Search & Discovery

For each failure mode, "reliable" means the founder can find the right material with low guesswork and low noise.

### Irrelevance / Buried Results

**[RECOMMEND]** Reliable means exact or near-exact matches rise to the top, titles and tags carry extra weight, and a few strong signals beat many weak ones. Architecturally, this requires weighted indexing over title, tags, code tokens, body text, and relation links — with title and tags receiving the highest boost. Behaviorally, it still depends on a minimum labeling discipline so the search engine has something meaningful to rank. The fix is roughly 60% architectural (indexing strategy, field weighting) and 40% behavioral (the founder consistently tags and titles materials).

### Result Overload

**[RECOMMEND]** Reliable means the first screen gives a short, explainable result set with filters, not a wall of everything that vaguely matches. Architecturally, this is ranking, deduplication, faceting, and result chunking — all of which build on the same weighted index used for irrelevance. Behaviorally, the founder should avoid dumping unrelated concepts into one record, because no ranking strategy fully fixes muddled input. The fix is roughly 70% architectural (ranking + faceting) and 30% behavioral (record discipline).

### Not Knowing What to Search For

**[RECOMMEND]** Reliable means the system can lead the founder to likely material through recent items, related topics, saved views, and browseable clusters — even when the founder has no keyword in mind. Architecturally, this is the most expensive mode because it starts to require semantic or graph-like discovery aids (topic clusters, relation traversal, usage-pattern suggestions). Behaviorally, it also depends on consistent topic naming and a small controlled vocabulary so the system has stable nodes to browse. The fix is roughly 50% architectural (graph/clustering infrastructure) and 50% behavioral (naming consistency).

**[OPEN]** Solve irrelevance and buried results first in the MVP. It is the cheapest way to make search feel trustworthy, it directly reduces the "I know it exists but can't find it" pain, and it unlocks better browsing later because the founder starts trusting the index. Defer the "what should I search for?" problem until the structure and labels have real usage data; that one is more expensive, more ambiguous, and easier to over-engineer too early. Overload can be partially handled by the same ranking work that fixes irrelevance, so it does not need its own separate MVP lane. The tradeoff: in the interim, the founder will still hit walls when they have no keyword at all, but that pain is less severe than the pain of not trusting search results at all.

---

## 5. Data Model & Architecture

### Relational Data Model

| Entity | Key Attributes | Relationships | Purpose |
| --- | --- | --- | --- |
| materials | id, title, material_type, topic_summary, status, current_version_id, created_at, updated_at | has many versions, tags, attachments, relations | Stable identity for anything the founder wants to resurface |
| material_versions | id, material_id, parent_version_id, version_number, language, change_note, created_at, created_by, test_status | belongs to one material, has many blocks | Immutable history for snippets and mixed-content edits |
| material_blocks | id, version_id, block_order, block_type, language, text_content, code_content, alt_text, source_ref | belongs to one version | Stores mixed content in searchable units |
| attachments | id, material_id, version_id, file_path, mime_type, caption, alt_text, width, height | belongs to a material or version | Handles images, screenshots, and other linked assets |
| tags | id, name, slug, tag_type | linked through material_tags | Shared vocabulary for topics and retrieval |
| material_tags | material_id, tag_id, version_id (optional) | joins materials to tags | Primary labeling surface for discovery |
| material_relations | id, from_material_id, to_material_id, relation_type, note, strength, created_at | links materials to materials | Cross-material resurfacing and topic graph |
| saved_searches | id, name, query, filters, created_at | belongs to the user | Reusable discovery entry points |
| search_events | id, query, clicked_material_id, no_result_flag, created_at | logs search behavior | Feedback loop for ranking and future improvements |

This model is optimized around one stable material identity, immutable versions, and flexible relationships. That combination supports discovery better than a type-specific schema because it keeps search, tags, and links in the same retrieval path. The `version_id` on `material_tags` is optional — it allows tagging at a specific version if needed, but defaults to material-level tagging for simplicity.

### Deployment Model

**[RECOMMEND]** The simplest deployment model is a single application with one relational database, one file store for assets, and one background worker if needed. For the MVP, SQLite with a persistent volume is enough if the hosting environment is simple and the dataset is still small; Postgres becomes the better choice only if persistence, concurrency, or future multi-user scaling starts to matter. Keep search in-process or in-database at first rather than introducing a separate search service.

The minimal model is fast to build and easy to self-host, but it trades away some future scaling headroom. Adding a separate search stack (e.g., Elasticsearch), message queue, or microservices now would slow the founder down without solving a problem they have not proven yet. The key tradeoff: minimal now means a potential migration later, but that migration is cheap if the data model is clean and the application layer is decoupled from the storage layer.

---

## 6. Build Sequencing

**[RECOMMEND]** Build in phases that get the founder to real capture and retrieval as early as possible, then make retrieval trustworthy, then broaden discovery.

### Phase 1 — Week 1: Capture and Basic Retrieval

**Build:** materials, immutable versions, blocks, tags, attachments, a simple recent list, and basic keyword search over titles, tags, and content.

**Defer:** semantic search, cross-material graph browsing, advanced diff views, execution helpers, analytics, saved searches.

**Why:** this gets real study material into the system immediately and tests whether the founder will actually keep using it. The two core pain points are partially addressed — the founder can now capture and find things by exact keyword, which is better than scattered files.

### Phase 2 — Weeks 2–3: Make Retrieval Trustworthy

**Build:** better ranking, result previews, duplicate suppression, filter chips, related-material links, and a compare view for versions.

**Defer:** multi-tenant concerns, collaboration, heavy automation, deep search infrastructure, semantic suggestions.

**Why:** this is where the two core pain points start to bend. The founder can now find old material with less guessing and compare snippet evolution when needed. The search irrelevance problem is meaningfully reduced.

### Phase 3 — Later: Broaden Discovery and Polish the Model

**Build:** semantic suggestions, saved searches, browsing by topic clusters, stronger relation types, richer image handling, and optional execution helpers.

**Defer:** only if proven unnecessary, not because the platform cannot support them.

**Why:** these features help when the founder has enough real content for patterns to emerge. They are deferred not because they are hard, but because they need usage data to be worth building.

### Three Specific Sequencing Calls

1. **Day-one data model:** materials, versions, blocks, tags, and attachments must exist on day one. Those are hard to retrofit later because they define the identity and retrieval surface of the content. Relations and saved searches can be added later without a painful migration if the base IDs are stable. The risk of deferring relations is low in the short term; the risk of deferring the core entities is high because every subsequent feature depends on them.

2. **First search mode to address:** irrelevance and buried results get addressed in Phase 1–2. Overload gets partially improved by the same ranking work, while the "not knowing what to search for" problem can wait until Phase 3. The interim cost is that discovery will still rely on the founder having some idea of the topic name — they will not get guided discovery, but they will get trustworthy exact-match retrieval.

3. **Code-version surfacing:** a real version chain is required in v1. Flat storage plus a naming convention is not enough because the founder's promise is comparison over time, and that is hard to reconstruct later once materials accumulate. The version chain is one of the few things that would be expensive to retrofit after the fact.

### Retrofit Risk Flags

- **Version history and identity** (Section 3): if deferred, the platform will have to rework how materials are stored just to support the core study workflow. This is the most expensive retrofit risk in the entire build.
- **Search indexing strategy** (Section 4): if deferred too long, the founder accumulates materials with no consistent tagging, and the index becomes noisy and untrustworthy — which makes it harder to adopt a better indexing strategy later because the founder has already lost confidence in search.
- **Relations and graph** (Section 5): can be bolted on later without painful migration, but the longer it is deferred, the more manual relationship-building the founder will have to do retroactively.

---

## 7. Discovery Questions

The founder should answer these before committing to the next layer of build. Do not answer them here — surface them for the founder to resolve.

- How much of the product should adapt to code-heavy domains versus stay uniform across all content ratios? The 5%–95% range is wide; over-engineering for the extremes will slow the MVP, but under-adapting will make code-heavy domains feel like second-class citizens.
- What is the smallest useful way to show version evolution without making the interface feel cluttered? The version chain is necessary, but the UI surface for it needs to be proportional to how often the founder actually compares versions.
- Which search failure mode matters most after the first usable MVP: relevance, overload, or not knowing what to search for? The answer determines whether Phase 2 should focus on ranking or on discovery aids.
- How much of search quality should come from indexing and structure versus from labeling habits and naming discipline? The split determines how much the platform can compensate for the founder's inconsistency versus how much discipline is required.
- If the tool later becomes multi-tenant, which parts must stay constant now and which can be redesigned later? The data model and application layer should be designed so that tenant isolation can be added without a schema rewrite, but the storage and deployment model can evolve.
- Does the founder want validation after week 1 on real study material, or is a longer setup phase acceptable before the tool feels useful? This determines whether Phase 1 should be even more minimal (just capture, no search) or whether the current scope is right.
- Whether the proposed build sequencing matches how the founder actually wants to validate the tool — e.g., do they want to start using it on real material after week 1, or are they comfortable with a longer setup phase before first real use?

---

*This document is a working discovery artifact. Open decisions remain open; recommendations are marked and should be treated as proposals for discussion, not final commitments.*
