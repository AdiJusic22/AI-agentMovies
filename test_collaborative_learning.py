"""
Demo: Collaborative Filtering Learning
Pokazuje kako agent uči kroz collaborative filtering:
- Novi korisnik dobija popularne preporuke
- Nakon što da feedback (like), agent pronalazi slične korisnike
- Sljedeće preporuke su drugačije jer koristi collaborative intelligence
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"
USER1 = "Alice"
MOOD = "happy"
TEST_MOVIE_ID = 1  # Toy Story

print("\n=== COLLABORATIVE FILTERING DEMO ===\n")

# 1) Alice dobija inicijalne preporuke (popularne za happy mood)
print("1️⃣  INITIAL RECOMMENDATIONS FOR ALICE (happy mood)")
print("   No feedback yet - showing popular movies")
resp = requests.get(f"{BASE_URL}/recommend", params={"name": USER1, "mood": MOOD})
initial_recs = resp.json()
print(f"   Got {len(initial_recs)} recommendations")
for i, movie in enumerate(initial_recs[:3], 1):
    print(f"     {i}. {movie['title']} (score: {movie['score']:.1f}) - {movie['reason']}")

# 2) Alice daje feedback - joj se sviđa film sa ID 1
print("\n2️⃣  ALICE GIVES FEEDBACK - Likes movie ID 1")
feedback_payload = {
    "name": USER1,
    "item_id": TEST_MOVIE_ID,
    "rating": 5,
    "mood": MOOD
}
resp = requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
print(f"   Feedback sent: {resp.json()}")

# 3) Simzaj još jedan korisnik koji isto voli ID 1 i slične filmove
print("\n3️⃣  BOB provides feedback (also likes movie 1)")
for movie_id, rating in [(TEST_MOVIE_ID, 5), (10, 4), (15, 5)]:
    feedback_payload = {
        "name": "Bob",
        "item_id": movie_id,
        "rating": rating,
        "mood": MOOD
    }
    resp = requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
    print(f"   Bob rated movie {movie_id}: {rating}")
    time.sleep(0.3)

# 4) Alice dobija nove preporuke - sada koristi collaborative intelligence
print("\n4️⃣  ALICE GETS NEW RECOMMENDATIONS (after feedback)")
print("   Now shows movies similar users liked!")
resp = requests.get(f"{BASE_URL}/recommend", params={"name": USER1, "mood": MOOD})
new_recs = resp.json()
print(f"   Got {len(new_recs)} recommendations")
for i, movie in enumerate(new_recs[:3], 1):
    print(f"     {i}. {movie['title']} (score: {movie['score']:.1f}) - {movie['reason']}")

# 5) Uspoređivanje
print("\n5️⃣  COMPARISON:")
initial_titles = [m['title'] for m in initial_recs[:3]]
new_titles = [m['title'] for m in new_recs[:3]]

if initial_titles != new_titles:
    print("   ✅ LEARNING WORKED! Recommendations changed after feedback")
    print(f"      Before: {initial_titles[:2]}")
    print(f"      After:  {new_titles[:2]}")
else:
    print("   ℹ️  Recommendations are same (model may already know Bob's taste)")

print("\n=== PRAVI AGENT UČI KROZ COLLABORATIVE FILTERING ===\n")
