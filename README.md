# Virtual Lab: photochemical control

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

Successful execution of this exact version was not established in the reviewed execution records. An older version has successful reference receipts; those results do not validate this version.

The historical evidence concerns the source version. This publication separates public inputs from private evaluation material and cleans documentation. No new task execution or model trial was performed for this publication, and the cleaned repository has not been revalidated end to end.

## Reference and verifier

Reference implementations, held-out cases, expected results and grading code are kept in the private repository `science-task-solutions`, under `VirtualLabPhotochemicalControl/`. They are excluded from this public repository. The public practice inputs and worked examples remain public by design.
