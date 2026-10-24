# Continuous-Flow Photochemical Reactor Control Specification v20

Implement `/app/controller.py`. The controller communicates with the reactor harness over stdin and stdout using newline-delimited JSON across a 6-stage continuous-flow photochemical synthesis horizon. Physical formulas, constants, the diagnostic-probe observation model and a local practice simulator are in `/app/public_model.py`; run `python3 test_practice.py` against `/app/practice_sessions.json`.

**Two quantities are never disclosed by the harness:** the run's kinetic regime (one of three) and its systemic quantum-yield drift. They can only be recovered from the diagnostic probe readouts you pay for at Stage 3, and every later decision depends on them.

---

## Protocol Lifecycle

### Stage 1: Feed Profile & Initial Flow Staging
- **Input**: `{"stage": 1, "profile": {...}}` ; `sessionId`, `feedConcentrations` (`substrateA`, `reactantB`, `catalystMolPercent`), Arrhenius parameters `activationEnergyJoulePerMol`, `preExponentialFactor`, dimerization parameters `dimerizationActivationEnergyJoulePerMol`, `dimerizationPreExponentialFactor`, `targetTemperatureC`, `totalPhotonBudgetJoules` (1200.0), `targetPurityMin` (95.0), `targetYieldMin` (85.0), `targetConversionEfficiency` (0.95).
- **Reply**: `{"flowRateUlMin": float, "initialLedPowerPercent": float}` with `flowRateUlMin` in `[50.0, 500.0]`, `initialLedPowerPercent` in `[10.0, 100.0]`.
- Residence time $\tau = 250.0\,\mu\text{L} / (Q/60)$; optical power $P = 3.0\,\text{W} \times \text{power}\%/100$.

### Stage 2: Optical Wavelength & Temperature Staging
- **Input**: `{"stage": 2, "optics": {...}}` ; `catalystAbsorbancePeakNm`, `molarExtinctionCoefficient`, `channelVolumeUl`, `pecletNumber`.
- **Reply**: `{"ledWavelengthBand": "blue_450nm" | "violet_420nm" | "uva_365nm", "reactorTemperatureC": float}` with temperature in `[20.0, 65.0]`.
- Gaussian spectral overlap ($\sigma_\lambda = 10$ nm) sets $f_{\text{abs}} = 1 - 10^{-A}$; temperature sets $k_r = A_0 e^{-E_a/RT}$.

### Stage 3: Metered Diagnostic Probes & Drift Compensation (two messages)
**3a ; probe selection.**
- **Input**: `{"stage": 3, "assay": {...}}` ; `measuredConversionPercent`, `byproductOligomerPercent`, `apparentResidenceTimeSec`, plus the public probe contract: `probeMenu` (four candidate pulses, ids 0-3), `probeBudget` (2), `probeEnergyJoules` (155.0 per probe), `probeNoise` (0.02). **No drift value and no regime is included.**
- **Reply**: `{"probeSelection": [ids]}` ; at most `probeBudget` distinct ids. Each selected probe consumes `probeEnergyJoules` from the same 1200 J photon budget the productive run must fit inside. Exceeding the budget fails the session.
- Observation model (public): for probe $p$ under true `(regime, drift)`,
  $$r_p = \text{base}_p + \text{regimeOffset}_p[\text{regime}] + \text{driftGain}_p \cdot \text{drift} + \varepsilon,\quad |\varepsilon| \le 0.02$$
  with `drift` in `[-0.15, 0.15]` and `regime` in `{photobleaching_fade, thermal_oligomer_runaway, catalyst_poisoning}`. `public_model.consistent_hypotheses(readouts)` returns every `(regime, drift)` consistent with a set of readouts. Not every probe pair separates all three regimes; choose probes that leave a single consistent hypothesis.

**3b ; readouts & compensation.**
- **Input**: `{"stage": 3, "probeReadouts": {"<id>": float, ...}}` ; the noisy readouts for the probes you selected, nothing else.
- **Reply**: `{"irradianceTrimPercent": float, "flowRateAdjustmentUlMin": float}`.
- Uncompensated drift $\Delta\Phi = \text{drift} + \Delta P/50$ collapses conversion when negative and drives quadratic radical dimerization when positive.

### Stage 4: Stoichiometric Radical Scavenger Quench Allocation
- **Input**: `{"stage": 4, "quench": {...}}` ; `scavengerConcentrationMolar`, `reagentQuenchCapacity` (2).
- **Reply**: `{"quenchInjections": [{"flowRateUlMin": float}, {"flowRateUlMin": float}]}` ; exactly two injections; total flow must match the radical flux $Q_{\text{eff}}[R^\bullet]/C_q$. Under-quenching breaches the oligomer ceiling; over-quenching (ratio > 1.20) contaminates the harvest.

### Stage 5: Regime-Specific Mitigation
- **Input**: `{"stage": 5, "kinetics": {...}}` ; `reactionEnthalpyKJPerMol`, `exothermDeltaT`. **The regime is not included**; act on the regime you inferred at Stage 3.
- **Reply** ; exactly one of:
  - `{"pulsedDutyCyclePercent": float}` in `[40.0, 60.0]` for `photobleaching_fade` (otherwise catalytic turnover drops 40%);
  - `{"emergencyCoolingTempC": float}` in `[12.0, 20.0]` for `thermal_oligomer_runaway` (otherwise the exotherm rises by +6.5 °C and breaches the ceiling);
  - `{"catalystReloadMolPercent": float}` in `[0.3, 0.6]` for `catalyst_poisoning` (otherwise conversion falls to 55%).
- A mitigation for the wrong regime is scored as no mitigation.

### Stage 6: Harvest & Fraction Collector Elution Window
- **Input**: `{"stage": 6, "harvest": {...}}` ; `accumulatedPhotonEnergyJoules`, `estimatedCrudeYieldPercent`.
- **Reply**: `{"fractionCollectorWindowSec": [t_start, t_end]}` with `t_start < t_end`, centred on the effective residence time with Taylor-Aris dispersion $\sigma_P = \tau/\sqrt{Pe\cdot Q/120}$ (≈ ±2.25 σ). Too narrow loses yield; too wide collects the solvent front and oligomer tail.

---

## Compound Invariants (all must hold on every session)
1. Product purity ≥ 95.0%
2. Isolated yield ≥ 85.0%
3. Total photon energy ≤ 1200.0 J ; accumulated + **probe energy (155 J per probe)** + active irradiation $3.0\,\text{W}\cdot P_{\text{eff}}\cdot\tau$
4. Channel exotherm ΔT ≤ 8.0 °C
5. Exactly 2 quench injections, total flow ≥ 2.0 µL/min; probe selection ≤ 2 probes
6. Oligomer byproduct ≤ 2.5%

The photon budget is shared: energy spent on probes is unavailable to the productive run, and energy saved by skipping probes leaves the regime and drift unknown.
