"""
Test script za Stavku 1: Background Runner
Demonstrira autonomni rad agent-a
"""
import requests
import time
import json

BASE_URL = "http://localhost:8001"

print("=" * 60)
print("TESTIRANJE STAVKE 1: Background Runner")
print("=" * 60)

# 1. Proveri runner stats (početno stanje)
print("\n1. Runner statistike (početno stanje):")
resp = requests.get(f"{BASE_URL}/runner/stats")
stats_before = resp.json()
print(json.dumps(stats_before, indent=2))
print(f"   - Runner je aktivan: {stats_before.get('running')}")
print(f"   - Obrađeno događaja: {stats_before.get('total_processed')}")
print(f"   - NoWork ticks: {stats_before.get('total_no_work')}")

# 2. Proveri queue
print("\n2. Stanje queue-a:")
resp = requests.get(f"{BASE_URL}/runner/events")
queue_before = resp.json()
print(json.dumps(queue_before, indent=2))
print(f"   - Pending: {queue_before.get('pending')}")
print(f"   - Processed: {queue_before.get('processed')}")

# 3. Dodaj 3 test event-a u queue
print("\n3. Dodajem 3 test event-a u queue...")
events = [
    {"user_id": "test_user_1", "event_type": "click", "item_id": "296", "session_id": "sess_1"},
    {"user_id": "test_user_2", "event_type": "view", "item_id": "356", "session_id": "sess_2"},
    {"user_id": "test_user_3", "event_type": "rating", "item_id": "480", "session_id": "sess_3"},
]

for i, event in enumerate(events, 1):
    resp = requests.post(f"{BASE_URL}/events", json=event)
    result = resp.json()
    print(f"   Event {i}: {result.get('status')} - ID: {result.get('event_id')[:8]}...")

# 4. Proveri queue odmah nakon dodavanja
print("\n4. Queue nakon dodavanja event-a:")
resp = requests.get(f"{BASE_URL}/runner/events")
queue_after_add = resp.json()
print(json.dumps(queue_after_add, indent=2))
print(f"   - Pending: {queue_after_add.get('pending')} (trebalo bi 3)")

# 5. Sačekaj da runner procesira (tick interval je 5s, ali može biti i kraće)
print("\n5. Čekam 10 sekundi da runner procesira event-e...")
print("   (Runner radi autonomno u pozadini - ne zavisi od nas!)")
for i in range(10, 0, -1):
    print(f"   {i}...", end=" ", flush=True)
    time.sleep(1)
print("\n")

# 6. Proveri runner stats nakon procesiranja
print("6. Runner statistike (posle procesiranja):")
resp = requests.get(f"{BASE_URL}/runner/stats")
stats_after = resp.json()
print(json.dumps(stats_after, indent=2))
print(f"   - Obrađeno događaja: {stats_after.get('total_processed')} (bilo: {stats_before.get('total_processed')})")
print(f"   - NoWork ticks: {stats_after.get('total_no_work')}")

# 7. Proveri queue posle procesiranja
print("\n7. Queue nakon procesiranja:")
resp = requests.get(f"{BASE_URL}/runner/events")
queue_after = resp.json()
print(json.dumps(queue_after, indent=2))
print(f"   - Pending: {queue_after.get('pending')} (trebalo bi 0)")
print(f"   - Processed: {queue_after.get('processed')} (trebalo bi {queue_before.get('processed', 0) + 3})")

# Zaključak
print("\n" + "=" * 60)
print("REZULTAT:")
print("=" * 60)
processed_diff = stats_after.get('total_processed', 0) - stats_before.get('total_processed', 0)
if processed_diff >= 3:
    print(f"✅ SUCCESS! Runner je autonomno procesirao {processed_diff} event-a")
    print("✅ Background loop radi!")
    print("✅ NoWork izlaz implementiran (vidi NoWork ticks)")
    print("✅ Event queue sistem funkcioniše!")
else:
    print(f"⚠️  Runner je procesirao {processed_diff} event-a (očekivano: 3)")
    print("   Možda treba sačekati još malo...")
    
print("\n💡 Runner nastavlja da radi autonomno u pozadini!")
print("=" * 60)
