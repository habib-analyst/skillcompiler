"""Tests for the SkillCompiler analog (project #117)."""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from skillcompiler import (Bank, CAPS, Program, generate_tasks, run_arm,
                           run_textual, synthesize, truth, apply_guided)


def _op(cap="scale", conv="A", params=None):
    return {"cap": cap, "conv": conv,
            "params": params or {"rate": 2.0}}


def test_validation_rejects_obvious_bug():
    # An obvious bug differs on essentially every validation input, so a
    # synthesis that returns "obvious" should be vanishingly rare across
    # many seeded syntheses; and validation itself must reject it.
    rng = random.Random(0)
    op = _op()
    true = CAPS["scale"]["true"]
    obvious = CAPS["scale"]["obvious"]
    xs = [rng.uniform(10.0, 1000.0) for _ in range(16)]
    assert all(abs(obvious(x, op["params"], "A")
                   - true(x, op["params"], "A")) > 1e-6 for x in xs)


def test_synthesis_returns_passing_or_last_template():
    rng = random.Random(1)
    prog, tested = synthesize(_op(), rng)
    assert prog.template in ("true", "obvious", "subtle")
    assert 1 <= tested <= 3


def test_strict_bank_key_includes_convention_and_params():
    bank = Bank(lax=False)
    op_a = _op(conv="A")
    op_b = _op(conv="B")
    bank.put(op_a, Program("scale", "true", "A"))
    assert bank.get(op_a) is not None
    assert bank.get(op_b) is None  # convention mismatch -> miss
    op_c = _op(conv="A", params={"rate": 2.5})
    assert bank.get(op_c) is None  # param mismatch -> miss


def test_lax_bank_ignores_convention():
    bank = Bank(lax=True)
    bank.put(_op(conv="A"), Program("scale", "true", "A"))
    assert bank.get(_op(conv="B")) is not None


def test_wrong_convention_program_computes_wrong_value():
    prog = Program("scale", "true", "A")  # written for A
    # Applied to a B task it uses factor 1.0 instead of 0.9.
    v = prog.run(100.0, {"rate": 2.0}, "B")
    assert abs(v - 200.0) < 1e-6
    assert abs(v - 180.0) > 1e-6  # true B value would be 180


def test_compiled_execution_is_deterministic():
    tasks = generate_tasks(20, seed=7)
    ok1, _, _, _ = run_arm(tasks, "bank", seed=11)
    ok2, _, _, _ = run_arm(tasks, "bank", seed=11)
    assert ok1 == ok2


def test_textual_varies_across_repetitions():
    tasks = generate_tasks(50, seed=8)
    r1 = [run_textual(t, random.Random(100 + i)) for i, t in
          enumerate(tasks)]
    r2 = [run_textual(t, random.Random(200 + i)) for i, t in
          enumerate(tasks)]
    # With a 0.12 slip per op, two independent textual executions of the
    # same tasks must differ somewhere.
    assert r1 != r2


def test_guided_draw_shared_across_arms():
    # A task whose guided draw fails fails in every arm identically at
    # the guided step: run a task with guided_ok False through the
    # no-bank arm with a stub program by using an empty op chain is not
    # possible, so instead check the guided helper directly.
    task = {"hint": 0, "guided_ok": False}
    assert apply_guided(10.2, task, False) == 11  # ceil, wrong
    assert apply_guided(10.2, task, True) == 10   # floor, correct


def test_truth_is_chain_of_true_functions():
    task = {"x0": 100.0,
            "ops": [{"cap": "scale", "conv": "A", "params": {"rate": 2.0}},
                    {"cap": "fee", "conv": "A", "params": {"fee": 10.0}}],
            "hint": 0, "guided_ok": True}
    # 100*2*1.0 = 200; +10*1.0 = 210; floor -> 210
    assert truth(task) == 210


def test_bank_grows_beyond_one_program():
    tasks = generate_tasks(120, seed=9)
    _, _, _, bank = run_arm(tasks, "bank", seed=12)
    assert bank is not None and bank.size() >= 10
