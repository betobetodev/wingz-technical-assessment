#!/usr/bin/env python
"""
Rides Report Generator.
This script runs a raw SQL query against the configured database to return the count
of Trips whose duration from Pickup to Dropoff was more than 1 hour, grouped by
Month and Driver.
"""

import os
import sys

import django

# Add project root to sys.path to resolve config module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connection  # noqa: E402


def main():
    # PostgreSQL: TO_CHAR for months, CONCAT/SUBSTRING, interval subtraction
    sql = """
    SELECT
        TO_CHAR(pickup_event.created_at, 'YYYY-MM') AS "Month",
        CONCAT(driver.first_name, ' ', SUBSTRING(driver.last_name FROM 1 FOR 1)) AS "Driver",
        COUNT(ride.id_ride) AS "Count"
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
    """

    print("\nExecuting Raw SQL Report query...")
    with connection.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()

    # Format and print the report table
    print(f"\n{'Month':<12} | {'Driver':<20} | {'Count of Trips > 1 hr':<22}")
    print("-" * 60)
    for row in rows:
        print(f"{row[0]:<12} | {row[1]:<20} | {row[2]:<22}")
    print()


if __name__ == "__main__":
    main()
