from pprint import pprint

from fastapi.testclient import TestClient

from main import app
from seed import seed_data


def run_demo() -> None:
	seed_data()

	with TestClient(app) as client:
		print("=" * 72)
		print("1. Route 1 - Customers")
		print("=" * 72)

		customers_response = client.get("/customers")
		customers_response.raise_for_status()
		customers = customers_response.json()
		print(f"Total customers: {len(customers)}")
		pprint(customers)

		print()
		customer_id = "CUST-001"
		customer_response = client.get(f"/customers/{customer_id}")
		customer_response.raise_for_status()
		print(f"Customer detail for {customer_id}:")
		pprint(customer_response.json())

		print()
		print("=" * 72)
		print("2. Route 2 - Recommendations")
		print("=" * 72)

		recommendation_response = client.post(
			"/recommendations",
			json={"customer_id": customer_id, "limit": 5},
		)
		recommendation_response.raise_for_status()
		recommendation_payload = recommendation_response.json()
		print("Recommendations payload:")
		pprint(recommendation_payload)

		print()
		print("Resumen:")
		print(f"- Customers disponibles: {len(customers)}")
		print(f"- Recommendations generadas: {len(recommendation_payload['recommendations'])}")
		print(f"- Customer usado: {recommendation_payload['customer_id']}")


if __name__ == "__main__":
	run_demo()
