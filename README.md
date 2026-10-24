# Virtual Lab Task: Photochemical Reactor Control

Choose diagnostic pulses for a simulated photoredox reactor, inspect their returned readings, and control flow, illumination, quenching, mitigation and product collection under shared resource limits.

**Task type:** Interactive simulated experimentation. **Source version:** 21.0.0.

All scientific specimens, measurements and instrument conditions are synthetic. These examples are not validated biological assays or clinical decision tools.

## Contents

- `TASK.md`: scientific task and required deliverable.
- `app/`: public scientific model, documentation and disclosed practice inputs where supplied.
- `Dockerfile`: the task's original dependency environment.

## Use

Build the environment with `docker build -t virtual-lab-photochemistry .`.

Implement `app/controller.py` using `TASK.md` and `app/SPEC.md`. Run the disclosed practice sessions inside the container:

```sh
docker run --rm -v "$PWD/app":/app virtual-lab-photochemistry python3 /app/test_practice.py
```

The public model and practice driver implement the probe/readout exchange and calculate the simulated process outcomes. The starter is not a completed solution.

## Execution evidence

On 2026-10-24 this published repository was run end to end: with the private reference installed in `app/`, the private grader passed 20 of 20 sessions (reward 1); the unchanged starter passed 0 of 20 (reward 0). These are local reference results in Docker, not blind solver results or platform approval.

## Reference and verifier

Reference implementations, held-out cases, expected results and grading code are kept in the private repository `science-task-solutions`, under `VirtualLabPhotochemicalControl/`. They are excluded from this public repository. The public practice inputs and worked examples remain public by design.
