---
name: propro-package-standards
description: How P. likes to build and maintain the propro package (Python toolkit for calculating and visualizing protein biochemical/biophysical properties). Covers README/documentation standards, pre-commit testing discipline, commit and PR description format, codebase hygiene sweeps for dead code and stale comments, and the correctness-first-then-performance order for new property calculators. Use this skill whenever creating or modifying code in propro (core, motifs, or interfaces), writing or reviewing its README, preparing a commit or PR, adding a new property/visualization, or cleaning up a module. Trigger even if the user doesn't say "skill" or name these practices explicitly — e.g. "I'm about to commit this", "can you clean up this file", "let's speed this up", or "write the README".
---

# Propro Package Engineering Standards

Working conventions for building and extending `propro`. These are how P. works on this package, not one-off rules for a single change. When in doubt, prefer the convention here over inventing a new pattern.

The throughline: propro exists to give fast, trustworthy answers about a protein's basic properties — the kind of thing someone checks before or during wet-lab work. That means correctness and clarity come first, every property calculator should be easy to verify by hand or against a known reference, and the package should stay easy to extend (new properties, new protein classes under `propro.motifs`, new external interfaces under `propro.interfaces`) without eroding trust in what's already there.

## 1. README quality

The README is the entry point for both P. and anyone else (including future-you) returning to the package after months away. A repo without a good README is effectively undocumented, no matter how good the code is.

`README.md` should contain, in this order:

1. **One-paragraph summary** — what the package does and what kind of problem it addresses.
2. **Quick start** — the smallest possible sequence of commands to go from a fresh clone to a working result on a sample sequence. This should be copy-pasteable and actually tested, not aspirational.
3. **Detailed installation** — environment setup, dependency versions (BioPython, pandas, matplotlib, ...), and any known platform gotchas.
4. **Module overview** — a short (2-4 sentence) description of each module (`core`, and each submodule under `motifs`/`interfaces` as they land), what input it expects and what output it produces. Each entry can link out to a dedicated page (`docs/<module>.md`) for full details once a module grows beyond a few paragraphs of explanation — the README stays a map, the docs pages hold the territory.
5. **Project status / repo map** — brief note on what's stable vs. scaffolded/placeholder, and where to find tests and examples.

Keep the README itself short. If a section is growing past a few paragraphs, that's a sign it wants to become its own `docs/` page with a link from the README instead.

## 2. Run the full test suite before every commit

Tests run before the commit happens, not after, and not just for the files that changed. A green local test suite is the minimum bar for a commit to exist — it's what keeps `main` (and every commit on it) bisectable and trustworthy.

- Run the complete suite (`pytest`), not a subset, even when the change feels small or unrelated to most of the codebase. Small, "obviously safe" changes (e.g. tweaking a report formatter) are exactly the ones that cause surprising breakage elsewhere.
- New property or visualization functions get tests that check them against a known reference where one exists (e.g. a well-characterized protein with published MW/pI/instability values), not just "it runs without throwing."
- If tests are slow, that's a problem to solve rather than a reason to skip them before commit — though most propro calculations should be fast enough that this rarely comes up (see §5).
- If a test fails and the fix isn't obvious, do not commit around it (e.g. by narrowing the diff or skipping the test) without flagging it explicitly — silently weakening test coverage to get a commit through defeats the purpose.
- If a new module has no tests yet for the code being touched, treat adding at least minimal coverage as part of the change, not a follow-up.
- If a required dependency (e.g. BioPython) isn't available in the environment, guard the affected tests with `pytest.importorskip(...)` so the suite degrades gracefully rather than silently passing or hard-failing everywhere.

## 3. Commit and PR descriptions

Every commit (and PR, where applicable) gets a real description, not just a one-line summary of the diff. The goal is that someone reading the log later understands *why* the change happened and what's known to still be missing, without having to read the diff itself.

Every description includes:

- **What changed and why** — the motivation, not just a restatement of the diff.
- **How it was verified** — which tests were run, and any manual verification for things tests don't cover (e.g. visual inspection of a generated plot, or a hand-computed check on a known reference sequence).
- **Future work** — a short, explicit section noting follow-ups, known limitations, or things intentionally deferred (e.g. "extinction coefficient assumes no non-standard chromophores"). This is what keeps planned work from getting lost between conversations.

## 4. Sweep for loose ends before every commit (at minimum)

Before committing — and periodically even outside the commit cycle — scan the touched files (and ideally the broader codebase) for leftovers that accumulate silently in fast-moving scientific code:

- Commented-out code blocks left over from earlier approaches.
- Functions, classes, or imports that are no longer called from anywhere.
- Stale `TODO`/`FIXME` comments that no longer apply, or that have quietly become permanent.
- Config options, function parameters, or flags that are accepted but no longer do anything.
- Print/debug statements left in from troubleshooting.

This doesn't need to be a separate ceremony — fold it into the pre-commit check alongside the test run. A practical approach:

```bash
# unused functions/imports/variables
vulture . --min-confidence 80

# unused imports and basic dead-code lints
ruff check . --select F401,F841

# leftover commented-out code and stale markers (manual scan of the diff)
git diff --staged | grep -nE '^\+.*#.*\b(TODO|FIXME|XXX)\b'
```

If something looks dead but you're not sure, it's worth a quick grep for callers before deleting — but the default bias should be toward removing rather than accumulating. A codebase that only ever grows comments and unused branches becomes harder to trust over time.

## 5. Optimization order: correctness first, performance only if it's actually needed

Propro's whole premise is that its calculations are cheap and quick — that's a scope boundary, not just a performance goal (see the project description: this package deliberately does not host complex or lengthy analyses). So the order for any new property calculator is:

1. **Correctness first.** Get the calculation right with the simplest implementation that's clearly correct. Validate against a known/expected value — a published reference for a well-characterized protein, an independent formula, or a hand-computed example on a short toy sequence. Correctness bugs in a property calculator (e.g. an off-by-one in extinction coefficient, a wrong pKa table) are much more damaging here than slowness, since the whole point is that people trust the number without re-deriving it themselves.
2. **Only then, if it's actually slow, optimize.** Most propro-scoped calculations (sequence-based composition, MW, pI, instability index, simple structure lookups) shouldn't need this step at all. If something genuinely is slow enough to matter, profile before guessing, and prefer a better single-pass approach (e.g. vectorizing with NumPy/pandas) over reaching for parallelism.
3. **If a calculation would require heavy optimization or parallelism to be usable, that's a signal it may not belong in propro at all** — reconsider whether it fits the package's scope before investing engineering effort to make it fast.

## Applying this skill

When asked to add a new property calculator or visualization, validate it against a known reference before considering it done — "runs without erroring" is not the same as "correct."

When asked to review code, commit, or open a PR, walk through §2-4 explicitly (tests, description, loose-ends sweep) rather than assuming they're implicitly covered.

When asked to "speed this up," first check whether the calculation should be in propro at all (§5.3) before optimizing it.
