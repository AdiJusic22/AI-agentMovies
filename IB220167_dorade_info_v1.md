# IB220167_dorade_info_v1

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
