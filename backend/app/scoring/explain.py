from typing import Literal

from app.models import ComparisonResult, Group

Verdict = Literal["same", "better", "close", "different", "lower"]

# Only measure_* specs carry a direction, and only these units have one that
# holds across every category we index. gb/tb/mah: more is better. lb/kg: less
# is better, since the only weights a listing publishes are shipping weights.
# Everything else is deliberately neutral — a bigger pillow is not a better
# pillow, so guessing a direction there would label noise as an improvement.
_HIGHER_BETTER = {"gb", "tb", "mah"}
_LOWER_BETTER = {"lb", "kg"}

# Within this band the difference is rounding or a spec sheet's own tolerance,
# not a real distinction worth a better/lower call.
_CLOSE_BAND = (0.95, 1.05)

# {baseline} is "the original" for a resolved target, "the median price" when
# the reference is the synthetic median of the candidate set (description mode),
# where calling it "the original" would name a product that does not exist.
_OPENING: dict[Group, str] = {
    Group.SAME_SPEC: (
        "Same materials and construction as {baseline}, without the logo."
    ),
    Group.SAME_JOB: "A different build that does the same job.",
    Group.CLEARS_FLOOR: "The cheapest option here that still clears the quality floor.",
}

_MATCHING_VERDICTS = {"same", "close", "better"}


def _as_float(value: float | str) -> float | None:
    # Extracted specs are already float | str, but a string spec that happens to
    # parse ("18") must compare numerically against a float target rather than
    # falling into the text branch and reading as "different".
    if isinstance(value, int | float):
        return float(value)
    try:
        return float(value.strip())
    except ValueError:
        return None


def verdict(
    name: str, target_value: float | str | None, value: float | str
) -> Verdict | None:
    """How this candidate's spec compares to the target's.

    None when the target has no such spec — there is nothing to compare against,
    which is also every spec in description mode, where no target is resolved.
    """
    if target_value is None:
        return None

    target_num = _as_float(target_value)
    num = _as_float(value)
    if target_num is None or num is None:
        return (
            "same"
            if str(target_value).casefold() == str(value).casefold()
            else "different"
        )

    if target_num == num:
        return "same"
    # A zero target makes the ratio undefined, so the band cannot be applied and
    # the sign table below is the only thing left to judge on.
    if target_num != 0:
        ratio = num / target_num
        if _CLOSE_BAND[0] <= ratio <= _CLOSE_BAND[1]:
            return "close"

    unit = name.removeprefix("measure_")
    if unit in _HIGHER_BETTER:
        return "better" if num > target_num else "lower"
    if unit in _LOWER_BETTER:
        return "better" if num < target_num else "lower"
    return "different"


def rationale(
    result: ComparisonResult,
    verdicts: list[Verdict | None],
    baseline_label: str = "the original",
) -> str:
    """One or two plain sentences explaining why this candidate is here.

    Reads nothing the UI is no longer allowed to show: no Bayesian Q, no value
    score V, no cosine (overview.md §3.4). Every figure here is one the result
    card already displays on its own.
    """
    parts = [_OPENING[result.group].format(baseline=baseline_label)]

    comparable = [v for v in verdicts if v is not None]
    if comparable:
        matching = sum(1 for v in comparable if v in _MATCHING_VERDICTS)
        parts.append(f"Matches on {matching} of {len(comparable)} listed specs.")

    if result.savings_amount is not None and result.savings_percent is not None:
        parts.append(
            f"Saves ${result.savings_amount:,.2f} "
            f"({result.savings_percent:.0f}%) versus {baseline_label}."
        )

    candidate = result.candidate
    if candidate.review_count > 0:
        parts.append(
            f"Rated {candidate.rating:.1f} across {candidate.review_count:,} reviews."
        )
    else:
        parts.append("No reviews yet.")

    return " ".join(parts)
