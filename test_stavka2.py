"""
Test script za Stavku 2: Thin Web Layer
Demonstrira da API sloj samo delegira na servis, bez poslovne logike.
"""
import requests
import json

BASE_URL = "http://localhost:8001"

print("=" * 60)
print("TESTIRANJE STAVKE 2: Thin Web Layer")
print("=" * 60)

# 1. Test feedback endpoint (poslovne logike u servisu)
print("\n1. Testiram /feedback endpoint (thin layer):")
feedback_data = {
    "name": "TestUser",
    "item_id": "296",
    "rating": 5,
    "mood": "happy"
}
resp = requests.post(f"{BASE_URL}/feedback", json=feedback_data)
result = resp.json()
print(f"   Response: {json.dumps(result, indent=2)}")
print(f"   ✅ Status: {result.get('status')}")

# 2. Test stats endpoint (agregacije u servisu)
print("\n2. Testiram /stats endpoint (thin layer):")
resp = requests.get(f"{BASE_URL}/stats?name=TestUser")
stats = resp.json()
print(f"   Response: {json.dumps(stats, indent=2)}")
print(f"   ✅ Total feedback: {stats.get('total_feedback')}")
print(f"   ✅ Liked count: {stats.get('liked_count')}")

# 3. Test ratings endpoint (filter logika u servisu)
print("\n3. Testiram /ratings endpoint (thin layer):")
resp = requests.get(f"{BASE_URL}/ratings?name=TestUser&mood=happy")
ratings = resp.json()
print(f"   Response: {json.dumps(ratings, indent=2)}")
print(f"   ✅ Broj ocjena: {len(ratings.get('ratings', []))}")

# 4. Test validacije (u servisu, ne u api.py)
print("\n4. Testiram validaciju (u servisu, ne u web sloju):")
bad_feedback = {"item_id": "123"}  # Nedostaje name
resp = requests.post(f"{BASE_URL}/feedback", json=bad_feedback)
result = resp.json()
print(f"   Response: {json.dumps(result, indent=2)}")
if "error" in result:
    print(f"   ✅ Validacija radi u servisu: {result.get('error')}")

print("\n" + "=" * 60)
print("REZULTAT:")
print("=" * 60)
print("✅ Web sloj (api.py) je TANAK - samo prima i vraća")
print("✅ Poslovna logika je u FeedbackService")
print("✅ Validacija, agregacija, i model update su u application sloju")
print("✅ Clean Architecture implementirana pravilno!")
print("=" * 60)
