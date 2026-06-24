# Wingz Rides API - Python/Django Developer Test

A robust, optimized Django REST Framework API for managing rides and event logs, backed by PostgreSQL, containerized with Docker, and verified with pytest.

---

## 1. Quick Start Requirements

To run this project, you only need three minimal tools installed on your host system:
- **Git**
- **Docker** (and Docker Compose)
- **GNU Make**

No local Python, Django, or PostgreSQL installation is needed. All dependencies run exclusively within Docker containers.

---

## 2. Setting Up the Environment

To spin up a completely fresh, built, and fully seeded environment from scratch, run:
```bash
make all
```
*Note: This command runs in **detached mode**, freeing up your terminal immediately. It clears previous containers, deletes database volumes, builds the image, runs migrations, seeds all reporting trips, and starts the server on `http://localhost:8000/`.*

---

## 3. Developer Commands Quick Reference

Use these `make` commands to control and verify the application:

| Command | Action |
| :--- | :--- |
| `make all` | Full rebuild and environment spin-up from a clean slate (detached). |
| `make test` | Runs the automated `pytest` verification suite. |
| `make lint` | Performs Ruff check-linting and formatting. |
| `make complexity` | Audits cognitive complexity metrics using Complexipy. |
| `make simulate` | Runs the interactive client simulator to verify API endpoints. |
| `make report` | Runs the raw SQL database report query and prints the output. |
| `make down` | Shuts down active compose containers. |

---

## 4. Manual API Verification (Browsable API)

1. Open the Django REST Framework interactive dashboard at `http://localhost:8000/api/rides/`.
2. Click **"Log in"** in the top-right corner to authenticate.
3. Use the default seeded credentials:
   - **Username**: `admin`
   - **Password**: `adminpassword`
4. You can now browse the endpoints, query filters, and detailed ride event logs.

---

## 5. Raw SQL Reporting Query

This SQL query matches the pickup (`Status changed to pickup`) and dropoff (`Status changed to dropoff`) events for each ride, calculates the trip duration using timestamp intervals, filters for trips lasting **more than 1 hour**, groups by Month and Driver name, and sorts chronologically.

```sql
SELECT
    TO_CHAR(pickup_event.created_at, 'YYYY-MM') AS "Month",
    CONCAT(driver.first_name, ' ', SUBSTRING(driver.last_name FROM 1 FOR 1)) AS "Driver",
    COUNT(ride.id_ride) AS "Count of Trips > 1 hr"
FROM
    rides_ride ride
JOIN
    rides_user driver ON ride.id_driver_id = driver.id_user
JOIN
    rides_rideevent pickup_event 
        ON ride.id_ride = pickup_event.id_ride_id 
        AND pickup_event.description = 'Status changed to pickup'
JOIN
    rides_rideevent dropoff_event 
        ON ride.id_ride = dropoff_event.id_ride_id 
        AND dropoff_event.description = 'Status changed to dropoff'
WHERE
    dropoff_event.created_at - pickup_event.created_at > INTERVAL '1 hour'
GROUP BY
    TO_CHAR(pickup_event.created_at, 'YYYY-MM'),
    driver.id_user,
    driver.first_name,
    driver.last_name
ORDER BY
    "Month" ASC,
    "Driver" ASC;
```

*Tip: Running `make report` will execute this exact SQL query inside the active database container and print the formatted output table.*

---

## 6. Key Design Decisions & Challenges

### A. Custom User Authentication Model
We inherited our custom `User` model from `AbstractUser` and registered it via `AUTH_USER_MODEL = "rides.User"`. This allows adding custom fields (like `role` and `phone_number`) and defining a custom primary key (`id_user`), while maintaining full compatibility with Django's native authentication backend (password hashing, sessions) without rewriting security code.

### B. The N+1 Query Problem (Constant Query Complexity)
Serializing relationships sequentially in lists is a major performance bottleneck (resulting in $1 + 2N$ queries). We solved this using:
- **Prefetching**: Viewsets overrides the queryset using `.select_related("id_rider", "id_driver")` to join user records, and `.prefetch_related("ride_events")` to fetch events in a single batch.
- **In-Memory Filtering**: Calling `.filter()` on a related manager inside a serializer field discards the prefetch cache. We evaluate `todays_ride_events` in memory using Python list comprehensions over `obj.ride_events.all()` to ensure **exactly 3 queries** are run regardless of pagination size.

### C. Database-Level Euclidean Coordinate Sorting
To sort rides by proximity (`near_lat` & `near_lng`), we avoided heavy geographic dependencies or database math functions (like SQL `POWER()`) which vary across database systems. Instead, we annotate querysets using arithmetic Django `F` expressions to compute the squared Euclidean distance ($d^2 = \Delta x^2 + \Delta y^2$), ensuring high performance and compatibility between PostgreSQL and SQLite.

### D. Seeding & Automated Tests Isolation
To prevent the reporting seed data migration (`0002_seed_data.py`) from polluting tests (which assert exact DB bounds and require clean states), we implemented environment checks in the migration file to automatically skip seeding if pytest or test arguments are detected.
