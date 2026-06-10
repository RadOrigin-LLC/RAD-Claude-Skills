# Product Requirements — <PROJECT_NAME>

**Updated:** <YYYY-MM-DD>
**Status:** Living product authority. Implementation is validated against this file.
This describes what the product *does and must do now* — not the original wish list.
Supersede old wording in place; move retired notes to `docs/archive/`.

<!-- THE ONE RULE: write what the product DOES and MUST DO, not what you dream it
     becomes. Dreams and future versions live in docs/plan.md's Release map, not
     here. A PRD full of someday-features can't validate anything.

     Don't want to write this by hand? /rad-planner:plan interviews you and drafts
     every section from your own answers, confirmed one section at a time. -->

## Purpose

<One or two sentences: what this product is and who it's for.
 ✅ "A URL shortener for our internal tools — paste a long link, get a short one."
 ❌ "A revolutionary next-generation link management platform.">

## Users & primary workflow

<Who uses it, and the ONE workflow that must work end-to-end.
 ✅ "A team member pastes a URL, gets a short code, and shares it; anyone clicking
    it lands on the original page."
 ❌ "Various stakeholders leverage the system for diverse use cases.">

- <Who uses it, and the main flow they complete.>

## In scope — current product behavior

<The behaviors the product currently commits to — checkable, present tense.
 ✅ "The same URL always returns the same short code."
 ❌ "Robust link handling.">

- <The behaviors the product currently commits to.>

## Non-goals

<Things you are deliberately NOT building — explicit foreclosures, not just "not
 yet." These protect you from scope creep and protect your coding agent from
 inventing features.
 ✅ "No user accounts — links are anonymous by design."
 ❌ "Misc improvements TBD.">

- <Deliberately NOT building this.>

## Acceptance criteria

<Observable, checkable conditions that define "the product behaves correctly."
 If you can't tell whether it passed, it isn't a criterion.
 ✅ "Visiting a short link redirects to the original URL in under a second."
 ❌ "The app should feel fast and reliable.">

- <Observable conditions that define "the product behaves correctly.">

<!-- Add sections as the product grows (e.g. AI authority boundaries, data rules).
     Keep each durable fact in ONE home; link rather than duplicate. -->
