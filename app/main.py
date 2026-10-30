import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .llm import generate_json
from .refusal import banned_hits
from .rules import Retriever, load_rules
from .validate import validate_caption

load_dotenv()
DATA = Path(os.environ.get("DATA_DIR", "data"))
PRODUCTS = {p["id"]: p for p in json.loads((DATA / "products.json").read_text(encoding="utf-8"))}
RULES = load_rules(DATA / "brand-guide.md")
RETRIEVER = Retriever(RULES)
CORE_SECTIONS = {"1", "2", "4"}  # voice, caption rules, hashtags: always sent to the LLM
LANGUAGES = {"en": "English", "de": "German (informal 'du')", "es": "neutral Spanish (Spain and Mexico)"}

SYSTEM_PROMPT = (
    "You write Instagram captions for Lumo Living. Follow the brand rules exactly. "
    'Reply only with JSON: {"caption": string, "hashtags": [string], "rules_used": [rule ids you followed]}.'
)

app = FastAPI(title="Lumo Living Post Writer")


class PostRequest(BaseModel):
    product_id: str
    languages: list[str] = ["en"]
    request: str = ""  # optional extra instruction from the user


class CheckRequest(BaseModel):
    product_id: str
    caption: str
    hashtags: list[str] = []
    language: str = "en"


def get_product(product_id: str) -> dict:
    if product_id not in PRODUCTS:
        raise HTTPException(404, f"Unknown product_id {product_id}")
    return PRODUCTS[product_id]


def write_post(product: dict, lang: str, rules_text: str, extra: str, rule_ids: list[str], attempts: int = 2) -> dict:
    user = (
        f"Product: {json.dumps(product, ensure_ascii=False)}\n"
        f"Brand rules:\n{rules_text}\n"
        f"Language: {LANGUAGES[lang]}\n"
        f"Extra request: {extra or 'none'}\n"
        "Return the JSON."
    )
    feedback, data, issues = "", {}, []
    for _ in range(attempts):
        data = generate_json(SYSTEM_PROMPT, user + feedback)
        issues = validate_caption(data.get("caption", ""), data.get("hashtags", []), product, lang)
        if not issues:
            return {
                "language": lang,
                "caption": data["caption"],
                "hashtags": data["hashtags"],
                "rules_used": data.get("rules_used") or rule_ids,
                "checks": "passed",
            }
        feedback = f"\nYour previous answer broke these rules: {'; '.join(issues)}. Fix them and reply with JSON again."
    return {
        "language": lang,
        "caption": data.get("caption"),
        "hashtags": data.get("hashtags"),
        "rules_used": rule_ids,
        "checks": "failed",
        "issues": issues,
    }


@app.post("/posts")
def create_post(req: PostRequest):
    product = get_product(req.product_id)
    bad = [lang for lang in req.languages if lang not in LANGUAGES]
    if bad:
        raise HTTPException(400, f"Unsupported languages: {bad}")

    hits = banned_hits(req.request, product)
    if hits:
        return {
            "refused": True,
            "reason": "This request asks for claims the brand never makes.",
            "rules": hits,
            "posts": [],
        }

    query = f"{product['name']} {' '.join(product['features'])} {req.request}"
    selected = {r["id"]: r for r in RULES if r["section"] in CORE_SECTIONS}
    for r in RETRIEVER.search(query, k=4):
        selected[r["id"]] = r
    rules_text = "\n".join(f"[{rid}] {r['text']}" for rid, r in selected.items())

    posts = [write_post(product, lang, rules_text, req.request, sorted(selected)) for lang in req.languages]
    return {"refused": False, "product_id": product["id"], "posts": posts}


@app.post("/check")
def check(req: CheckRequest):
    product = get_product(req.product_id)
    issues = validate_caption(req.caption, req.hashtags, product, req.language)
    return {"passed": not issues, "issues": issues}


@app.get("/health")
def health():
    return {"status": "ok", "products": len(PRODUCTS), "rules": len(RULES)}
