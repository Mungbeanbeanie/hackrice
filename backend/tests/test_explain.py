import pytest

from app.models import ComparisonResult, Group, Product
from app.scoring import explain


def _product(rating: float = 4.4, review_count: int = 1200) -> Product:
    return Product(
        id="p1",
        title="Unbranded Contour Memory Foam Pillow",
        description=None,
        brand="b",
        price=42.0,
        original_price=None,
        rating=rating,
        review_count=review_count,
        vendor="v",
        vendor_logo=None,
        image_url=None,
        product_url="u",
        specs=[],
    )


def _result(
    group: Group = Group.SAME_SPEC,
    savings_amount: float | None = 78.0,
    savings_percent: float | None = 65.0,
    product: Product | None = None,
) -> ComparisonResult:
    return ComparisonResult(
        candidate=product or _product(),
        similarity=0.96,
        # Distinctive figures: the leak assertion below looks for these exact
        # strings, so they must not collide with any rating or savings number.
        quality_score=4.873,
        value_score=0.11142,
        group=group,
        savings_amount=savings_amount,
        savings_percent=savings_percent,
    )


# --- verdict ---


def test_verdict_is_none_when_target_lacks_the_spec() -> None:
    # The whole description-mode case: no target resolved, so nothing to
    # compare any candidate spec against.
    assert explain.verdict("material", None, "latex") is None


def test_same_for_case_insensitive_string_match() -> None:
    assert explain.verdict("material", "memory foam", "Memory Foam") == "same"


def test_same_for_equal_numbers() -> None:
    assert explain.verdict("measure_in", 18.0, 18.0) == "same"


def test_numeric_string_compares_as_a_number_not_as_text() -> None:
    # "18" and 18.0 are the same spec; falling into the text branch would only
    # ever report them equal by accident of formatting.
    assert explain.verdict("measure_in", "18", 18.0) == "same"


def test_close_when_within_the_tolerance_band() -> None:
    assert explain.verdict("measure_in", 18.0, 18.5) == "close"


def test_better_when_more_of_a_higher_is_better_unit() -> None:
    assert explain.verdict("measure_gb", 128.0, 256.0) == "better"


def test_lower_when_less_of_a_higher_is_better_unit() -> None:
    assert explain.verdict("measure_gb", 256.0, 128.0) == "lower"


def test_better_when_less_of_a_lower_is_better_unit() -> None:
    # Weight is the inverted one: a lighter listing is the better listing.
    assert explain.verdict("measure_lb", 5.0, 2.0) == "better"


def test_lower_when_more_of_a_lower_is_better_unit() -> None:
    assert explain.verdict("measure_lb", 2.0, 5.0) == "lower"


def test_different_for_mismatched_strings() -> None:
    assert explain.verdict("size", "queen", "king") == "different"


def test_neutral_unit_never_claims_better_or_lower() -> None:
    # A bigger pillow is not a better pillow. Inches carry no direction, so a
    # real gap has to read as "different", not as an improvement.
    assert explain.verdict("measure_in", 18.0, 30.0) == "different"


@pytest.mark.parametrize("name", ["measure_in", "measure_gb"])
def test_zero_target_does_not_divide_by_zero(name: str) -> None:
    # The ratio is undefined here, so the band cannot be applied — the call must
    # still return a verdict rather than raising.
    assert explain.verdict(name, 0.0, 5.0) in {"better", "different"}


def test_every_verdict_value_is_reachable() -> None:
    # The union is 5 values and all 5 must be producible from the spec
    # vocabulary serpapi_client actually emits — an unreachable value is a
    # chip style in SpecBreakdownModal that can never render.
    produced = {
        explain.verdict("material", "memory foam", "memory foam"),
        explain.verdict("measure_gb", 128.0, 256.0),
        explain.verdict("measure_in", 18.0, 18.5),
        explain.verdict("size", "queen", "king"),
        explain.verdict("measure_gb", 256.0, 128.0),
    }
    assert produced == {"same", "better", "close", "different", "lower"}


# --- rationale ---


def test_rationale_includes_savings_when_present() -> None:
    text = explain.rationale(_result(), ["same", "close"])
    assert "$78.00" in text
    assert "65%" in text


def test_rationale_omits_savings_when_absent() -> None:
    text = explain.rationale(
        _result(savings_amount=None, savings_percent=None), ["same"]
    )
    assert "Saves" not in text
    assert "$" not in text


def test_rationale_counts_only_comparable_specs() -> None:
    text = explain.rationale(_result(), ["same", "different", None, "better"])
    # Three comparable, two of them matching — the None is not a spec that
    # failed to match, it is a spec with nothing to match against.
    assert "2 of 3" in text


def test_rationale_omits_spec_count_when_nothing_is_comparable() -> None:
    text = explain.rationale(_result(), [None, None])
    assert "specs" not in text


def test_rationale_opening_differs_per_group() -> None:
    openings = {explain.rationale(_result(group=g), []).split(".")[0] for g in Group}
    assert len(openings) == len(Group)


def test_rationale_handles_a_product_with_no_reviews() -> None:
    text = explain.rationale(_result(product=_product(rating=0.0, review_count=0)), [])
    assert "No reviews yet." in text


def test_rationale_never_leaks_the_scoring_math() -> None:
    # overview.md §3.4: Q, V and cosine still drive ordering but must not reach
    # the UI, and rationale is the one free-text field that could carry them.
    text = explain.rationale(_result(), ["same", "better"])
    for leaked in ("4.873", "0.11142", "0.96"):
        assert leaked not in text
