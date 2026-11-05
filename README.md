# skillcompiler (project #117)

Scripted analog of arXiv 2610.39508 "Compile Away Uncertainty":
textual agent skills re-interpreted every execution vs
executability-aware compilation into validated programs plus a program
asset bank with reuse.

## Run
- `python3 -m pytest tests/ -q` — 10 tests
- `python3 run_pilot.py` — pilot (seed 117001, n=300)
- `python3 run_headtohead.py` — head-to-head (seed 117002, n=1200)

## Headline (head-to-head, n=1200, paired bootstrap 2000)
| arm | success | syntheses/task |
|---|---|---|
| textual | 0.797 | 0.000 |
| fresh compile (no bank) | 0.937 | 3.000 |
| compiled + validated bank | 0.937 | 0.025 |
| bank, no validation gate | 0.515 | 0.025 |
| bank, lax (convention ignored) | 0.459 | 0.004 |

Textual flip rate across 3 repetitions: 0.328, CI [0.283, 0.375].
Bank − textual: +0.140, CI [0.119, 0.163]. All 8 PREREG bars pass.

## Scope honesty
Scripted analog only. The paper's figures (up to 32.33% improvement,
five benchmarks, six model families) are context only, never claimed
as reproduced. The textual slip rate is a stated disease-model
parameter; the reuse-cost, validation-gate, and compatibility effects
emerge from the candidate/validation/key mechanics.
