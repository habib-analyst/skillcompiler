"""Pilot run for #117 skillcompiler (seed 117001, n=300)."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from skillcompiler import (bootstrap_diff, bootstrap_rate, generate_tasks,
                           mean, run_arm, run_textual)

SEED = 117001
N = 300
tasks = generate_tasks(N, SEED)
res = {}
for arm in ("textual", "nobank", "bank", "bank_nogate", "bank_lax"):
    ok, syn, hits, bank = run_arm(tasks, arm, seed=SEED + 100)
    res[arm] = {"success": mean(ok),
                "syn_per_task": mean(syn),
                "hit_rate": mean(hits) / 3.0,
                "bank_size": bank.size() if bank is not None else 0}

# Textual flip: first 200 tasks, K=3 fresh textual executions each.
flip_flags = []
for i, t in enumerate(tasks[:200]):
    outs = [run_textual(t, random.Random(SEED + 1000 + 10 * i + k))
            for k in range(3)]
    from skillcompiler import truth
    tt = truth(t)
    oks = [abs(o - tt) <= 1e-6 for o in outs]
    flip_flags.append(len(set(oks)) > 1)
flip_rate, flip_ci = bootstrap_rate([1.0 if f else 0.0 for f in flip_flags],
                                    seed=999)

# Paired diffs vs textual / vs nogate on the pilot stream.
text_ok, _, _, _ = run_arm(tasks, "textual", seed=SEED + 100)
bank_ok, _, _, _ = run_arm(tasks, "bank", seed=SEED + 100)
nogate_ok, _, _, _ = run_arm(tasks, "bank_nogate", seed=SEED + 100)
# NOTE: run_arm with the same seed replays identical RNG streams, so
# these re-runs reproduce the res[arm] success lists exactly.
d_bank_text, ci_bt = bootstrap_diff(bank_ok, text_ok, seed=999)
d_bank_nogate, ci_bn = bootstrap_diff(bank_ok, nogate_ok, seed=999)

out = {"meta": {"seed": SEED, "n": N},
       "arms": res,
       "flip": {"rate": flip_rate, "ci95": list(flip_ci)},
       "diffs": {"bank_minus_textual": {"mean": d_bank_text,
                                        "ci95": list(ci_bt)},
                 "bank_minus_nogate": {"mean": d_bank_nogate,
                                       "ci95": list(ci_bn)}},
       "pilot_gates": {
           "P1_flip_ge_0.15": flip_rate >= 0.15,
           "P2_bank_minus_textual_ge_0.10": d_bank_text >= 0.10,
           "P3_bank_cost_le_0.70_x_nobank":
               res["bank"]["syn_per_task"]
               <= 0.70 * res["nobank"]["syn_per_task"],
           "P4_bank_size_ge_10": res["bank"]["bank_size"] >= 10,
           "P5_bank_minus_nogate_ge_0.10": d_bank_nogate >= 0.10}}
out["pilot_gate_pass"] = all(out["pilot_gates"].values())
Path(__file__).resolve().parent.joinpath(
    "results", "pilot.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
