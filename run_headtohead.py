"""Head-to-head run for #117 skillcompiler (seed 117002, n=1200)."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from skillcompiler import (bootstrap_diff, bootstrap_rate, generate_tasks,
                           mean, run_arm, run_textual, truth)

SEED = 117002
N = 1200
tasks = generate_tasks(N, SEED)
arms = {}
oks = {}
for arm in ("textual", "nobank", "bank", "bank_nogate", "bank_lax"):
    ok, syn, hits, bank = run_arm(tasks, arm, seed=SEED + 100)
    oks[arm] = ok
    arms[arm] = {"success": mean(ok),
                 "syn_per_task": mean(syn),
                 "hit_rate": mean(hits) / 3.0,
                 "bank_size": bank.size() if bank is not None else 0}

# Textual flip: first 400 tasks, K=3 fresh textual executions each.
flip_flags = []
for i, t in enumerate(tasks[:400]):
    outs = [run_textual(t, random.Random(SEED + 5000 + 10 * i + k))
            for k in range(3)]
    tt = truth(t)
    oks_rep = [abs(o - tt) <= 1e-6 for o in outs]
    flip_flags.append(len(set(oks_rep)) > 1)
flip_rate, flip_ci = bootstrap_rate([1.0 if f else 0.0 for f in flip_flags],
                                    seed=999)

# Paired diffs.
def diff(a, b):
    m, ci = bootstrap_diff(oks[a], oks[b], seed=999)
    return {"mean": m, "ci95": list(ci)}

diffs = {
    "bank_minus_textual": diff("bank", "textual"),
    "bank_minus_nobank": diff("bank", "nobank"),
    "bank_minus_nogate": diff("bank", "bank_nogate"),
    "bank_minus_lax": diff("bank", "bank_lax"),
}

# Benign bound: among tasks textual succeeds on, bank success rate.
t_ok_idx = [i for i, v in enumerate(oks["textual"]) if v]
benign = mean([oks["bank"][i] for i in t_ok_idx]) if t_ok_idx else 0.0

bars = {
    "D1_flip_ge_0.25_and_ci_lo_ge_0.18":
        flip_rate >= 0.25 and flip_ci[0] >= 0.18,
    "D2_textual_success_le_0.90": arms["textual"]["success"] <= 0.90,
    "M1_bank_minus_textual_ge_0.08_and_ci_lo_ge_0.03":
        diffs["bank_minus_textual"]["mean"] >= 0.08
        and diffs["bank_minus_textual"]["ci95"][0] >= 0.03,
    "M2_bank_cost_le_0.50_x_nobank":
        arms["bank"]["syn_per_task"]
        <= 0.50 * arms["nobank"]["syn_per_task"],
    "M3_bank_minus_nogate_ge_0.30_and_ci_lo_ge_0.20":
        diffs["bank_minus_nogate"]["mean"] >= 0.30
        and diffs["bank_minus_nogate"]["ci95"][0] >= 0.20,
    "M4_bank_minus_lax_ge_0.30_and_ci_lo_ge_0.20":
        diffs["bank_minus_lax"]["mean"] >= 0.30
        and diffs["bank_minus_lax"]["ci95"][0] >= 0.20,
    "M5_bank_minus_nobank_ge_minus_0.03_and_ci_lo_ge_minus_0.08":
        diffs["bank_minus_nobank"]["mean"] >= -0.03
        and diffs["bank_minus_nobank"]["ci95"][0] >= -0.08,
    "B1_benign_ge_0.95": benign >= 0.95,
}
out = {"meta": {"seed": SEED, "n": N},
       "arms": arms,
       "flip": {"rate": flip_rate, "ci95": list(flip_ci),
                "n_tasks": 400, "k_reps": 3},
       "diffs": diffs,
       "benign": {"n_textual_success": len(t_ok_idx),
                  "bank_success_on_those": benign},
       "bars": bars,
       "all_bars_pass": all(bars.values())}
base = Path(__file__).resolve().parent / "results"
(base / "headline.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
