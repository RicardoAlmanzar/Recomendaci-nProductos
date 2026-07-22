import sys
import httpx

def check_deployment(base_url="http://localhost:8000"):
    print(f"Validating deployment at {base_url}...")
    try:
        health = httpx.get(f"{base_url}/health")
        if health.status_code == 200:
            print("[\u2713] Health check OK.")
        else:
            print(f"[X] Health check failed with {health.status_code}")
            sys.exit(1)
            
        readiness = httpx.get(f"{base_url}/readiness")
        if readiness.status_code == 200:
            print("[\u2713] Readiness check OK.")
        else:
            print(f"[X] Readiness check failed with {readiness.status_code}")
            sys.exit(1)
            
        print("\nDeployment validation successful! The engine is ready.")
    except httpx.RequestError as e:
        print(f"[X] Connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    check_deployment(url)
