import re

from .refusal import banned_hits

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
CTA_WORDS = ["link", "bio", "tap", "tippe", "toca", "tocca", "descubre", "entdecke", "discover", "shop", "mehr"]


def validate_caption(caption: str, hashtags: list[str], product: dict, lang: str) -> list[str]:
    """Return a list of rule violations. Empty list means the caption passes."""
    issues = []
    words = len(caption.split())
    if not 40 <= words <= 90:
        issues.append(f"caption has {words} words, must be 40-90")
    emojis = EMOJI.findall(caption)
    if len(emojis) > 2:
        issues.append("more than 2 emojis")
    if caption[:1] and EMOJI.match(caption[:1]):
        issues.append("caption starts with an emoji")
    if product["name"] not in caption:
        issues.append(f"product name must appear exactly as '{product['name']}'")
    mentioned = [f for f in product["features"] if f.lower() in caption.lower()]
    if len(mentioned) > 2:
        issues.append("mentions more than 2 product features")
    if not any(w in caption.lower() for w in CTA_WORDS):
        issues.append("missing a call to action")
    if not 3 <= len(hashtags) <= 5:
        issues.append("needs 3-5 hashtags")
    if "#LumoLiving" not in hashtags:
        issues.append("#LumoLiving hashtag is missing")
    if any(len(h) > 20 for h in hashtags):
        issues.append("a hashtag is longer than 20 characters")
    if lang == "de" and re.search(r"\bSie\b", caption):
        issues.append("use informal 'du' in German, not 'Sie'")
    for hit in banned_hits(caption, product):
        issues.append(f"breaks rule {hit}")
    return issues
