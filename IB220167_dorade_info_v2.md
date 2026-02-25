# IB220167_dorade_info_v2

1. Background runner/worker sa NoWork izlazom

- Šta je bilo prije:
  - Orchestrator.step() se pozivao isključivo kroz HTTP zahtjev (korisnik klikne), bez autonomnog tick loop-a.
  - Nije postojao background worker niti NoWork izlaz kada nema posla.
  - Eventi nisu išli u queue; obrada je bila direktna u request-u.

- Šta je poslije:
  - Implementiran background runner koji periodično poziva tick() i obrađuje po jedan event iz queue-a.
  - Dodan NoWork izlaz kada nema posla, a loop nastavlja raditi bez nepotrebnog trošenja resursa.
  - Eventi se spremaju u bazu sa statusom pending/processed i obrađuju u pozadini.

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/application/runner.py
    - Klasa: BackgroundRunner
    - Metode: run(), tick(), get_next_event(), get_stats(), stop()
  - src/application/orchestrator.py
    - Klasa: Orchestrator
    - Metoda: tick()
    - Metoda: step() (sada samo vraća preporuke)
  - src/infrastructure/db.py
    - Model: EventModel (dodano polje status)
  - src/interface/api.py
    - Startup/shutdown: startup_event(), shutdown_event()
    - Endpoint: /events (sada queue-uje event)
    - Endpointi: /runner/stats, /runner/events


2. Thin Web Layer (web sloj tanak)

- Šta je bilo prije:
  - src/interface/api.py je imao poslovnu logiku u endpointima.
  - /feedback je direktno pozivao learner i recommender.update_model(), uz validaciju u web sloju.
  - /stats je radio poslovnu agregaciju (liked/disliked, favorite_mood) direktno u api.py.

- Šta je poslije:
  - Poslovna logika premještena u application sloj (FeedbackService).
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

3. Learn integracija u autonomnom tick-u - PRAVI Collaborative Filtering (obavezna crvena zastavica)

- Šta je bilo prije:
  - Event iz runnera nije imao polja 'name' i 'rating' koja DummyLearner očekuje.
  - Orchestrator.tick() pozivao learner.learn(event), ali learner nije mogao raditi jer su nedostajala polja.
  - Nije bilo demo-a koji pokazuje da se preporuke mijenjaju nakon feedbacka.
  - Trebala je samo memorija (lookup u bazi), a ne ML model.

- Šta je poslije:
  - ⭐ PRAVI LEARNING: Implementiran mlRecommender sa **Collaborative Filtering** (cosine similarity)
  - EventModel proširena sa poljima user_name, rating, mood.
  - DummyLearner sada:
    * Sprema feedback u FeedbackModel
    * Poziva recommender.update_model() da učita nove feedback-e u ratings matricu
    * Cosine similarity pronalazi SLIČNE KORISNIKE na osnovu rating history
  - MLRecommender sada koristi:
    * Cosine similarity između korisnika (ne KNN) za fleksibilnost
    * Pronalazi slične korisnike koji su dali visokim ocjenama filmovima
    * Vraća preporuke filmova koje su slični korisnici voljeli
    * Fallback: popularne preporuke za nove korisnike
  - Kreiran demo script test_collaborative_learning.py koji pokazuje:
    * Alice dobija inicijalne (popularne) preporuke
    * Alice i Bob daju feedback (like određene filmove)
    * Alice dobija nove preporuke na osnovu Bob-a (sličan korinik)
    * Agent je ZAISTA naučio kroz collaborative intelligence!

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/infrastructure/db.py
    - Model: EventModel (dodana polja user_name, rating, mood)
  - src/infrastructure/learner_impl.py
    - Klasa: DummyLearner
    - Konstruktor: __init__(self, recommender) - sada prima recommender referencu
    - Metoda: learn() (sprema feedback + poziva recommender.update_model() za ML)
  - src/infrastructure/recommender_impl.py (KOMPLETNO REENGINEERED)
    - Klasa: MLRecommender
    - Metoda: recommend() (vraća liked + collaborative + popular preporuke)
    - Metoda: _get_collaborative_recommendations() (cosine similarity pronalazi slične korisnike)
    - Metoda: _get_popular_recommendations() (fallback za nove korisnike)
    - Metoda: _load_feedback_ratings() (učitava feedback iz baze u matricu)
    - Metoda: update_model() (učitava nove feedback-e za cosine similarity)
  - src/interface/api.py
    - Globalna instance: recommender_instance (dijeljena između learner-a i orchestrator-a)
    - Startup: recommender se kreira jednom i koristi se svuda
  - src/application/orchestrator.py
    - Klasa: Orchestrator
    - Metoda: tick() (guard za Learn poziv: samo ako postoji rating)
  - test_collaborative_learning.py
    - Demo script koji pokazuje pravi ML learning (ne samo memorija)
    - Korak 1: Alice dobija preporuke
    - Korak 2: Alice i Bob daju feedback
    - Korak 3: Alice dobija drugačije preporuke jer agent pronalazi Bob-a kao sličnog korisnika


4. Queue status tranzicije (obavezna crvena zastavica) + Thin web za /events (preporučena) + Sensor kontekst u Think fazi (preporučena)

- Šta je bilo prije:
  - get_next_event() u runner.py postavljao event.status='processed' PRIJE nego orchestrator.tick() obradi event.
  - Ako tick() padne, event je već markiran kao processed i gubi se (neće se ponovo obraditi).
  - Endpointi /events i /runner/events radili direktan DB rad u api.py (nije thin web).
  - Sensor context (self.sensor.sense()) se uzimao ali nije korišten u Think fazi.

- Šta je poslije:
  - Implementiran pending → processing → processed/failed flow u runner.py.
  - Status se postavlja na 'processing' PRIJE tick(), pa 'processed' nakon uspjeha ili 'failed' nakon exception-a.
  - Kreiran EventQueueService u application sloju sa metodama enqueue_event() i get_queue_stats().
  - API endpointi /events i /runner/events delegiraju na EventQueueService (thin web pattern).
  - Orchestrator u tick() koristi sensor context kao fallback za user_name i mood u Think fazi.

- Gdje se promjena vidi u kodu (putanja/fajl/klasa/metoda):
  - src/application/runner.py
    - Klasa: BackgroundRunner
    - Metoda: tick() (tranzicija pending → processing → processed/failed)
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