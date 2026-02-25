# IB220167_dorade_info_v2

1. Background runner/worker sa NoWork izlazom

- Sta je bilo prije:
  - Orchestrator.step() se pozivao iskljucivo kroz HTTP zahtjev (korisnik klikne), bez autonomnog tick loop-a.
  - Nije postojao background worker niti NoWork izlaz kada nema posla.
  - Eventi nisu isli u queue; obrada je bila direktna u request-u.

- Sta je poslije:
  - Implementiran background runner koji periodicno poziva tick() i obradjuje po jedan event iz queue-a.
  - Dodan NoWork izlaz kada nema posla, a loop nastavlja raditi bez nepotrebnog trosenja resursa.
  - Eventi se spremaju u bazu sa statusom pending/processed i obradjuju u pozadini.

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/application/runner.py
    - Klasa: BackgroundRunner
    - Metode: run(), tick(), get_next_event(), get_stats(), stop()
  - src/application/orchestrator.py
    - Klasa: Orchestrator
    - Metoda: tick()
    - Metoda: step() (sada samo vraca preporuke)
  - src/infrastructure/db.py
    - Model: EventModel (dodano polje status)
  - src/interface/api.py
    - Startup/shutdown: startup_event(), shutdown_event()
    - Endpoint: /events (sada queue-uje event)
    - Endpointi: /runner/stats, /runner/events


2. Thin Web Layer (web sloj tanak)

- Sta je bilo prije:
  - src/interface/api.py je imao poslovnu logiku u endpointima.
  - /feedback je direktno pozivao learner i recommender.update_model(), uz validaciju u web sloju.
  - /stats je radio poslovnu agregaciju (liked/disliked, favorite_mood) direktno u api.py.

- Sta je poslije:
  - Poslovna logika premjestena u application sloj (FeedbackService).
  - Web sloj samo prima request i delegira na servis, bez poslovne logike.
  - Validacija, agregacije i model update su u servisu.

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/application/feedback_service.py
    - Klasa: FeedbackService
    - Metode: process_feedback(), get_user_statistics(), get_user_ratings()
  - src/interface/api.py
    - Endpoint: /feedback (delegira na FeedbackService.process_feedback)
    - Endpoint: /stats (delegira na FeedbackService.get_user_statistics)
    - Endpoint: /ratings (delegira na FeedbackService.get_user_ratings)
    - Dependency: get_feedback_service()


3. Learn integracija u autonomnom tick-u (obavezna crvena zastavica)

- Sta je bilo prije:
  - Event iz runnera nije imao polja 'name' i 'rating' koja DummyLearner ocekuje.
  - Orchestrator.tick() pozivao learner.learn(event), ali learner nije mogao raditi jer su nedostajala polja.
  - Nije bilo demo-a koji pokazuje da se preporuke mijenjaju nakon feedbacka.

- Sta je poslije:
  - EventModel prosirena sa poljima user_name, rating, mood.
  - DummyLearner prihvata i 'name' i 'user_name'.
  - Learn faza snima feedback u bazu i azurira model (update_model) nakon feedback-a.
  - Implementiran collaborative filtering sa cosine similarity (pravi learning, ne samo memorija).
  - Dodan demo script test_collaborative_learning.py i test_simple_learning.py.

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/infrastructure/db.py
    - Model: EventModel (dodana polja user_name, rating, mood)
  - src/infrastructure/learner_impl.py
    - Klasa: DummyLearner
    - Metoda: learn() (validacija polja, snima feedback, poziva update_model)
  - src/infrastructure/recommender_impl.py
    - Klasa: MLRecommender
    - Metoda: recommend() (liked + collaborative + popular fallback)
    - Metoda: _get_collaborative_recommendations() (cosine similarity)
    - Metoda: _get_popular_recommendations()
    - Metoda: _load_feedback_ratings()
    - Metoda: update_model()
  - src/application/orchestrator.py
    - Klasa: Orchestrator
    - Metoda: tick() (Learn poziv samo ako postoji rating)
  - test_collaborative_learning.py
  - test_simple_learning.py


4. Queue status tranzicije (obavezna crvena zastavica) + Thin web za /events (preporucena) + Sensor kontekst u Think fazi (preporucena)

- Sta je bilo prije:
  - get_next_event() u runner.py postavljao event.status='processed' prije nego orchestrator.tick() obradi event.
  - Ako tick() padne, event je vec markiran kao processed i gubi se (nece se ponovo obraditi).
  - Endpointi /events i /runner/events radili direktan DB rad u api.py (nije thin web).
  - Sensor context (self.sensor.sense()) se uzimao ali nije koristio u Think fazi.

- Sta je poslije:
  - Implementiran pending -> processing -> processed/failed flow u runner.py.
  - Status se postavlja na 'processing' prije tick(), pa 'processed' nakon uspjeha ili 'failed' nakon exception-a.
  - Kreiran EventQueueService u application sloju sa metodama enqueue_event() i get_queue_stats().
  - API endpointi /events i /runner/events delegiraju na EventQueueService (thin web pattern).
  - Orchestrator u tick() koristi sensor context kao fallback za user_name i mood u Think fazi.

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/application/runner.py
    - Klasa: BackgroundRunner
    - Metoda: tick() (tranzicija pending -> processing -> processed/failed)
    - Metoda: _mark_event_status() (helper za promjenu statusa)
  - src/application/event_service.py
    - Klasa: EventQueueService
    - Metode: enqueue_event(), get_queue_stats()
  - src/interface/api.py
    - Endpoint: /events (delegira na EventQueueService.enqueue_event)
    - Endpoint: /runner/events (delegira na EventQueueService.get_queue_stats)
    - Dependency: get_event_service()
  - src/application/orchestrator.py
    - Klasa: Orchestrator
    - Metoda: tick() (koristi sensor context za fallback user_name i mood)
