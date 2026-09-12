from app.ingestion.target_resolver import pick_target
from app.models import Product

# The real link from the bug report, scheme-less exactly as it was pasted.
AMAZON_URL = (
    "amazon.com/Retrospec-Dakota-Bicycle-Skateboard-Helmet/dp/B094PPPR3R/"
    "ref=sr_1_6?crid=UNUBOM35S1DI&dib_tag=se&keywords=scooter%2Bhelmet"
)
SLUG_TEXT = "Retrospec Dakota Bicycle Skateboard Helmet"


def _product(id: str, title: str, vendor: str) -> Product:
    return Product(
        id=id,
        title=title,
        description=None,
        brand=None,
        price=10.0,
        original_price=None,
        rating=4.0,
        review_count=10,
        vendor=vendor,
        vendor_logo=None,
        image_url=None,
        product_url="u",
        specs=[],
    )


def test_title_overlap_beats_googles_merchant_ranking() -> None:
    # The reported bug: slot 0 was a Dick's helmet, and nothing checked it
    # against the product the user had actually named.
    results = [
        _product("a", "Bell Sports Adult Bike Helmet", "Dick's Sporting Goods"),
        _product("b", "Giro Fixture MIPS Helmet", "Backcountry"),
        _product("c", "Retrospec Dakota Bicycle Skateboard Helmet", "Walmart"),
    ]
    assert pick_target(results, AMAZON_URL, SLUG_TEXT).id == "c"


def test_pasted_retailer_wins_over_a_better_title_match() -> None:
    # The user pointed at one listing. If that retailer is in the result set at
    # all, it is the listing they meant, even if another title reads closer.
    results = [
        _product("a", "Retrospec Dakota Bicycle Skateboard Helmet", "Walmart"),
        _product("b", "Retrospec Dakota Helmet", "Amazon.com"),
    ]
    assert pick_target(results, AMAZON_URL, SLUG_TEXT).id == "b"


def test_vendor_match_ignores_punctuation_and_spacing() -> None:
    results = [
        _product("a", "Some Other Helmet", "Walmart"),
        _product("b", "Some Other Helmet", "Dick's Sporting Goods"),
    ]
    picked = pick_target(results, "dickssportinggoods.com/p/helmet-123", "helmet")
    assert picked.id == "b"


def test_no_signal_at_all_degrades_to_the_first_result() -> None:
    # Old behaviour is the floor, not a regression: with nothing to go on the
    # upstream ranking is still the best available guess.
    results = [
        _product("a", "Totally Unrelated Thing", "Walmart"),
        _product("b", "Another Unrelated Thing", "Target"),
    ]
    assert pick_target(results, "ergonomic pillow", "ergonomic pillow").id == "a"


def test_exact_product_mode_has_no_url_to_read() -> None:
    # No host label, so the overlap pass is the only pass.
    results = [
        _product("a", "Generic Running Shoe", "Zappos"),
        _product("b", "Nike Pegasus 40 Running Shoe", "Nike"),
    ]
    assert pick_target(results, "Nike Pegasus 40", "Nike Pegasus 40").id == "b"
