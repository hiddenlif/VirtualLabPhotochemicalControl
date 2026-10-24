"""Photochemical Continuous-Flow Reactor Physics, Diagnostic-Probe Observation Model & Practice Simulator.

Governing physical equations for microreactor flow kinetics, optical absorption, photon energy
consumption, Arrhenius side-product formation, and fraction elution ; plus the public observation
model for the metered diagnostic probes. The per-run kinetic regime and quantum-yield drift are NOT
disclosed by the harness; they can only be recovered from paid-for probe readouts. `simulate_session`
is a local practice scorer for `practice_sessions.json` (whose sessions carry a visible `hidden` block
for self-checking). The sealed evaluation corpus is separate and non-derivable from this file.
"""

from __future__ import annotations

import math
from typing import Any

# Reactor Specifications
CHANNEL_VOLUME_UL = 250.0
OPTICAL_PATH_LENGTH_CM = 0.1
LED_MAX_OPTICAL_WATTS = 3.0
R_IDEAL = 8.314

# Compound Invariant Thresholds
MAX_PHOTON_BUDGET_JOULES = 1200.0
MIN_PURITY_PERCENT = 95.0
MIN_YIELD_PERCENT = 85.0
MAX_TEMPERATURE_RISE_C = 8.0
MAX_QUENCH_INJECTIONS = 2
MAX_BYPRODUCT_PERCENT = 2.5

# Metered diagnostic probes (public). Each probe costs PROBE_ENERGY_J from the SAME photon budget the
# productive run must fit inside, and at most PROBE_BUDGET probes may be run per session.
PROBE_BUDGET = 2
PROBE_ENERGY_J = 155.0
PROBE_NOISE = 0.02
REGIMES = ("photobleaching_fade", "thermal_oligomer_runaway", "catalyst_poisoning")
DRIFT_RANGE = (-0.15, 0.15)

# Observation model: readout = base + regimeOffset[regime] + driftGain * drift + noise, |noise| <= PROBE_NOISE.
PROBE_MENU: list[dict[str, Any]] = [
    {
        "id": 0,
        "name": "blue_450nm_short_pulse",
        "base": 1.00,
        "driftGain": 2.0,
        "regimeOffset": {
            "photobleaching_fade": 0.0,
            "thermal_oligomer_runaway": 0.0,
            "catalyst_poisoning": 0.0,
        },
    },
    {
        "id": 1,
        "name": "uva_365nm_long_pulse",
        "base": 0.0,
        "driftGain": 0.0,
        "regimeOffset": {
            "photobleaching_fade": 0.40,
            "thermal_oligomer_runaway": 0.70,
            "catalyst_poisoning": 0.70,
        },
    },
    {
        "id": 2,
        "name": "violet_420nm_mid_pulse",
        "base": 0.0,
        "driftGain": 1.0,
        "regimeOffset": {
            "photobleaching_fade": 0.55,
            "thermal_oligomer_runaway": 0.55,
            "catalyst_poisoning": 1.10,
        },
    },
    {
        "id": 3,
        "name": "blue_450nm_long_pulse",
        "base": 1.60,
        "driftGain": 0.30,
        "regimeOffset": {
            "photobleaching_fade": 0.0,
            "thermal_oligomer_runaway": 0.0,
            "catalyst_poisoning": 0.0,
        },
    },
]


def probe_expected(probe_id: int, regime: str, drift: float) -> float:
    """Noiseless expected readout of a diagnostic probe under a hypothesised (regime, drift)."""
    p = PROBE_MENU[probe_id]
    return p["base"] + p["regimeOffset"][regime] + p["driftGain"] * drift


def consistent_hypotheses(readouts: dict[int, float]) -> list[tuple[str, float]]:
    """All (regime, drift) hypotheses consistent with the observed readouts within PROBE_NOISE.

    For each regime the drift is estimated from the drift-sensitive probes; a hypothesis survives only
    if every observed probe matches its prediction within the noise bound. One surviving hypothesis
    means the hidden state is identified; several means the chosen probes cannot separate them."""
    out = []
    for reg in REGIMES:
        est = []
        for pid, r in readouts.items():
            g = PROBE_MENU[pid]["driftGain"]
            if g > 0:
                est.append(
                    (r - PROBE_MENU[pid]["base"] - PROBE_MENU[pid]["regimeOffset"][reg])
                    / g
                )
        d = sum(est) / len(est) if est else 0.0
        d = max(DRIFT_RANGE[0], min(DRIFT_RANGE[1], d))
        if all(
            abs(probe_expected(pid, reg, d) - r) <= PROBE_NOISE + 1e-9
            for pid, r in readouts.items()
        ):
            out.append((reg, d))
    return out


def gaussian_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def calculate_residence_time_sec(flow_rate_ul_min: float) -> float:
    """Hydraulic residence time in seconds: tau = V_channel / Q_flow."""
    return CHANNEL_VOLUME_UL / max(1e-6, flow_rate_ul_min / 60.0)


def calculate_optical_absorption(
    wavelength_band: str,
    peak_nm: float,
    molar_extinction: float,
    conc_catalyst_molar: float,
    path_length_cm: float = OPTICAL_PATH_LENGTH_CM,
) -> tuple[float, float, float]:
    """Extinction ratio, absorbance and fraction absorbed via a Gaussian spectral overlap model."""
    band_center = (
        450.0
        if wavelength_band == "blue_450nm"
        else (420.0 if wavelength_band == "violet_420nm" else 365.0)
    )
    extinction_ratio = math.exp(-((band_center - peak_nm) ** 2) / (2.0 * 10.0**2))
    eps_eff = molar_extinction * extinction_ratio
    absorbance = eps_eff * conc_catalyst_molar * path_length_cm
    return extinction_ratio, absorbance, 1.0 - math.pow(10.0, -absorbance)


def simulate_session(case: dict[str, Any], replies: dict[str, Any]) -> dict[str, Any]:
    """Practice scorer. `case["hidden"]` must hold {"regime", "drift"}; `replies` holds the six stage
    replies keyed "1","2","3a","3b","4","5","6" (3a = probe selection, 3b = trims after readouts)."""
    H = case["hidden"]
    s1, s2, s3a, s3b, s4, s5, s6 = (
        replies[k] for k in ("1", "2", "3a", "3b", "4", "5", "6")
    )
    flow0 = float(s1["flowRateUlMin"])
    led0 = float(s1["initialLedPowerPercent"])
    band = s2["ledWavelengthBand"]
    temp_c = float(s2["reactorTemperatureC"])
    sel = list(s3a.get("probeSelection", []))
    probe_energy = len(sel) * PROBE_ENERGY_J
    irr_trim = float(s3b.get("irradianceTrimPercent", 0))
    flow_adj = float(s3b.get("flowRateAdjustmentUlMin", 0))
    quenches = s4.get("quenchInjections", [])
    total_quench_flow = sum(float(q.get("flowRateUlMin", 0.0)) for q in quenches)
    window = s6.get("fractionCollectorWindowSec", [0, 1])
    reg = H["regime"]
    if reg == "photobleaching_fade":
        ok5 = 40.0 <= float(s5.get("pulsedDutyCyclePercent", 100.0)) <= 60.0
        eta_branch, dT5, conv_mod = (1.0 if ok5 else 0.60), 0.0, 1.0
    elif reg == "thermal_oligomer_runaway":
        ok5 = 12.0 <= float(s5.get("emergencyCoolingTempC", 99.0)) <= 20.0
        eta_branch, dT5, conv_mod = 1.0, (-2.5 if ok5 else 6.5), 1.0
    else:
        ok5 = 0.3 <= float(s5.get("catalystReloadMolPercent", 0.0)) <= 0.6
        eta_branch, dT5, conv_mod = 1.0, 0.0, (1.0 if ok5 else 0.55)
    effective_flow = max(10.0, flow0 + flow_adj)
    tau = calculate_residence_time_sec(effective_flow)
    conc_cat = (
        case["profile"]["feedConcentrations"]["catalystMolPercent"] / 100.0
    ) * case["profile"]["feedConcentrations"]["substrateA"]
    _, _, f_abs = calculate_optical_absorption(
        band,
        case["optics"]["catalystAbsorbancePeakNm"],
        case["optics"]["molarExtinctionCoefficient"],
        conc_cat,
    )
    p_eff = max(0.10, min(1.0, (led0 + irr_trim) / 100.0))
    drift = H["drift"]
    temp_k = temp_c + 273.15
    k_r = case["profile"]["preExponentialFactor"] * math.exp(
        -case["profile"]["activationEnergyJoulePerMol"] / (R_IDEAL * temp_k)
    )
    uncomp = drift + (irr_trim / 50.0)
    drive_mod = max(0.10, 1.0 + 3.8 * uncomp if uncomp < 0 else 1.0)
    photo_intensity = p_eff * f_abs * (1.0 + drift)
    conversion = (1.0 - math.exp(-(k_r * photo_intensity * tau * drive_mod))) * conv_mod
    rad_mod = max(0.5, 1.0 + 3.5 * uncomp if uncomp > 0 else 1.0)
    c_rad = max(0.0005, (photo_intensity * 0.080 * rad_mod) / (1.0 + k_r * 0.040))
    k_dim = case["profile"]["dimerizationPreExponentialFactor"] * math.exp(
        -case["profile"]["dimerizationActivationEnergyJoulePerMol"] / (R_IDEAL * temp_k)
    )
    in_reactor_dimer = (k_dim / max(1e-5, k_r)) * (c_rad**2) * 2000.0
    quench_ratio = total_quench_flow / max(
        1e-6, (effective_flow * c_rad) / case["quench"]["scavengerConcentrationMolar"]
    )
    post_quench_dimer_pct = max(0.0, 1.0 - quench_ratio) * 2.5
    scavenger_impurity_pct = max(0.0, quench_ratio - 1.20) * 5.2
    heat_gen = (
        abs(case["kinetics"]["reactionEnthalpyKJPerMol"])
        * conversion
        * case["profile"]["feedConcentrations"]["substrateA"]
        * 0.18
    )
    total_exotherm = max(
        0.0,
        case["kinetics"]["exothermDeltaT"]
        + heat_gen
        + (p_eff - 0.45) * 2.8
        - (effective_flow - 100.0) * 0.020
        + dT5,
    )
    total_oligomer = (
        case["assay"]["byproductOligomerPercent"]
        + in_reactor_dimer
        + max(0.0, (total_exotherm - 4.5) * 0.45)
        + post_quench_dimer_pct
    )
    total_energy = (
        case["harvest"]["accumulatedPhotonEnergyJoules"]
        + probe_energy
        + LED_MAX_OPTICAL_WATTS * p_eff * tau
    )
    pe = case["optics"]["pecletNumber"] * (effective_flow / 120.0)
    sigma_p = tau / math.sqrt(pe)
    t1, t2 = window
    f_p = max(
        0.0, gaussian_cdf((t2 - tau) / sigma_p) - gaussian_cdf((t1 - tau) / sigma_p)
    )
    f_front = max(
        0.0,
        gaussian_cdf((t2 - 0.60 * tau) / (0.8 * sigma_p))
        - gaussian_cdf((t1 - 0.60 * tau) / (0.8 * sigma_p)),
    )
    f_tail = max(
        0.0,
        gaussian_cdf((t2 - 1.55 * tau) / (1.2 * sigma_p))
        - gaussian_cdf((t1 - 1.55 * tau) / (1.2 * sigma_p)),
    )
    isolated_yield = (
        case["harvest"]["estimatedCrudeYieldPercent"]
        * min(1.0, conversion / 0.95)
        * eta_branch
        * f_p
    )
    total_imp = (
        total_oligomer
        + f_front * 5.0
        + f_tail * (total_oligomer * 2.5)
        + scavenger_impurity_pct
    )
    purity = (isolated_yield / max(1e-6, isolated_yield + total_imp)) * 100.0
    inv = {
        "purity_pass": purity >= MIN_PURITY_PERCENT,
        "yield_pass": isolated_yield >= MIN_YIELD_PERCENT,
        "energy_pass": total_energy <= MAX_PHOTON_BUDGET_JOULES,
        "exotherm_pass": total_exotherm <= MAX_TEMPERATURE_RISE_C,
        "quench_pass": len(quenches) == 2 and total_quench_flow >= 2.0,
        "oligomer_pass": total_oligomer <= MAX_BYPRODUCT_PERCENT,
        "probe_budget_pass": len(sel) <= PROBE_BUDGET,
        "regime_mitigated": ok5,
    }
    return {
        "passed": all(inv.values()),
        "isolatedYieldPercent": isolated_yield,
        "productPurityPercent": purity,
        "totalPhotonEnergyJoules": total_energy,
        "probeEnergyJoules": probe_energy,
        "channelExothermDeltaTC": total_exotherm,
        "oligomerByproductPercent": total_oligomer,
        "residenceTimeSec": tau,
        "invariants": inv,
    }
