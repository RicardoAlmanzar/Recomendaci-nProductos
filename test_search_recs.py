import urllib.request
import json

# Test 1: Search related recommendations WITH category filter (current broken behavior)
payload = json.dumps({
    "customer_id": "CUST-001",
    "page_type": "search",
    "slot": "related",
    "limit": 8,
    "context": {"category": "packaging"}
}).encode()

req = urllib.request.Request(
    "http://127.0.0.1:8010/recommendations",
    data=payload,
    headers={"Content-Type": "application/json"}
)

try:
    r = urllib.request.urlopen(req)
    d = json.loads(r.read().decode())
    print("=== WITH category filter (packaging) ===")
    print("Items count:", len(d.get("items", [])))
    for i in d.get("items", []):
        print(f"  - {i['name']} ({i['category']}) score={i['score']}")
    if not d.get("items"):
        print("  NO ITEMS - this confirms the bug!")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")

print()

# Test 2: Without category filter  
payload2 = json.dumps({
    "customer_id": "CUST-001",
    "page_type": "search",
    "slot": "related",
    "limit": 8
}).encode()

req2 = urllib.request.Request(
    "http://127.0.0.1:8010/recommendations",
    data=payload2,
    headers={"Content-Type": "application/json"}
)

try:
    r2 = urllib.request.urlopen(req2)
    d2 = json.loads(r2.read().decode())
    print("=== WITHOUT category filter ===")
    print("Items count:", len(d2.get("items", [])))
    for i in d2.get("items", []):
        print(f"  - {i['name']} ({i['category']}) score={i['score']} reasons={i['reason_codes']}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.read().decode()}")
