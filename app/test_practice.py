"""Entrant Practice Test Suite.

Drives /app/controller.py through the full protocol ; including the two-message metered probe exchange
at Stage 3 ; against the five local sessions in practice_sessions.json, then scores each with
public_model.simulate_session. Practice sessions carry a visible `hidden` block (regime, drift, probe
noise) so readouts can be generated locally and so you can see whether your inference was right. The
sealed evaluation corpus uses different draws.
"""

import json
import subprocess
import sys
from pathlib import Path

import public_model as M

APP_DIR = Path(__file__).parent


def run_session(case):
    proc = subprocess.Popen(
        [sys.executable, "-B", "-s", "-u", str(APP_DIR / "controller.py")],
        cwd=str(APP_DIR),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    def exchange(stage, key, data):
        proc.stdin.write(json.dumps({"stage": stage, key: data}) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            raise RuntimeError(
                f"Controller exited at Stage {stage}: {proc.stderr.read()[:400]}"
            )
        return json.loads(line)

    H = case["hidden"]
    try:
        replies = {}
        replies["1"] = exchange(1, "profile", case["profile"])
        replies["2"] = exchange(2, "optics", case["optics"])
        replies["3a"] = exchange(3, "assay", case["assay"])
        sel = replies["3a"].get("probeSelection", [])
        readouts = {
            str(pid): round(
                M.probe_expected(pid, H["regime"], H["drift"]) + H["noise"][pid], 4
            )
            for pid in sel
        }
        replies["3b"] = exchange(3, "probeReadouts", readouts)
        replies["4"] = exchange(4, "quench", case["quench"])
        replies["5"] = exchange(5, "kinetics", case["kinetics"])
        replies["6"] = exchange(6, "harvest", case["harvest"])
        res = M.simulate_session(case, replies)
        hyps = M.consistent_hypotheses({int(k): float(v) for k, v in readouts.items()})
        diag = (
            f"probes={sel} hypotheses={len(hyps)} true={H['regime']}/{H['drift']:+.3f} "
            f"yield={res['isolatedYieldPercent']:.1f}% purity={res['productPurityPercent']:.1f}% "
            f"energy={res['totalPhotonEnergyJoules']:.0f}J (probes {res['probeEnergyJoules']:.0f}J) "
            f"exotherm={res['channelExothermDeltaTC']:.1f}C oligomer={res['oligomerByproductPercent']:.2f}% "
            f"fails={[k for k, v in res['invariants'].items() if not v]}"
        )
        return res["passed"], diag
    except Exception as e:
        return False, str(e)
    finally:
        try:
            proc.stdin.close()
            proc.terminate()
            proc.wait(timeout=1)
        except Exception:
            pass


def main():
    sessions = json.loads((APP_DIR / "practice_sessions.json").read_text())
    passed = 0
    for s in sessions:
        ok, msg = run_session(s)
        print(f"[{'PASS' if ok else 'FAIL'}] {s['id']}: {msg}")
        passed += ok
    print(f"\nPractice evaluation complete: {passed}/{len(sessions)} passed")
    if passed != len(sessions):
        sys.exit(1)


if __name__ == "__main__":
    main()
