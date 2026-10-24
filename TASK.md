Your task is to implement `/app/controller.py` to operate a continuous-flow photoredox microreactor.

The controller communicates with the reactor test harness over standard input and standard output using newline-delimited JSON. Each stage exchanges one message pair across feed setup, wavelength selection, diagnostic probing, radical quenching, kinetic mitigation, and product collection.

Two quantities are never disclosed in the stage inputs: the quantum-yield drift and the active kinetic failure regime (photobleaching fade, thermal oligomerization, or catalyst poisoning). The only way to determine them is to spend part of the photon energy budget on diagnostic pulses during the probe phase and inspect the resulting sensor readouts. Sensor readouts carry zero-mean Gaussian noise. Because diagnostic pulses and the productive reaction share the same photon quota, only one or two pulses can be fired before the budget is exhausted.

Subsequent stages depend on this diagnosis. Irradiance and flow must be adjusted for the measured drift, radical scavenger metered to neutralize active intermediates without exceeding the quench ratio ceiling, and the appropriate countermeasure applied to the channel. Photobleaching requires duty-cycle pulsing, thermal runaway requires cooling, and catalyst poisoning requires reloading fresh catalyst.

Collection valves must then cut fractions that meet target purity and yield thresholds while staying within the total photon energy allowance. Interface schemas, rate constants, and refusal rules are documented in `/app/SPEC.md`, while `/app/public_model.py` provides the observation model and hypothesis consistency helpers. Test the controller locally with `python3 /app/test_practice.py` against `/app/practice_sessions.json`.
