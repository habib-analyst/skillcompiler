"""SkillCompiler analog (project #117).

Scripted analog of arXiv 2610.39508 "Compile Away Uncertainty":
textual skills re-interpreted every execution vs executability-aware
compilation into validated programs + a program asset bank with reuse.

DESIGN (fixed in G0, before any pilot number):
- A task is a chain of 3 programmatic ops + 1 agent-guided op.
  Ground truth = compose the TRUE functions, guided op correct.
- Each capability has 3 candidate templates: correct, an obvious bug
  (differs on essentially every input), and a subtle bug (differs only
  inside a narrow input band). Compilation = shuffle the templates with
  a seeded RNG, validate each on N_VAL fresh examples, admit the FIRST
  template that passes all examples. Nothing about success rates is
  hard-coded: a template's fate emerges from whether its bug triggers
  on the validation examples and on the task inputs.
- A program is a template + the convention it was written for. Programs
  are param-generic (params are supplied by the task at execution).
- Bank key (strict arms) = (capability, convention, params tuple).
  Lax arm keys on capability only, ignoring convention: a program
  written for convention A applied to a convention-B task uses A's
  factor, so it computes the wrong value.
- Convention effect: FACTOR = {"A": 1.0, "B": 0.9} multiplies the
  capability's main parameter. A wrong-convention program is wrong
  whenever the parameter is nonzero (it always is here).
- Textual arm: per programmatic op, with probability SLIP the agent
  re-derives the op as a random buggy template instead of the true
  function (fresh draw per execution). This is the disease model:
  probabilistic re-interpretation. It is a parameter, stated openly;
  the load-bearing results are the reuse-cost, validation-gate, and
  compatibility effects, which are NOT parameters.
- Agent-guided op: a rounding-direction choice. Its success draw is
  generated once per task and SHARED by all arms (common random
  numbers), so arm differences come only from the programmatic ops.
- Task success: exact match (tol 1e-6) between arm output and truth.

No LLM, no network, no GPU. Pure Python, seeded, deterministic.
"""

import math
import random

FACTOR = {"A": 1.0, "B": 0.9}
SLIP = 0.12            # textual re-interpretation slip probability per op
GUIDED_OK = 0.95       # agent-guided op success probability (shared draw)
N_VAL = 16             # validation examples per synthesis
VALID_LO, VALID_HI = 10.0, 1000.0
TOL = 1e-6

# ---------------------------------------------------------------- caps
# true_fn(x, params, convention) -> float
# obvious_fn / subtle_fn: same signature; subtle differs only in BAND.


def _mk(true, obvious, subtle_band, subtle_fn):
    return {"true": true, "obvious": obvious,
            "band": subtle_band, "subtle": subtle_fn}


def _subtle(true, band, perturb):
    def f(x, params, conv):
        v = true(x, params, conv)
        if band[0] <= x <= band[1]:
            return perturb(v, x, params, conv)
        return v
    return f


CAPS = {
    "scale": _mk(
        lambda x, p, c: x * p["rate"] * FACTOR[c],
        lambda x, p, c: x * p["rate"] * FACTOR[c] + 37.0,
        (500.0, 512.0),
        _subtle(lambda x, p, c: x * p["rate"] * FACTOR[c],
                (500.0, 512.0),
                lambda v, x, p, c: v * 1.07)),
    "discount": _mk(
        lambda x, p, c: x * (1.0 - p["d"] * FACTOR[c]),
        lambda x, p, c: x - p["d"] * 100.0,
        (300.0, 312.0),
        _subtle(lambda x, p, c: x * (1.0 - p["d"] * FACTOR[c]),
                (300.0, 312.0),
                lambda v, x, p, c: v * 0.93)),
    "fee": _mk(
        lambda x, p, c: x + p["fee"] * FACTOR[c],
        lambda x, p, c: x - p["fee"] * FACTOR[c],
        (100.0, 112.0),
        _subtle(lambda x, p, c: x + p["fee"] * FACTOR[c],
                (100.0, 112.0),
                lambda v, x, p, c: v + 9.0)),
    "tax": _mk(
        lambda x, p, c: x * (1.0 + p["t"] * FACTOR[c]),
        lambda x, p, c: x + p["t"],
        (700.0, 712.0),
        _subtle(lambda x, p, c: x * (1.0 + p["t"] * FACTOR[c]),
                (700.0, 712.0),
                lambda v, x, p, c: v * 1.05)),
    "clamp": _mk(
        lambda x, p, c: min(max(x, p["lo"]), p["hi"] * FACTOR[c]),
        lambda x, p, c: x,
        (200.0, 212.0),
        _subtle(lambda x, p, c: min(max(x, p["lo"]), p["hi"] * FACTOR[c]),
                (200.0, 212.0),
                lambda v, x, p, c: v + 13.0)),
    "shift": _mk(
        lambda x, p, c: x + p["shift"] * FACTOR[c],
        lambda x, p, c: x - p["shift"] * FACTOR[c],
        (800.0, 812.0),
        _subtle(lambda x, p, c: x + p["shift"] * FACTOR[c],
                (800.0, 812.0),
                lambda v, x, p, c: v - 11.0)),
}

PARAM_SETS = {
    "scale": [{"rate": r} for r in (1.5, 2.0, 2.5)],
    "discount": [{"d": d} for d in (0.10, 0.20, 0.30)],
    "fee": [{"fee": f} for f in (10.0, 20.0, 30.0)],
    "tax": [{"t": t} for t in (0.05, 0.10, 0.20)],
    "clamp": [{"lo": lo, "hi": hi} for (lo, hi) in
              ((50.0, 800.0), (20.0, 500.0), (100.0, 900.0))],
    "shift": [{"shift": s} for s in (5.0, 15.0, 25.0)],
}

# Families: (op capability, convention) triples + input range.
FAMILIES = [
    {"ops": [("scale", "A"), ("discount", "A"), ("fee", "A")],
     "xrange": (10.0, 200.0)},
    {"ops": [("scale", "B"), ("tax", "A"), ("clamp", "A")],
     "xrange": (10.0, 200.0)},
    {"ops": [("discount", "B"), ("fee", "B"), ("scale", "A")],
     "xrange": (500.0, 1500.0)},
    {"ops": [("tax", "B"), ("scale", "B"), ("discount", "A")],
     "xrange": (5.0, 50.0)},
    {"ops": [("fee", "A"), ("clamp", "B"), ("tax", "A")],
     "xrange": (100.0, 900.0)},
    {"ops": [("clamp", "A"), ("discount", "B"), ("fee", "B")],
     "xrange": (20.0, 300.0)},
]


def param_key(params):
    return tuple(sorted(params.items()))


# ---------------------------------------------------------------- tasks
def generate_tasks(n, seed):
    """Return a list of task dicts. Guided-op draw is fixed per task."""
    rng = random.Random(seed)
    tasks = []
    for i in range(n):
        fam = FAMILIES[rng.randrange(len(FAMILIES))]
        lo, hi = fam["xrange"]
        x0 = rng.uniform(lo, hi)
        ops = []
        for cap, conv in fam["ops"]:
            params = dict(rng.choice(PARAM_SETS[cap]))
            ops.append({"cap": cap, "conv": conv, "params": params})
        hint = rng.randrange(2)  # 0 -> floor, 1 -> ceil is correct
        guided_ok = rng.random() < GUIDED_OK
        tasks.append({"x0": x0, "ops": ops, "hint": hint,
                      "guided_ok": guided_ok})
    return tasks


def truth(task):
    v = task["x0"]
    for op in task["ops"]:
        v = CAPS[op["cap"]]["true"](v, op["params"], op["conv"])
    return math.floor(v) if task["hint"] == 0 else math.ceil(v)


def apply_guided(v, task, ok):
    if ok:
        return math.floor(v) if task["hint"] == 0 else math.ceil(v)
    return math.ceil(v) if task["hint"] == 0 else math.floor(v)


# ---------------------------------------------------------------- compilation
class Program:
    def __init__(self, cap, template, written_conv):
        self.cap = cap
        self.template = template  # "correct" | "obvious" | "subtle"
        self.written_conv = written_conv

    def run(self, x, params, task_conv):
        # A program uses the convention it was WRITTEN for, not the
        # task's convention. Strict retrieval guarantees they match;
        # lax retrieval does not, which is exactly the lax failure.
        fn = CAPS[self.cap][self.template]
        return fn(x, params, self.written_conv)


def synthesize(op, rng):
    """Validate shuffled candidates on N_VAL fresh examples.

    Returns (program, n_candidates_tested). The first candidate passing
    all examples wins; if none passes, the last tested is still returned
    (validation failure is recorded by the caller via template name).
    """
    cap, conv, params = op["cap"], op["conv"], op["params"]
    templates = ["true", "obvious", "subtle"]
    rng.shuffle(templates)
    examples = [rng.uniform(VALID_LO, VALID_HI) for _ in range(N_VAL)]
    true = CAPS[cap]["true"]
    for j, t in enumerate(templates):
        fn = CAPS[cap][t]
        if all(abs(fn(x, params, conv) - true(x, params, conv)) <= TOL
               for x in examples):
            return Program(cap, t, conv), j + 1
    return Program(cap, templates[-1], conv), len(templates)


class Bank:
    """Program asset bank. Strict keys (cap, conv, params); lax keys cap."""

    def __init__(self, lax=False):
        self.lax = lax
        self.store = {}

    def _key(self, op):
        if self.lax:
            return (op["cap"],)
        return (op["cap"], op["conv"], param_key(op["params"]))

    def get(self, op):
        return self.store.get(self._key(op))

    def put(self, op, prog):
        self.store[self._key(op)] = prog

    def size(self):
        return len(self.store)


# ---------------------------------------------------------------- arms
def run_textual(task, rng):
    v = task["x0"]
    for op in task["ops"]:
        if rng.random() < SLIP:
            t = rng.choice(["obvious", "subtle"])
            v = CAPS[op["cap"]][t](v, op["params"], op["conv"])
        else:
            v = CAPS[op["cap"]]["true"](v, op["params"], op["conv"])
    return apply_guided(v, task, task["guided_ok"])


def _run_compiled(task, rng, bank, validate):
    """bank=None -> fresh synthesis every op (no-bank arm).
    validate=False -> admit first shuffled candidate without checking."""
    v = task["x0"]
    syntheses = 0
    hits = 0
    for op in task["ops"]:
        prog = bank.get(op) if bank is not None else None
        if prog is not None:
            hits += 1
        else:
            syntheses += 1
            if validate:
                prog, _ = synthesize(op, rng)
            else:
                templates = ["true", "obvious", "subtle"]
                rng.shuffle(templates)
                prog = Program(op["cap"], templates[0], op["conv"])
            if bank is not None:
                bank.put(op, prog)
        v = prog.run(v, op["params"], op["conv"])
    return apply_guided(v, task, task["guided_ok"]), syntheses, hits


def run_arm(tasks, arm, seed):
    """Returns (successes list, syntheses per task list, hits list, bank).

    Arms: textual, nobank, bank, bank_nogate, bank_lax.
    """
    rng = random.Random(seed)
    ok, syn, hits = [], [], []
    bank = None
    if arm == "bank":
        bank = Bank(lax=False)
    elif arm == "bank_nogate":
        bank = Bank(lax=False)
    elif arm == "bank_lax":
        bank = Bank(lax=True)
    for task in tasks:
        t = truth(task)
        if arm == "textual":
            out = run_textual(task, rng)
            ok.append(abs(out - t) <= TOL)
            syn.append(0)
            hits.append(0)
        elif arm == "nobank":
            out, s, h = _run_compiled(task, rng, None, True)
            ok.append(abs(out - t) <= TOL)
            syn.append(s)
            hits.append(h)
        elif arm == "bank":
            out, s, h = _run_compiled(task, rng, bank, True)
            ok.append(abs(out - t) <= TOL)
            syn.append(s)
            hits.append(h)
        elif arm == "bank_nogate":
            out, s, h = _run_compiled(task, rng, bank, False)
            ok.append(abs(out - t) <= TOL)
            syn.append(s)
            hits.append(h)
        elif arm == "bank_lax":
            out, s, h = _run_compiled(task, rng, bank, True)
            ok.append(abs(out - t) <= TOL)
            syn.append(s)
            hits.append(h)
        else:
            raise ValueError(arm)
    return ok, syn, hits, bank


# ---------------------------------------------------------------- stats
def mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def bootstrap_diff(a, b, n_boot=2000, seed=999):
    """Paired bootstrap CI for mean(a) - mean(b); a, b are 0/1 lists."""
    rng = random.Random(seed)
    n = len(a)
    diffs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        diffs.append(mean([a[i] for i in idx]) - mean([b[i] for i in idx]))
    diffs.sort()
    lo = diffs[int(0.025 * n_boot)]
    hi = diffs[int(0.975 * n_boot)]
    return mean(a) - mean(b), (lo, hi)


def bootstrap_rate(xs, n_boot=2000, seed=999):
    rng = random.Random(seed)
    n = len(xs)
    vals = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(mean([xs[i] for i in idx]))
    vals.sort()
    return mean(xs), (vals[int(0.025 * n_boot)], vals[int(0.975 * n_boot)])
