import os
import sys
import requests


BASE_URL = os.getenv(
    "HEX_API_URL",
    "http://127.0.0.1:8000",
)


def check(
    name: str,
    condition: bool,
):
    if condition:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}")
        sys.exit(1)


def main():

    print()
    print("=" * 60)
    print("HEX FINAL BACKEND SMOKE TEST")
    print("=" * 60)
    print(
        f"API: {BASE_URL}"
    )
    print()


    # -------------------------------------------------
    # 1. Root
    # -------------------------------------------------

    response = requests.get(
        f"{BASE_URL}/",
        timeout=15,
    )

    check(
        "Backend root",
        response.status_code == 200,
    )


    # -------------------------------------------------
    # 2. OpenAPI
    # -------------------------------------------------

    response = requests.get(
        f"{BASE_URL}/openapi.json",
        timeout=15,
    )

    check(
        "OpenAPI available",
        response.status_code == 200,
    )

    openapi = response.json()


    # -------------------------------------------------
    # 3. Important routes
    # -------------------------------------------------

    routes = openapi.get(
        "paths",
        {},
    )


    required_routes = [
        "/auth/login",
        "/global-exposure/{event_id}",
        "/demo/red-sea",
        "/copilot/ask",
        "/approvals",
    ]


    for route in required_routes:

        check(
            f"Route exists: {route}",
            route in routes,
        )


    # -------------------------------------------------
    # 4. Global events
    # -------------------------------------------------

    response = requests.get(
        f"{BASE_URL}/global-events/",
        params={
            "limit": 5,
        },
        timeout=20,
    )


    check(
        "Global events endpoint",
        response.status_code
        in {200, 401, 403},
    )


    # -------------------------------------------------
    # 5. Finished
    # -------------------------------------------------

    print()
    print("=" * 60)
    print("BACKEND SMOKE TEST COMPLETE")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()