import re

# Rules from section 3 of brand-guide.md ("Claims we never make")
BANNED = [
    (r"\b(cures?|cured|heals?|healed|treats?|treated|prevents?|prevented)\b", "3 (No medical or health claims)"),
    (r"\b(insomnia|anxiety|back pain|depression|sleep disorder)\b", "3 (No medical or health claims)"),
    (r"\b(best|perfect|guarantee[d]?|100%)\b", "3 (No absolute claims)"),
    (r"\b(limited time|discounts?|% off|sale|prices?|cheaper)\b", "3 (No prices, discounts or limited-time offers)"),
    (r"\b(competitors?|ikea|amazon)\b", "3 (Never mention competitors)"),
]
SUSTAINABILITY = (
    r"\b(sustainabl[ey]|eco[- ]friendly|eco|vegan|organic|plastic[- ]free)\b",
    "3 (No sustainability claims unless the product's sustainability field says so)",
)


def banned_hits(text: str, product: dict | None = None) -> list[str]:
    rules = list(BANNED)
    if not (product and product.get("sustainability")):
        rules.append(SUSTAINABILITY)
    return list(dict.fromkeys(rule for pattern, rule in rules if re.search(pattern, text, re.I)))
