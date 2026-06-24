from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


def seed_data(apps, schema_editor):
    import sys

    from django.conf import settings

    # Skip seeding during automated test suite runs to preserve clean test state
    if (
        "test" in sys.argv
        or any("pytest" in arg for arg in sys.argv)
        or settings.DATABASES["default"]["NAME"].startswith("test_")
    ):
        return

    User = apps.get_model("rides", "User")
    Ride = apps.get_model("rides", "Ride")
    RideEvent = apps.get_model("rides", "RideEvent")

    # Create users with hashed passwords
    admin = User.objects.create(
        username="admin",
        first_name="System",
        last_name="Administrator",
        email="admin@example.com",
        password=make_password("adminpassword"),
        role="admin",
        is_staff=True,
        is_superuser=True,
    )
    rider = User.objects.create(
        username="rider1",
        first_name="Jane",
        last_name="Rider",
        email="rider1@example.com",
        password=make_password("riderpassword"),
        role="rider",
    )

    # Create the report drivers
    chris = User.objects.create(
        username="chris",
        first_name="Chris",
        last_name="H",
        email="chris@example.com",
        password=make_password("driverpassword"),
        role="driver",
    )
    howard = User.objects.create(
        username="howard",
        first_name="Howard",
        last_name="Y",
        email="howard@example.com",
        password=make_password("driverpassword"),
        role="driver",
    )
    randy = User.objects.create(
        username="randy",
        first_name="Randy",
        last_name="W",
        email="randy@example.com",
        password=make_password("driverpassword"),
        role="driver",
    )

    # Helper function to generate trips matching criteria (duration > 1 hour)
    def seed_trips(driver, month_str, count):
        import datetime

        year, month = map(int, month_str.split("-"))

        for i in range(count):
            # Stagger the days and hours to keep times realistic and non-colliding
            day = (i % 28) + 1
            hour = i % 24
            pickup_naive = datetime.datetime(year, month, day, hour, 0, 0)
            pickup_time = timezone.make_aware(pickup_naive, timezone.get_current_timezone())
            # Duration: 1 hour 30 mins (which is > 1 hour)
            dropoff_time = pickup_time + timedelta(hours=1, minutes=30)

            ride = Ride.objects.create(
                status="dropoff",
                id_rider=rider,
                id_driver=driver,
                pickup_latitude=37.7749,
                pickup_longitude=-122.4194,
                dropoff_latitude=37.7849,
                dropoff_longitude=-122.4094,
                pickup_time=pickup_time,
            )

            # Pickup event matching the query description
            RideEvent.objects.create(
                id_ride=ride,
                description="Status changed to pickup",
                created_at=pickup_time,
            )
            # Dropoff event matching the query description
            RideEvent.objects.create(
                id_ride=ride,
                description="Status changed to dropoff",
                created_at=dropoff_time,
            )

    # Populate matching the sample report exactly:
    # 2024-01: Chris H (4), Howard Y (5), Randy W (2)
    seed_trips(chris, "2024-01", 4)
    seed_trips(howard, "2024-01", 5)
    seed_trips(randy, "2024-01", 2)

    # 2024-02: Chris H (7), Howard Y (5)
    seed_trips(chris, "2024-02", 7)
    seed_trips(howard, "2024-02", 5)

    # 2024-03: Chris H (2), Howard Y (2), Randy W (11)
    seed_trips(chris, "2024-03", 2)
    seed_trips(howard, "2024-03", 2)
    seed_trips(randy, "2024-03", 11)

    # 2024-04: Howard Y (7), Randy W (3)
    seed_trips(howard, "2024-04", 7)
    seed_trips(randy, "2024-04", 3)


class Migration(migrations.Migration):
    dependencies = [
        ("rides", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_data),
    ]
