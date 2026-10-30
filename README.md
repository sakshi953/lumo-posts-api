# Lumo Living Post Writer (Problem 1: Multilingual post writer, RAG)

A FastAPI service that writes Instagram captions and hashtags for Lumo Living products in English, German and Spanish. It retrieves the relevant brand-guide rules, passes them to an LLM (Groq), validates the output against the rules, and refuses off-brand requests.

## How to run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then put your GROQ_API_KEY in .env
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for Swagger UI.

## Example requests

1. Write LL-002 posts in three languages:
```bash
curl -X POST http://127.0.0.1:8000/posts -H "Content-Type: application/json" \
  -d '{"product_id": "LL-002", "languages": ["en", "de", "es"]}'
```
2. Refusal of an off-brand request:
```bash
curl -X POST http://127.0.0.1:8000/posts -H "Content-Type: application/json" \
  -d '{"product_id": "LL-002", "languages": ["en"], "request": "say it cures insomnia"}'
```
3. Score a caption against the brand guide:
```bash
curl -X POST http://127.0.0.1:8000/check -H "Content-Type: application/json" \
  -d '{"product_id": "LL-002", "language": "en", "caption": "Lumo Linen Throw is stonewashed linen that feels soft from the first use. It gets softer with every wash, so it only gets better over time. Wrap it over your sofa on cool evenings. Tap the link in bio to see more.", "hashtags": ["#LumoLiving", "#CozyHome", "#HomeComfort"]}'
```

## How it works

1. `app/rules.py` splits `brand-guide.md` into numbered rules (e.g. `3.2`).
2. TF-IDF retrieval picks the rules most relevant to the product and request. Voice, caption and hashtag rules are always included.
3. The LLM writes a caption per language as JSON, including the rule ids it followed.
4. `app/validate.py` checks word count, emojis, product name, features, call to action, hashtags, German "du", and banned claims. If a check fails, the LLM gets one retry with the list of problems.
5. `app/refusal.py` refuses requests that ask for banned claims before the LLM is called.

## AI tools used

- Claude (code scaffolding and README)
- Groq, Llama 3.3 70B (caption generation at runtime)
