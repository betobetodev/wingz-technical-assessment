#!/usr/bin/env python
"""
Rides API Client Simulator.
This script performs HTTP requests to the running Rides API to demonstrate and verify
its behavior (authentication, filtering, distance sorting, and pagination).
"""

import base64
import json
import sys
import urllib.error
import urllib.request

# Configuration
BASE_URL = "http://localhost:8000/api/rides/"
USERNAME = "admin"
PASSWORD = "adminpassword"

# ANSI Terminal Colors
GREEN = "\033[92m"
BLUE = "\033[94m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(title):
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{title.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}\n")


def make_request(url, method="GET", payload=None, auth=True):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/json")

    if payload:
        json_data = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
        req.data = json_data

    if auth:
        auth_str = f"{USERNAME}:{PASSWORD}"
        auth_bytes = auth_str.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        req.add_header("Authorization", f"Basic {auth_b64}")

    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            return status_code, json.loads(body) if body else None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            err_json = json.loads(body)
        except json.JSONDecodeError:
            err_json = body
        return e.code, err_json
    except urllib.error.URLError as e:
        # If localhost fails, fall back to the docker container hostname 'web'
        if "localhost" in url or "127.0.0.1" in url:
            fallback_url = url.replace("localhost:8000", "web:8000").replace(
                "127.0.0.1:8000", "web:8000"
            )
            return make_request(fallback_url, method, payload, auth)
        print(
            f"{RED}{BOLD}Connection Error:{RESET} Could not connect to {url}. "
            f"Is the web server running? ({e.reason})"
        )
        sys.exit(1)


def main():
    print_header("Rides API Client Simulator")

    # 1. Test Authentication Protection
    print(f"{BOLD}[1] Verifying Anonymous Access Restrictions...{RESET}")
    status_code, response = make_request(BASE_URL, auth=False)
    print(f"Status Code: {RED if status_code >= 400 else GREEN}{status_code}{RESET}")
    print(f"Response: {response}\n")

    # 2. Fetch All Rides (Authenticated)
    print(f"{BOLD}[2] Fetching All Rides (Authenticated as admin)...{RESET}")
    status_code, response = make_request(BASE_URL)
    print(f"Status Code: {GREEN if status_code == 200 else RED}{status_code}{RESET}")
    if status_code == 200:
        print(f"Pagination Details: Total Rides = {response.get('count')}")
        results = response.get("results", [])
        for ride in results:
            print(
                f" - {BOLD}Ride #{ride['id_ride']}{RESET} | "
                f"Status: {YELLOW}{ride['status']}{RESET} | "
                f"Rider: {ride['id_rider']['first_name']} ({ride['id_rider']['email']}) | "
                f"Driver: {ride['id_driver']['first_name'] if ride['id_driver'] else 'None'}"
            )
            print(f"   Pickup Lat/Lng: {ride['pickup_latitude']}, {ride['pickup_longitude']}")
            print(f"   Total Events: {len(ride['ride_events'])}")
            print(f"   Recent Events (24h): {len(ride['todays_ride_events'])}")
    print()

    # 3. Filter by Status
    print(f"{BOLD}[3] Filtering Rides by Status '?status=pickup'...{RESET}")
    status_code, response = make_request(f"{BASE_URL}?status=pickup")
    print(f"Status Code: {GREEN if status_code == 200 else RED}{status_code}{RESET}")
    if status_code == 200:
        results = response.get("results", [])
        print(f"Found {len(results)} rides in 'pickup' status:")
        for ride in results:
            print(f" - Ride #{ride['id_ride']} Status: {ride['status']}")
    print()

    # 4. Sorting by Euclidean Proximity
    # We pass coordinates near Ride #1 (which is at 37.7749, -122.4194)
    print(f"{BOLD}[4] Sorting Rides by Proximity to Coordinate (37.7749, -122.4194)...{RESET}")
    status_code, response = make_request(
        f"{BASE_URL}?near_lat=37.7749&near_lng=-122.4194&ordering=distance"
    )
    print(f"Status Code: {GREEN if status_code == 200 else RED}{status_code}{RESET}")
    if status_code == 200:
        results = response.get("results", [])
        print("Rides ordered by closest to coordinates:")
        for idx, ride in enumerate(results):
            lat, lng = ride["pickup_latitude"], ride["pickup_longitude"]
            print(f" {idx + 1}. Ride #{ride['id_ride']} at ({lat}, {lng})")
    print()

    # 5. Fetch Specific Ride and Nested Events Details
    print(f"{BOLD}[5] Fetching Detail Endpoint for Ride #1 (verifying nesting details)...{RESET}")
    status_code, response = make_request(f"{BASE_URL}1/")
    print(f"Status Code: {GREEN if status_code == 200 else RED}{status_code}{RESET}")
    if status_code == 200:
        print(f"Ride #{response['id_ride']} details:")
        print(f"  Rider: {response['id_rider']}")
        print(f"  Driver: {response['id_driver']}")
        print("  All Historical Events:")
        for event in response["ride_events"]:
            print(f"   * [{event['created_at']}] {event['description']}")
        print("  Recent (24h) Events:")
        for event in response["todays_ride_events"]:
            print(f"   * [{event['created_at']}] {event['description']}")
    print()

    print_header("Simulation Finished")


if __name__ == "__main__":
    main()
