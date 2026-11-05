# PILOT PREREG — Project #117 `skillcompiler` (arXiv 2610.39508)

Written BEFORE any pilot number is observed. This file gates the pilot
only; the head-to-head PREREG is locked separately, after the pilot.

## Fixed before any number (G0 rules, from src/skillcompiler.py)
- Task = chain of 3 programmatic ops + 1 agent-guided op; ground truth
  = true-function composition with the guided op correct.
- Textual arm: per programmatic op, slip probability 0.12 replaces the
  true function with a random buggy template (fresh draw per execution).
- Compilation: shuffle the 3 candidate templates (true / obvious /
  subtle) with a seeded RNG, validate on 16 fresh examples, admit the
  FIRST template passing all examples.
- Bank key (strict): (capability, convention, params tuple).
  Lax arm keys on capability only (convention ignored).
- No-gate arm: strict keys, but admits the first shuffled template
  WITHOUT validation.
- Guided-op draw is generated once per task and shared by all arms.

## Pilot protocol
- Seed 117001, n=300 tasks (fresh stream, never reused for head-to-head).
- Arms: textual, nobank, bank, bank_nogate, bank_lax.
- Textual flip measurement: first 200 pilot tasks, K=3 independent
  textual executions each (fresh draws per repetition); flip = task
  outcome varies across the 3 repetitions.

## Pilot gates (ALL must pass, else KILL at the pilot gate)
- P1: textual flip rate >= 0.15 (the disease is real in this analog).
- P2: bank task success - textual task success >= +0.10.
- P3: bank syntheses per task <= 0.70 x nobank syntheses per task
  (the reuse mechanism actually reuses).
- P4: bank holds >= 10 distinct program assets at end of pilot
  (the bank is a real bank, not one program).
- P5: bank task success - bank_nogate task success >= +0.10
  (the validation gate, not mere compilation, carries the gain).

If any pilot gate fails, the project is KILLED at the pilot gate: no
bar-lowering, no re-seed, no rule change after seeing pilot numbers
except the pre-declared head-to-head bar placement (bars set BELOW
pilot values, never above, and never moved after head-to-head numbers
are observed).
