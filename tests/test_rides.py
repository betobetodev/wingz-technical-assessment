from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from rides.models import Ride, RideEvent, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin_user",
        role="admin",
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
    )


@pytest.fixture
def rider_user(db):
    return User.objects.create_user(
        username="rider_user",
        role="rider",
        first_name="Rider",
        last_name="User",
        email="rider@example.com",
    )


@pytest.fixture
def driver_user(db):
    return User.objects.create_user(
        username="driver_user",
        role="driver",
        first_name="Driver",
        last_name="User",
        email="driver@example.com",
    )


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def rider_client(api_client, rider_user):
    api_client.force_authenticate(user=rider_user)
    return api_client


def create_test_ride(rider, driver, **kwargs):
    defaults = {
        "status": "pickup",
        "id_rider": rider,
        "id_driver": driver,
        "pickup_latitude": 37.7749,
        "pickup_longitude": -122.4194,
        "dropoff_latitude": 37.7849,
        "dropoff_longitude": -122.4094,
        "pickup_time": timezone.now(),
    }
    defaults.update(kwargs)
    return Ride.objects.create(**defaults)


# ==============================================================================
# Category 1: Authentication & Role-Based Access Tests
# ==============================================================================


@pytest.mark.django_db
def test_anonymous_request_blocked(api_client):
    """
    Verify that anonymous or unauthenticated requests are blocked.
    """
    # Test GET list
    response = api_client.get("/api/rides/")
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )

    # Test POST create
    response = api_client.post("/api/rides/", {})
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@pytest.mark.django_db
def test_non_admin_request_blocked(rider_client, rider_user, driver_user):
    """
    Verify that an authenticated user with a non-admin role (e.g., 'rider')
    receives HTTP 403 Forbidden when calling any CRUD endpoint.
    """
    ride = create_test_ride(rider_user, driver_user)

    # Test GET list
    response = rider_client.get("/api/rides/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test GET detail
    response = rider_client.get(f"/api/rides/{ride.id_ride}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test POST create
    response = rider_client.post("/api/rides/", {})
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test PUT update
    response = rider_client.put(f"/api/rides/{ride.id_ride}/", {})
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Test DELETE
    response = rider_client.delete(f"/api/rides/{ride.id_ride}/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_admin_request_allowed(admin_client, rider_user, driver_user):
    """
    Verify that an authenticated user with 'admin' role can successfully
    access the endpoints.
    """
    response = admin_client.get("/api/rides/")
    assert response.status_code == status.HTTP_200_OK


# ==============================================================================
# Category 2: Ride List API & Filtering Tests
# ==============================================================================


@pytest.mark.django_db
def test_ride_list_fields_and_nesting(admin_client, rider_user, driver_user):
    """
    Verify that the Ride list endpoint returns the correct fields,
    including the nested related objects (id_rider, id_driver, and ride_events).
    """
    ride = create_test_ride(rider_user, driver_user, status="pickup")
    event1 = RideEvent.objects.create(
        id_ride=ride, description="Driver accepted", created_at=timezone.now()
    )
    event2 = RideEvent.objects.create(
        id_ride=ride, description="Driver arrived", created_at=timezone.now()
    )

    response = admin_client.get("/api/rides/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # The payload is paginated, so actual list is in 'results'
    assert "results" in data
    results = data["results"]
    assert len(results) == 1

    ride_data = results[0]
    assert ride_data["id_ride"] == ride.id_ride
    assert ride_data["status"] == "pickup"

    # Verify nested rider
    assert "id_rider" in ride_data
    assert ride_data["id_rider"]["id_user"] == rider_user.id_user
    assert ride_data["id_rider"]["username"] == rider_user.username
    assert ride_data["id_rider"]["role"] == "rider"

    # Verify nested driver
    assert "id_driver" in ride_data
    assert ride_data["id_driver"]["id_user"] == driver_user.id_user
    assert ride_data["id_driver"]["username"] == driver_user.username
    assert ride_data["id_driver"]["role"] == "driver"

    # Verify nested ride events
    assert "ride_events" in ride_data
    assert len(ride_data["ride_events"]) == 2
    assert ride_data["ride_events"][0]["id_ride_event"] == event1.id_ride_event
    assert ride_data["ride_events"][0]["description"] == "Driver accepted"
    assert ride_data["ride_events"][1]["id_ride_event"] == event2.id_ride_event
    assert ride_data["ride_events"][1]["description"] == "Driver arrived"


@pytest.mark.django_db
def test_ride_list_pagination(admin_client, rider_user, driver_user):
    """
    Verify that pagination works correctly (limit/offset parameters are respected
    and payload contains keys like 'results' and 'count').
    """
    # Create 12 rides
    for i in range(12):
        create_test_ride(rider_user, driver_user, status=f"ride_{i}")

    # Request first page of 5 items
    response = admin_client.get("/api/rides/?limit=5&offset=0")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "count" in data
    assert "results" in data
    assert "next" in data
    assert "previous" in data

    assert data["count"] == 12
    assert len(data["results"]) == 5

    # Request next page
    response = admin_client.get("/api/rides/?limit=5&offset=5")
    assert response.status_code == status.HTTP_200_OK
    data_page2 = response.json()
    assert len(data_page2["results"]) == 5


@pytest.mark.django_db
def test_filtering_by_status(admin_client, rider_user, driver_user):
    """
    Verify filtering rides by status (e.g., /api/rides/?status=pickup).
    """
    # Create 2 rides with status 'pickup' and 3 rides with status 'en-route'
    create_test_ride(rider_user, driver_user, status="pickup")
    create_test_ride(rider_user, driver_user, status="pickup")
    create_test_ride(rider_user, driver_user, status="en-route")
    create_test_ride(rider_user, driver_user, status="en-route")
    create_test_ride(rider_user, driver_user, status="en-route")

    # Filter for 'pickup'
    response = admin_client.get("/api/rides/?status=pickup")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 2
    for r in results:
        assert r["status"] == "pickup"

    # Filter for 'en-route'
    response = admin_client.get("/api/rides/?status=en-route")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 3
    for r in results:
        assert r["status"] == "en-route"


@pytest.mark.django_db
def test_filtering_by_rider_email(admin_client, rider_user, driver_user):
    """
    Verify filtering by rider email (e.g., /api/rides/?rider_email=test@example.com).
    """
    rider2 = User.objects.create_user(username="rider2", role="rider", email="rider2@example.com")

    # 3 rides for rider_user (rider@example.com)
    create_test_ride(rider_user, driver_user)
    create_test_ride(rider_user, driver_user)
    create_test_ride(rider_user, driver_user)

    # 1 ride for rider2 (rider2@example.com)
    create_test_ride(rider2, driver_user)

    # Filter for rider2
    response = admin_client.get("/api/rides/?rider_email=rider2@example.com")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["id_rider"]["email"] == "rider2@example.com"


# ==============================================================================
# Category 3: Advanced Sorting Tests
# ==============================================================================


@pytest.mark.django_db
def test_sorting_by_pickup_time(admin_client, rider_user, driver_user):
    """
    Verify sorting rides by pickup_time in both ascending and descending order.
    """
    now = timezone.now()
    r1 = create_test_ride(rider_user, driver_user, pickup_time=now - timedelta(hours=2))
    r2 = create_test_ride(rider_user, driver_user, pickup_time=now)
    r3 = create_test_ride(rider_user, driver_user, pickup_time=now - timedelta(hours=1))

    # Ascending order
    response = admin_client.get("/api/rides/?ordering=pickup_time")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert results[0]["id_ride"] == r1.id_ride
    assert results[1]["id_ride"] == r3.id_ride
    assert results[2]["id_ride"] == r2.id_ride

    # Descending order
    response = admin_client.get("/api/rides/?ordering=-pickup_time")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert results[0]["id_ride"] == r2.id_ride
    assert results[1]["id_ride"] == r3.id_ride
    assert results[2]["id_ride"] == r1.id_ride


@pytest.mark.django_db
def test_sorting_by_distance(admin_client, rider_user, driver_user):
    """
    Verify sorting rides by calculated distance from a specified coordinate.
    """
    # Coordinates of target: 37.7749, -122.4194
    # Ride A: Exactly at the target (closest)
    r_a = create_test_ride(
        rider_user, driver_user, pickup_latitude=37.7749, pickup_longitude=-122.4194
    )
    # Ride B: Moderately close
    r_b = create_test_ride(
        rider_user, driver_user, pickup_latitude=37.7800, pickup_longitude=-122.4200
    )
    # Ride C: Farthest away
    r_c = create_test_ride(
        rider_user, driver_user, pickup_latitude=37.9000, pickup_longitude=-122.5000
    )

    response = admin_client.get("/api/rides/?near_lat=37.7749&near_lng=-122.4194")
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]

    assert len(results) == 3
    assert results[0]["id_ride"] == r_a.id_ride
    assert results[1]["id_ride"] == r_b.id_ride
    assert results[2]["id_ride"] == r_c.id_ride


# ==============================================================================
# Category 4: Performance & Query Budget Tests
# ==============================================================================


@pytest.mark.django_db
def test_todays_ride_events_field(admin_client, rider_user, driver_user):
    """
    Verify that each ride contains the field 'todays_ride_events' showing
    only events created within the last 24 hours.
    """
    ride = create_test_ride(rider_user, driver_user)
    now = timezone.now()

    # Event 1: 12 hours ago (should be included in todays_ride_events)
    event1 = RideEvent.objects.create(
        id_ride=ride, description="Recent event", created_at=now - timedelta(hours=12)
    )

    # Event 2: 36 hours ago (should be excluded from todays_ride_events)
    event2 = RideEvent.objects.create(
        id_ride=ride, description="Old event", created_at=now - timedelta(hours=36)
    )

    response = admin_client.get("/api/rides/")
    assert response.status_code == status.HTTP_200_OK
    ride_data = response.json()["results"][0]

    # 'ride_events' contains both
    all_events = ride_data["ride_events"]
    assert len(all_events) == 2
    event_ids = [e["id_ride_event"] for e in all_events]
    assert event1.id_ride_event in event_ids
    assert event2.id_ride_event in event_ids

    # 'todays_ride_events' contains only the one within 24h
    todays = ride_data["todays_ride_events"]
    assert len(todays) == 1
    assert todays[0]["id_ride_event"] == event1.id_ride_event
    assert todays[0]["description"] == "Recent event"


@pytest.mark.django_db
def test_query_count_limit(admin_client, django_assert_num_queries, rider_user, driver_user):
    """
    Assert that calling the Ride list endpoint fetches the page of rides,
    riders, drivers, and ride events in exactly 3 queries (including the
    pagination COUNT query). No extra queries per row (N+1 query check).
    """
    # Create 5 rides, each with 3 events
    for i in range(5):
        ride = create_test_ride(rider_user, driver_user)
        for j in range(3):
            RideEvent.objects.create(
                id_ride=ride,
                description=f"Ride {i} Event {j}",
                created_at=timezone.now(),
            )

    # The expected queries are:
    # 1. COUNT(*) to get pagination count
    # 2. SELECT * FROM rides (joining users via select_related)
    # 3. SELECT * FROM ride_events WHERE id_ride IN (...) (prefetch_related)
    with django_assert_num_queries(3):
        response = admin_client.get("/api/rides/")
        assert response.status_code == status.HTTP_200_OK

    results = response.json()["results"]
    assert len(results) == 5
