#!/usr/bin/env python3
"""Exact rank enumeration for the small catalyst decision frontiers.

Spearman rho and Kendall tau are treated here as descriptive summaries of rank
rearrangement. The complete permutation space is enumerated for the n=3 NH3
frontier and n=4 MeOH frontier so that small-n discreteness is explicit.

The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from itertools import permutations
from math import factorial


CASES = {
    "NH3_top3": {
        "labels": ["Ru", "Os", "Fe"],
        "upstream_order": ["Ru", "Os", "Fe"],
        "downstream_order": ["Fe", "Ru", "Os"],
        "expected_rho": Fraction(-1, 2),
        "expected_tau": Fraction(-1, 3),
        "expected_inversions": 2,
    },
    "MeOH_2pct_STY_per_g_Re": {
        "labels": [
            "1 wt% Re / 250 C",
            "1 wt% Re / 200 C",
            "5 wt% Re / 200 C",
            "5 wt% Re / 250 C",
        ],
        "upstream_order": [
            "1 wt% Re / 250 C",
            "1 wt% Re / 200 C",
            "5 wt% Re / 200 C",
            "5 wt% Re / 250 C",
        ],
        "downstream_order": [
            "5 wt% Re / 200 C",
            "1 wt% Re / 200 C",
            "1 wt% Re / 250 C",
            "5 wt% Re / 250 C",
        ],
        "expected_rho": Fraction(1, 5),
        "expected_tau": Fraction(0, 1),
        "expected_inversions": 3,
    },
}


def ranks_for_order(labels: list[str], order: list[str]) -> tuple[int, ...]:
    rank = {label: idx + 1 for idx, label in enumerate(order)}
    return tuple(rank[label] for label in labels)


def spearman_rho(reference_ranks: tuple[int, ...], other_ranks: tuple[int, ...]) -> Fraction:
    n = len(reference_ranks)
    if n != len(other_ranks):
        raise ValueError("Rank vectors must have the same length")
    d2 = sum((a - b) ** 2 for a, b in zip(reference_ranks, other_ranks))
    return Fraction(1, 1) - Fraction(6 * d2, n * (n * n - 1))


def kendall_tau(reference_ranks: tuple[int, ...], other_ranks: tuple[int, ...]) -> Fraction:
    n = len(reference_ranks)
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            sign_ref = reference_ranks[i] - reference_ranks[j]
            sign_other = other_ranks[i] - other_ranks[j]
            if sign_ref * sign_other > 0:
                concordant += 1
            elif sign_ref * sign_other < 0:
                discordant += 1
            else:
                raise ValueError("Ties are not supported in these frozen rank cases")
    pairs = n * (n - 1) // 2
    return Fraction(concordant - discordant, pairs)


def pairwise_inversions(
    labels: list[str], reference_ranks: tuple[int, ...], other_ranks: tuple[int, ...]
) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            if (reference_ranks[i] - reference_ranks[j]) * (other_ranks[i] - other_ranks[j]) < 0:
                out.append((labels[i], labels[j]))
    return out


def exact_enumeration(reference_ranks: tuple[int, ...], observed_ranks: tuple[int, ...]) -> dict[str, object]:
    n = len(reference_ranks)
    observed_rho = spearman_rho(reference_ranks, observed_ranks)
    observed_tau = kendall_tau(reference_ranks, observed_ranks)
    perm_rhos: list[Fraction] = []
    perm_taus: list[Fraction] = []

    for perm in permutations(range(1, n + 1)):
        perm_rhos.append(spearman_rho(reference_ranks, perm))
        perm_taus.append(kendall_tau(reference_ranks, perm))

    total = factorial(n)
    rho_two_sided = Fraction(sum(abs(v) >= abs(observed_rho) for v in perm_rhos), total)
    tau_two_sided = Fraction(sum(abs(v) >= abs(observed_tau) for v in perm_taus), total)
    rho_lower = Fraction(sum(v <= observed_rho for v in perm_rhos), total)
    tau_lower = Fraction(sum(v <= observed_tau for v in perm_taus), total)

    return {
        "total": total,
        "rho": observed_rho,
        "tau": observed_tau,
        "rho_two_sided": rho_two_sided,
        "tau_two_sided": tau_two_sided,
        "rho_lower": rho_lower,
        "tau_lower": tau_lower,
        "rho_distribution": Counter(perm_rhos),
        "tau_distribution": Counter(perm_taus),
    }


def fmt_fraction(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator} ({float(value):.4f})"


def case_report(name: str, case: dict[str, object]) -> str:
    labels = list(case["labels"])
    upstream = list(case["upstream_order"])
    downstream = list(case["downstream_order"])
    ref = ranks_for_order(labels, upstream)
    obs = ranks_for_order(labels, downstream)
    exact = exact_enumeration(ref, obs)
    inversions = pairwise_inversions(labels, ref, obs)

    lines = [
        f"## {name}",
        "",
        f"- n = {len(labels)}; complete permutation space = {exact['total']}",
        f"- upstream order: {' > '.join(upstream)}",
        f"- downstream order: {' > '.join(downstream)}",
        f"- Spearman rho = {float(exact['rho']):.2f}",
        f"- Kendall tau = {float(exact['tau']):.2f}",
        f"- pairwise inversions = {len(inversions)}/{len(labels) * (len(labels) - 1) // 2}",
        f"- inverted pairs: {', '.join(f'{a} vs {b}' for a, b in inversions)}",
        f"- exact two-sided Spearman permutation probability = {fmt_fraction(exact['rho_two_sided'])}",
        f"- exact two-sided Kendall permutation probability = {fmt_fraction(exact['tau_two_sided'])}",
        "",
        "These exact probabilities are reported only to show the discreteness of the small-n rank space; they are not used as evidence for a population-level significance claim.",
        "",
    ]
    return "\n".join(lines)


def run_checks() -> None:
    for name, case in CASES.items():
        labels = list(case["labels"])
        ref = ranks_for_order(labels, list(case["upstream_order"]))
        obs = ranks_for_order(labels, list(case["downstream_order"]))
        rho = spearman_rho(ref, obs)
        tau = kendall_tau(ref, obs)
        inversions = pairwise_inversions(labels, ref, obs)
        assert rho == case["expected_rho"], (name, rho, case["expected_rho"])
        assert tau == case["expected_tau"], (name, tau, case["expected_tau"])
        assert len(inversions) == case["expected_inversions"], (
            name,
            len(inversions),
            case["expected_inversions"],
        )

    nh3 = CASES["NH3_top3"]
    labels = list(nh3["labels"])
    ref = ranks_for_order(labels, list(nh3["upstream_order"]))
    obs = ranks_for_order(labels, list(nh3["downstream_order"]))
    exact = exact_enumeration(ref, obs)
    assert exact["rho_two_sided"] == Fraction(1, 1)
    assert exact["tau_two_sided"] == Fraction(1, 1)

    meoh = CASES["MeOH_2pct_STY_per_g_Re"]
    labels = list(meoh["labels"])
    ref = ranks_for_order(labels, list(meoh["upstream_order"]))
    obs = ranks_for_order(labels, list(meoh["downstream_order"]))
    exact = exact_enumeration(ref, obs)
    assert exact["rho_two_sided"] == Fraction(11, 12)
    assert exact["tau_two_sided"] == Fraction(1, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="assert the frozen canonical values")
    args = parser.parse_args()

    if args.check:
        run_checks()
        print("PASS: exact rank-enumeration checks match the frozen NH3 and MeOH frontier values.")
    else:
        print("# Exact decision-frontier rank enumeration\n")
        for case_name, case in CASES.items():
            print(case_report(case_name, case))
