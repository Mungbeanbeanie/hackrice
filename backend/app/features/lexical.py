import math
import re

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def tfidf_vectors(
    docs: list[str], reference: str
) -> tuple[list[list[float]], list[float]]:
    """Offline stand-in for the embedding model: TF-IDF over the candidate set.

    Used when the embeddings API is unavailable. The candidate set comes from a
    single shopping query, so it is already one topic — distinguishing within it
    is mostly lexical, which TF-IDF does without a network call.

    The vocabulary is fit on `docs` only, so reference terms no candidate uses
    are dropped. That is correct rather than lossy: a term shared by nothing
    carries no power to rank one candidate above another.
    """
    corpus = [_tokenize(d) for d in docs]
    vocab = {term: i for i, term in enumerate(sorted({t for d in corpus for t in d}))}
    n_docs = len(corpus)

    counts = [[0.0] * len(vocab) for _ in corpus]
    for row, tokens in zip(counts, corpus, strict=True):
        for term in tokens:
            row[vocab[term]] += 1.0

    # Smoothed, always-positive idf: a term in every document still scores >0,
    # so a document of only-common terms keeps a non-zero vector and a defined
    # cosine, instead of collapsing to the zero vector.
    doc_freq = [sum(1 for row in counts if row[i] > 0) for i in range(len(vocab))]
    idf = [math.log((1 + n_docs) / (1 + df)) + 1 for df in doc_freq]

    def _weighted(row: list[float]) -> list[float]:
        vec = [tf * w for tf, w in zip(row, idf, strict=True)]
        norm = math.sqrt(sum(v * v for v in vec))
        return [v / norm for v in vec] if norm else vec

    ref_counts = [0.0] * len(vocab)
    for term in _tokenize(reference):
        if term in vocab:
            ref_counts[vocab[term]] += 1.0

    return [_weighted(row) for row in counts], _weighted(ref_counts)
