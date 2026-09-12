from urllib.parse import urlparse


def url_to_text(url: str) -> str:
    path = urlparse(url).path
    segments = [segment for segment in path.split("/") if segment]
    slug = segments[-1] if segments else ""

    if "." in slug:
        slug = slug.rsplit(".", 1)[0]

    parts = slug.split("-")
    if parts and parts[-1].isdigit():
        parts = parts[:-1]

    return " ".join(parts).replace("_", " ").strip()
