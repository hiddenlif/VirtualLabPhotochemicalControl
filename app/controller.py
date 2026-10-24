"""Photochemical Reaction Controller ; implement this file.

Newline-delimited JSON over stdin/stdout. See /app/SPEC.md for the protocol. Stage 3 is a two-message
exchange: first an `assay` message carrying the diagnostic probe menu (reply with `probeSelection`),
then a `probeReadouts` message carrying the readouts you paid for (reply with your compensation trims).
The kinetic regime and quantum-yield drift are never disclosed ; infer them from the readouts.
"""

import json
import sys


class PhotochemicalController:
    def stage1_feed_profile(self, profile):
        raise NotImplementedError

    def stage2_optics_setup(self, optics):
        raise NotImplementedError

    def stage3_probe_selection(self, assay):
        raise NotImplementedError

    def stage3_compensate(self, readouts):
        raise NotImplementedError

    def stage4_quench_allocation(self, quench):
        raise NotImplementedError

    def stage5_kinetic_branch(self, kinetics):
        raise NotImplementedError

    def stage6_harvest(self, harvest):
        raise NotImplementedError


def main():
    c = PhotochemicalController()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        stage = msg.get("stage")
        if stage == 1:
            reply = c.stage1_feed_profile(msg["profile"])
        elif stage == 2:
            reply = c.stage2_optics_setup(msg["optics"])
        elif stage == 3 and "assay" in msg:
            reply = c.stage3_probe_selection(msg["assay"])
        elif stage == 3 and "probeReadouts" in msg:
            reply = c.stage3_compensate(msg["probeReadouts"])
        elif stage == 4:
            reply = c.stage4_quench_allocation(msg["quench"])
        elif stage == 5:
            reply = c.stage5_kinetic_branch(msg["kinetics"])
        elif stage == 6:
            reply = c.stage6_harvest(msg["harvest"])
        else:
            raise ValueError(f"Unknown message: {list(msg)}")
        print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
