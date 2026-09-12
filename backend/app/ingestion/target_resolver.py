import re
from urllib.parse import unquote, urlparse


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
