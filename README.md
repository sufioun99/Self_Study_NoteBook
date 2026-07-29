# Self_Study_NoteBook
Self-study notebook: software for storing study elements and code pictures linked to related topics.

You are a product strategist helping a founder think through a study management platform during discovery. The goal is to surface tradeoffs clearly, make direct recommendations where marked, and keep the document practical for a solo founder building an MVP in weeks.

## Founder Context
- Core problem: this is a personal workflow tool, not a broad SaaS product, and speed to first value matters more than architectural completeness.
- Constraints: self-hosted or free-tier hosting only, no multi-tenant design up front.
- Content composition: most content is code-heavy overall, but the code ratio varies widely by topic area.
- Two severe pain points: forgetting materials exist, and search failing to resurface them reliably.
- Code model: snippets are versioned alongside older versions for comparison; they are not edited in place.
- Execution: inline testing of small snippets is acceptable, but full in-platform execution is not the main requirement.

Reference these constraints briefly where relevant rather than repeating them in every section.

---

## 1. Problem & Workflow Friction

The workflow breaks in two places. First, the founder forgets materials exist because notes, snippets, images, and topic links are stored as isolated artifacts rather than a remembered trail of study work. Second, search fails because the founder often does not know the best keyword, the result set is either too noisy or too long, and useful items are buried behind weak ranking or inconsistent labeling.

The platform should address both by making every study item independently findable through a stable identity, topic metadata, and a searchable body, then by showing recent, related, and version-linked materials even when the exact keyword is missing. That means the default recovery path should not depend on remembering a perfect phrase.

---

## 2. Content & Organization Model

**[RECOMMEND]** Use one unified organization and search model, not separate models by content mix. The core object should be a material with typed blocks and metadata; rendering can vary by content type, but discovery should stay consistent across code-heavy and prose-heavy domains. Separate models would fragment search behavior, make cross-material relationships harder, and create more maintenance than the MVP can absorb.

**[RECOMMEND]** The hardest challenge is normalizing relevance across mixed content types while preserving what makes each type useful. Code wants exact token matching, version awareness, and syntax-adjacent signals; prose wants semantic similarity and topic labels; images need surrounding context and alt text. This matters because the product only works if a single search surface can rank all of them plausibly enough to resurface old material instead of hiding it in type-specific silos.

---

## 3. Code Storage & Retrieval

**[RECOMMEND]** Use a real linear version chain from v1, but keep it simple. Model one canonical snippet record with immutable versions underneath it, each version pointing to its parent. Show a timeline view with version number, short change summary, tags, and a compare action against the previous or selected version. For the MVP, that is enough to expose evolution without needing branching or complex merge logic.

Concrete structure:
- Canonical snippet: stable identity, title, topic links, current head version.
- Version rows: immutable content, parent version, created time, short note, language, and execution/test metadata if available.
- Compare UI: diff between head and prior version, plus an optional compare against any earlier version.
- Iteration tags: labels like draft, tuned, reference, or deprecated so the founder can see how a snippet evolved.

Flat storage plus naming convention is too weak here because version comparison is part of the core promise; if it waits too long, the history becomes harder to model and harder to trust.

---

## 4. Search & Discovery

For each failure mode, “reliable” should mean the founder can find the right material with low guesswork and low noise.

**Irrelevance or buried results**: reliable means exact or near-exact matches rise to the top, tags and titles matter, and a few strong signals beat many weak ones. Architecturally, this needs weighted indexing over title, tags, code tokens, body text, and relation links. Behaviorally, it still depends on a minimum labeling discipline so the search engine has something to rank.

**Overload**: reliable means the first screen gives a short, explainable result set with filters, not a wall of everything that vaguely matches. Architecturally, this is mostly ranking, deduping, faceting, and chunking. Behaviorally, the founder should avoid dumping unrelated concepts into one record, because no ranking strategy fully fixes muddled input.

**Not knowing what to search for**: reliable means the system can still lead the founder to likely material through recent items, related topics, saved views, and browseable clusters. Architecturally, this is the most expensive mode because it starts to require semantic or graph-like discovery aids. Behaviorally, it also depends on consistent topic naming and a small controlled vocabulary.

**[OPEN]** Solve irrelevance and buried results first in the MVP. It is the cheapest way to make search feel trustworthy, it directly reduces the “I know it exists but can’t find it” pain, and it unlocks better browsing later because the founder starts trusting the index. Defer the “what should I search for?” problem until the structure and labels have real usage data; that one is more expensive, more ambiguous, and easier to over-engineer too early. Overload can be partially handled by the same ranking work, so it does not need its own separate MVP lane.

---

## 5. Data Model & Architecture

| Entity | Key attributes | Relationships | Purpose |
| --- | --- | --- | --- |
| materials | id, title, material_type, topic_summary, status, current_version_id, created_at, updated_at | has many versions, tags, attachments, relations | Stable identity for anything the founder wants to resurface |
| material_versions | id, material_id, parent_version_id, version_number, language, change_note, created_at, created_by, test_status | belongs to one material, has many blocks | Immutable history for snippets and mixed-content edits |
| material_blocks | id, version_id, block_order, block_type, language, text_content, code_content, alt_text, source_ref | belongs to one version | Stores mixed content in searchable units |
| attachments | id, material_id, version_id, file_path, mime_type, caption, alt_text, width, height | belongs to a material or version | Handles images, screenshots, and other linked assets |
| tags | id, name, slug, tag_type | linked through material_tags | Shared vocabulary for topics and retrieval |
| material_tags | material_id, tag_id, version_id optional | joins materials to tags | Primary labeling surface for discovery |
| material_relations | id, from_material_id, to_material_id, relation_type, note, strength, created_at | links materials to materials | Cross-material resurfacing and topic graph |
| saved_searches | id, name, query, filters, created_at | belongs to the user | Reusable discovery entry points |
| search_events | id, query, clicked_material_id, no_result_flag, created_at | logs search behavior | Feedback loop for ranking and future improvements |

This model is optimized around one stable material identity, immutable versions, and flexible relationships. That combination supports discovery better than a type-specific schema because it keeps search, tags, and links in the same retrieval path.

**[RECOMMEND]** The simplest deployment model is a single application with one relational database, one file store for assets, and one background worker if needed. For the MVP, SQLite with a persistent volume is enough if the hosting environment is simple and the dataset is still small; Postgres becomes the better choice only if persistence, concurrency, or future multi-user scaling starts to matter. Keep search in-process or in-database at first rather than introducing a separate search service.

The minimal model is fast to build and easy to self-host, but it trades away some future scaling headroom. Adding a separate search stack, message queue, or microservices now would slow the founder down without solving a problem they have not proven yet.

---

## 6. Build Sequencing

**[RECOMMEND]** Build in phases that get the founder to real capture and retrieval as early as possible.

**Week 1: capture and basic retrieval**
- Build: materials, immutable versions, blocks, tags, attachments, a simple recent list, and basic keyword search over titles, tags, and content.
- Defer: semantic search, cross-material graph browsing, advanced diff views, execution, analytics.
- Why: this gets real study material into the system immediately and tests whether the founder will actually keep using it.

**Weeks 2–3: make retrieval trustworthy**
- Build: better ranking, result previews, duplicate suppression, filter chips, related-material links, and a compare view for versions.
- Defer: multi-tenant concerns, collaboration, heavy automation, and deep search infrastructure.
- Why: this is where the two core pain points start to bend. The founder can now find old material with less guessing and compare snippet evolution when needed.

**Later: broaden discovery and polish the model**
- Build: semantic suggestions, saved searches, browsing by topic clusters, stronger relation types, richer image handling, and optional execution helpers.
- Defer: only if proven unnecessary, not because the platform cannot support them.
- Why: these features help when the founder has enough real content for patterns to emerge.

Sequencing calls:
- Day one must include materials, versions, blocks, tags, and attachments. Those are hard to retrofit later because they define the identity and retrieval surface of the content. Relations and saved searches can be added later without painful migration if the base IDs are stable.
- The first search mode to address is irrelevance or buried results. Overload gets partially improved by the same ranking work, while the “not knowing what to search for” problem can wait. The interim cost is that discovery will still rely on the founder having some idea of the topic name.
- Version surfacing should use a real version chain in v1. Flat naming can work only as a temporary UI trick, not as the storage model, because the founder’s promise is comparison over time and that is hard to reconstruct later.

The expensive retrofit risk is version history and identity. If those are delayed, the platform will have to rework how materials are stored just to support the core study workflow.

---

## 7. Discovery Questions

The founder should answer these before committing to the next layer of build:
- How much of the product should adapt to code-heavy domains versus stay uniform across all content ratios?
- What is the smallest useful way to show version evolution without making the interface feel cluttered?
- Which search failure mode matters most after the first usable MVP: relevance, overload, or not knowing what to search for?
- How much of search quality should come from indexing and structure versus from labeling habits and naming discipline?
- If the tool later becomes multi-tenant, which parts must stay constant now and which can be redesigned later?
- Does the founder want validation after week 1 on real study material, or is a longer setup phase acceptable before the tool feels useful?

---

## Output Format

Use the section headers above. Include tables where a data model or matrix is requested. Keep prose tight; this is a working discovery document, not a pitch deck. Tradeoffs should be explicit, and open decisions should remain open unless a recommendation is marked.
