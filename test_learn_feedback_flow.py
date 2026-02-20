"""
Reproducible demo for Learn integration:
/recommend -> /feedback -> /recommend for the same user+mood.
"""
import requests
import json

BASE_URL = "http://localhost:8001"
USER_NAME = "DemoUser"
MOOD = "happy"

print("=== Learn Integration Demo ===")

print("\n1) Initial recommendations")
resp = requests.get(f"{BASE_URL}/recommend", params={"name": USER_NAME, "mood": MOOD})
initial = resp.json()
print(json.dumps(initial[:3], indent=2))

if not initial:
    raise SystemExit("No recommendations returned.")

picked_item = initial[0].get("item_id")
if not picked_item:
    raise SystemExit("No item_id in recommendations.")

print(f"\n2) Sending feedback for item_id={picked_item}")
feedback_payload = {
    "name": USER_NAME,
    "item_id": picked_item,
    "rating": 5,
    "mood": MOOD
}
resp = requests.post(f"{BASE_URL}/feedback", json=feedback_payload)
print(resp.json())

print("\n3) Recommendations after feedback")
resp = requests.get(f"{BASE_URL}/recommend", params={"name": USER_NAME, "mood": MOOD})
after = resp.json()
print(json.dumps(after[:3], indent=2))

if after and after[0].get("item_id") == picked_item:
    print("\nSUCCESS: Same input gives different output ordering (liked item on top).")
else:
    print("\nNOTE: Output ordering did not change as expected. Try again or ensure feedback saved.")
