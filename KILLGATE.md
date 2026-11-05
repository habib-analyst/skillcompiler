# KILLGATE — Project #117 `skillcompiler` — PASS (all gates)

Source: arXiv 2610.39508, "Compile Away Uncertainty: Self-Evolving
Agent Skills via Programmatic Compilation" (Yang et al.). Scripted
analog; $0, CPU only, no LLM calls.

## G0 — Harness: PASS
Runnable harness in src/skillcompiler.py: scripted agents executing
synthetic multi-op tasks from textual skills vs compiled programs, with
a program asset bank. One G0 bug was caught by tests (template-name
mismatch "correct" vs dict key "true") and fixed before any pilot
number was observed.

## G1 — Author-code recheck (fresh, by this builder, 2026-10-30): PASS
- Abstract page (arxiv.org/abs/2610.39508, fetched fresh): title,
  authors (Chengyu Yang et al.), 29 Oct 2026 submission all match;
  NO author code link — only arXiv's own third-party toggles
  (alphaXiv, CatalyzeX, DagsHub, Hugging Face, etc.). Abstract carries
  NO release statement (contrast #100, where the abstract announced a
  package).
- Full-text HTML (arxiv.org/html/2610.39508v1, 1584 lines, fetched
  fresh): find-tool validated on this page ("SkillCompiler" returns
  73 matches), and the following return ZERO matches: github, zenodo,
  4open, anonymous, "code is available", "data is available",
  "available at", "we release", "open source".
- The only "replication" hits are the phrase "replication axis" in
  statistical-notes text (repeated-evaluation axes, not a package),
  and the only "supplement" hit is "supplementary fraction" (a metric
  name, not supplementary materials). Neither is an author artifact.
- Conclusion: no author repo, no retrievable author package, no
  release sentence with a public location. G1 PASSES under both the
  narrow reading and the #100 lesson. No package was downloaded or
  inspected (none exists to inspect). If a located author package
  later appears, re-examine under the #100 precedent.

## Pilot gate: PASS
PILOT_PREREG.md written before any pilot number. Seed 117001, n=300:
textual flip 0.360 CI [0.300, 0.425]; bank-textual +0.123 CI [0.083,
0.167]; bank syntheses 0.10/task vs nobank 3.00/task; bank holds 30
assets; bank-nogate +0.677. All five pilot gates P1-P5 passed.

## PREREG: locked before head-to-head, zero amendments
PILOT_PREREG (10:31:29) < pilot (10:31:41) < PREREG (10:31:59) <
headline (10:32:35) UTC. Decision rule "ANY locked bar fails → KILL".
No amendments.

## G2 — Disease: PASS (2/2, fresh seed 117002, n=1200)
- D1: textual flip rate 0.3275, CI [0.2825, 0.3750] (bars >= 0.25 /
  lo >= 0.18). PASS
- D2: textual task success 0.7967 (bar <= 0.90). PASS

## G3 — Mechanism + benign bound: PASS (6/6)
- M1: bank - textual +0.1400, CI [0.1192, 0.1625] (bars >= +0.08 /
  lo >= +0.03). PASS
- M2: bank syntheses 0.025/task vs nobank 3.000/task, ratio 0.008
  (bar <= 0.50x). Bank hit rate 0.9917; 30 assets. PASS
- M3: bank - bank_nogate +0.4217, CI [0.3933, 0.4500] (bars >= +0.30
  / lo >= +0.20) — the validation gate carries the gain. PASS
- M4: bank - bank_lax +0.4775, CI [0.4492, 0.5075] (bars >= +0.30 /
  lo >= +0.20) — ignoring convention collapses reuse. PASS
- M5: bank - nobank 0.0000, CI [-0.0083, +0.0083] (bars >= -0.03 /
  lo >= -0.08) — reuse costs nothing vs fresh compilation. PASS
- B1: among the 956 tasks textual succeeds on, bank succeeds on
  0.9812 (bar >= 0.95). PASS

## Determinism
SHA-256(results/headline.json) =
63b0486da8db10665d0a0fd7b176678be38fb14e5b210411d91bf4ef4d3ecf79.
Rerun on the same seed is byte-identical. Tests: 10 passed.

## Tautology guard (why this is not baked in)
No success rate for any arm is encoded in the harness. The textual
slip rate (0.12/op) is a disease-model parameter, stated openly in
PREREG.md; it sets the size of the textual-vs-compiled gap. The
load-bearing results emerge from mechanics, not parameters: the
validation gate (M3) emerges from candidate bugs triggering on
validation examples; the compatibility effect (M4) emerges from
wrong-convention programs computing wrong values; the reuse cost
(M2) emerges from key recurrence in the task stream; non-inferiority
(M5) emerges from validated programs being near-equivalent whether
fresh or reused. A bank holding a single program would prove nothing;
this bank holds 30 distinct assets with a 0.9917 hit rate.

## Verdict: SHIP
REPO NEEDED: habib-analyst/skillcompiler (builder does not push; the
GitHub App token cannot create repos).
