# Personal Recommender Agent - Specifikacija

## Ideja i Tip Agenta
- **Problem:** Personalizirana preporuka sadržaja (filmovi, lekcije) koja se brzo prilagođava korisnikovom kontekstu i feedbacku, s fokusom na session-aware ponašanje i online adaptaciju.
- **Zašto agent, ne app:** Iterativno ponašanje — agent kontinuirano opaža interakcije, donosi odluke, i uči iz ishoda kroz vrijeme, ne samo jednom.
- **Tip agenta:** Recommender + Learning agent (session-aware + online update). Optimizira engagement (CTR, NDCG) i prilagođava se korisnikovom ponašanju.
- **Unikatnost:** Kombinacija session-based embeddings, online learning, i exploration policy (MAB) za balans između eksploatacije i istraživanja.
- **Primjenjivost:** Koristi se u streaming platformama, e-learning sustavima, ili news aggregatorima za povećanje engagementa i retentiona.

## Sense → Think → Act → Learn Ciklus (Detaljno)

### Sense (Opažanje)
- **Šta agent opaža:** 
  - Session events: clicks, impressions, dwell time, ratings (explicit/implicit).
  - Item metadata: genre, tags, popularity, embeddings.
  - User profile: long-term preferences, history.
  - Context: time of day, device type, session length.
- **Format i frekvencija:** JSON event stream (HTTP POST /events); event-driven tick (na svaki event) + nightly batch za retrain.
- **Primjeri ulaza:** 
  ```json
  {
    "user_id": "123",
    "session_id": "sess_456",
    "event_type": "click",
    "item_id": "movie_789",
    "timestamp": "2026-01-02T10:00:00Z",
    "context": {"device": "mobile", "time_of_day": "morning"}
  }
  ```

### Think (Zaključivanje)
- **Kako zaključuje:** 
  - Session encoder: RNN ili transformer za short-term context.
  - Long-term model: Matrix factorization ili embedding-based CF.
  - Hybrid scorer: Kombinacija collaborative + content-based (cosine similarity na embeddings).
  - Exploration: Epsilon-greedy ili multi-armed bandit za diversity.
  - Rules: Business constraints (no repeat items, age-appropriate, diversity score >0.5).
- **Output:** Ranked list of 10 items + confidence scores + explanation (optional).
- **Metrike za evaluaciju:** NDCG@10, Hit Rate@10, CTR.

### Act (Akcija)
- **Šta agent radi:** 
  - Return ranked recommendations via API.
  - Log events za learning.
  - Optional: Push notification ili A/B variant.
- **Safety:** Fallback na popular items ako confidence < threshold.
- **Primjeri akcija:** 
  - API response: `{"recommendations": [{"item_id": "movie_789", "score": 0.95, "reason": "Similar to clicked item"}]}`
  - Side-effect: Insert into DB za retrain.

### Learn (Učenje)
- **Šta pamti i kako mijenja:** 
  - Replay buffer: Store events u SQLite DB.
  - Online update: Fine-tune session embeddings na novim events.
  - Batch retrain: Nightly update global model (matrix factorization) na novim labeled data.
- **Retrigger:** Svakih 1000 events ili drop u NDCG >5%.
- **Metode:** Incremental SGD za embeddings; periodic full retrain za CF model.

## Acceptance Kriteriji
- **Functional:**
  - Agent prima event i vraća top-10 recommendations <200ms (local dev).
  - NDCG@10 na test setu >=0.7 (baseline: popularity-based).
  - Persists >1000 events bez gubitka.
  - Retrain job povećava CTR za >5% nakon 1 dana simulacije.
- **Non-functional:**
  - Clean Architecture: Domain sloj bez dependencies na infra; Web sloj tanak (<50 lines).
  - Tick loop: Event-driven, ne blocking UI.
  - Security: No SQL injection; API protected basic auth.
- **Edge cases:**
  - New user: Fallback na popular items.
  - Low confidence: Flag "explore" mode.
  - High load: Queue events, async processing.

## OpenAPI Endpoints (Minimal)
- **GET /recommend?user_id={}&session_id={}&n=10**
  - Response: `{"items": [{"id": "item1", "score": 0.9, "reason": "Based on history"}]}`
- **POST /events** (body: event JSON)
  - Response: 200 OK
- **POST /admin/retrain** (protected)
  - Response: 200 OK + log

## Testni Plan
- **Unit tests:** Think module (scorer accuracy), Learner (buffer size).
- **Integration:** Tick loop (mock events → recommendations).
- **Performance:** Load test 100 req/s.
- **Acceptance:** Simuliraj 1 dan events, provjeri NDCG uplift.

## LLM Workflow
- **Ideacija (GPT/Copilot Chat):** "Predloži 3 alternative za session-aware recommender; navedi slabosti i proširenja."
- **Kod (Claude/Copilot IDE):** "Generiši `src/domain/recommender.py` s hybrid scorer; koristi dependency injection."
- **Review (GPT):** "Review kod za coupling; predloži 3 poboljšanja za S→T→A→L separation."

## Ideje za Proširenje
- **Uncertainty:** Agent označava nesigurne preporuke i traži feedback.
- **Active Learning:** Traži eksplicitne ratings za najinformativnije items.
- **Explainability:** LLM-generirane razloge za top-3.
- **Multi-agent:** DecisionAgent + DataCollectorAgent za paralelno učenje.