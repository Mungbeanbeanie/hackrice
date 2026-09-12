import pytest

from app.coupons.selector import _normalize_store, store_slug


@pytest.mark.parametrize(
    ("display_name", "expected"),
    [
        # SerpAPI merchant names, as Product.vendor actually carries them.
        ("Dick's Sporting Goods", "dickssportinggoods"),
        ("Best Buy", "bestbuy"),
        ("Amazon.com", "amazoncom"),
        ("1800 Pet Meds", "1800petmeds"),
        ("Bed Bath & Beyond", "bedbathbeyond"),
        # Already-domain input has to survive the same trip.
        ("https://www.walmart.com/", "walmartcom"),
    ],
)
def test_display_names_reduce_to_a_domain_label(
    display_name: str, expected: str
) -> None:
    assert store_slug(display_name) == expected


def test_normalize_store_still_yields_a_bare_domain() -> None:
    # The exact-domain half of the lookup must keep working — store_slug is an
    # additional match, not a replacement.
    assert _normalize_store("https://www.1800petmeds.com/") == "1800petmeds.com"


def test_slug_of_an_empty_name_is_empty() -> None:
    # A blank vendor must not produce a slug that matches every row.
    assert store_slug("   ") == ""
