import re
from urllib.parse import unquote, urlparse

from app.models import Product


def _words(segment: str) -> list[str]:
    stem = unquote(segment).rsplit(".", 1)[0]
    return [part for part in re.split(r"[-_+]", stem) if part.isalpha()]


def url_to_text(url: str) -> str:
    # Retail URLs bury the product slug mid-path and hang tracking junk off the
    # end (/Product-Name-Here/dp/ASIN/ref=sr_1_6), so the last segment is a ref
    # tag, not the product. Pick the segment with the most word-like parts.
    #
    # Prefixing "//" when the scheme is missing keeps the domain in netloc and
    # out of the path, so a pasted "amazon.com/..." can't win the contest with
    # its own hostname.
    path = urlparse(url if "//" in url else f"//{url}").path
    segments = [segment for segment in path.split("/") if segment]
    best = max(segments, key=lambda segment: len(_words(segment)), default="")
    return " ".join(_words(best))


def _host_label(raw_query: str) -> str:
    """The retailer label of a pasted URL ("amazon"), or "" for non-URL input.

    Same scheme-less handling as url_to_text: the netloc it already computes and
    throws away is the only record of which retailer the user actually meant.
    """
    netloc = urlparse(raw_query if "//" in raw_query else f"//{raw_query}").netloc
    host = netloc.lower().removeprefix("www.").split(":")[0]
    return host.split(".")[0] if "." in host else ""


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _overlap(search_text: str, title: str) -> float:
    wanted = {w for w in _squash_words(search_text) if w}
    if not wanted:
        return 0.0
    have = set(_squash_words(title))
    return len(wanted & have) / len(wanted)


def _squash_words(text: str) -> list[str]:
    return [_squash(word) for word in text.split()]


def pick_target(results: list[Product], raw_query: str, search_text: str) -> Product:
    """The result the user actually named, not whichever merchant Google ranked first.

    SerpAPI returns Google Shopping's own merchant ordering, so slot 0 is a
    popularity answer to the query — pasting an Amazon helmet link would hand
    back a different retailer's different helmet, and that wrong product then
    became the baseline price, the spec-verdict reference and the similarity
    reference for every candidate.

    Two passes: the pasted URL's retailer if it is in the result set at all,
    then the title with the most words in common with the query. A total tie
    falls through to results[0], which is the old behaviour.

    ponytail: token overlap, not a real product-page scrape. Amazon barely feeds
    Google Shopping so the vendor pass usually misses and the overlap pass
    carries this; fetching the pasted page's title is the upgrade path.
    """
    label = _host_label(raw_query)
    if label:
        for product in results:
            vendor = _squash(product.vendor)
            if vendor and (label in vendor or vendor in label):
                return product

    return max(results, key=lambda p: _overlap(search_text, p.title))
