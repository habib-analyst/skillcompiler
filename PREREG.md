# PREREG — Project #117 `skillcompiler` (arXiv 2610.39508)

Locked AFTER the pilot run and BEFORE any head-to-head run.
Decision rule: **ANY locked bar fails → KILL, no amendments.**
Post-hoc amendments are impermissible (the #97 veto).

## Pilot (seed 117001, n=300, already observed — bars set below pilot values)
- textual success 0.827; nobank 0.947; bank 0.950; bank_nogate 0.273;
  bank_lax 0.220.
- textual flip rate (200 tasks x 3 reps) 0.360, CI [0.300, 0.425].
- bank - textual +0.123, CI [0.083, 0.167].
- bank - nogate +0.677, CI [0.623, 0.727].
- bank syntheses 0.10/task (nobank 3.00/task); bank hit rate 0.967;
  bank holds 30 distinct assets; lax bank holds 5 (one per capability).
- Pilot gates P1-P5 all passed (see PILOT_PREREG.md).
- No pilot number is presented as a head-to-head result.

## Head-to-head protocol (fresh seed 117002, n=1200 tasks)
- Same task generator and arms as the pilot; arms share the task list
  and the per-task guided-op draw (common random numbers).
- Paired bootstrap: 2000 resamples over tasks, seed 999.
- Textual flip: first 400 head-to-head tasks, K=3 independent textual
  executions each (fresh draws per repetition).
- Syntheses per task: bank arms count only cache misses; nobank counts
  every programmatic op (3.00/task by construction).

## G2 — Disease bars (textual re-interpretation injects uncertainty)
- D1: textual flip rate >= 0.25 AND bootstrap CI lower bound >= 0.18.
- D2: textual task success <= 0.90 (point estimate).

## G3 — Load-bearing mechanism + benign bound
- M1: bank - textual task success mean >= +0.08 AND CI lower >= +0.03.
- M2: bank syntheses per task <= 0.50 x nobank syntheses per task
  (reuse actually avoids synthesis).
- M3: bank - bank_nogate task success mean >= +0.30 AND CI lower
  >= +0.20 (the validation gate, not mere compilation, carries the gain).
- M4: bank - bank_lax task success mean >= +0.30 AND CI lower >= +0.20
  (the compatibility check — capability+convention+params key — is
  load-bearing; ignoring convention collapses reuse).
- M5: bank - nobank task success mean >= -0.03 AND CI lower >= -0.08
  (reuse does not meaningfully cost correctness vs fresh compilation).
- B1 (benign bound): among tasks where the textual arm succeeds,
  the bank arm also succeeds in >= 0.95 of them (compilation rarely
  breaks a task textual execution already handled).

## Differentiation (stated before head-to-head, carried into PAPER.md)
- vs #56 tool-trace-audit / #77 detector-truth-gap / #85 harness-vcr:
  this is skill compilation + program-asset reuse, not trace truth,
  detector disagreement, or model-vs-harness attribution.
- vs #111 blindfold: this certifies nothing and audits no coin; the
  object is execution determinism via compiled programs, not
  certificate validity under information leakage.
- vs #115 prompt-lottery: the object is programmatic execution of
  skills, not judge-prompt sensitivity or aggregation.
- vs #110 poisoned-skills / #114 trust-region: no injection, no
  placement/trust structure; the "adversary" here is re-interpretation
  noise, not a payload.

## Scope limits (stated before head-to-head)
- Scripted analog only. The paper's figures (up to 32.33% improvement,
  five benchmarks, six model families, ALFWorld 98.26%) are CONTEXT
  ONLY and are never claimed as reproduced.
- The textual slip rate (0.12/op) is a disease-model parameter, stated
  openly: it sets the size of the textual-vs-compiled gap. The
  load-bearing results are the reuse-cost (M2), validation-gate (M3),
  and compatibility (M4) effects, which emerge from the candidate /
  validation / key mechanics, not from any success-rate parameter.
- Synthetic tasks only; no real repositories, no LLM agents, no SIEM.
- Bank applicability is capability+convention+params, not full
  semantic equivalence; the non-inferiority bar (M5) measures the cost
  of that choice.
