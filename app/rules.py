import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_rules(path: Path) -> list[dict]:
    """Split brand-guide.md into rules. Each bullet (or paragraph) becomes one rule, e.g. id '3.2'."""
    rules, section, buf = [], None, []

    def flush():
        if buf and section:
            text = " ".join(s.strip() for s in buf).strip()
            text = re.sub(r"^- ", "", text)
            n = sum(1 for r in rules if r["section"] == section) + 1
            rules.append({"id": f"{section}.{n}", "section": section, "text": text})
        buf.clear()

    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^## (\d+)\.", line)
        if m:
            flush()
            section = m.group(1)
            continue
        if not line.strip():
            flush()
            continue
        if line.startswith("- "):
            flush()
        buf.append(line)
    flush()
    return rules


class Retriever:
    """TF-IDF search over brand rules. Swap for embeddings later if you want."""

    def __init__(self, rules: list[dict]):
        self.rules = rules
        self.vec = TfidfVectorizer(stop_words="english")
        self.matrix = self.vec.fit_transform([r["text"] for r in rules])

    def search(self, query: str, k: int = 4) -> list[dict]:
        sims = cosine_similarity(self.vec.transform([query]), self.matrix)[0]
        order = sims.argsort()[::-1][:k]
        return [dict(self.rules[i], score=round(float(sims[i]), 3)) for i in order if sims[i] > 0]
