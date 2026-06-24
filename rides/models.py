from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id_user = models.AutoField(primary_key=True)
    role = models.CharField(max_length=50, default="rider")
    phone_number = models.CharField(max_length=30, blank=True, null=True)

    # Use email as the main identifier or keep standard username.
    # To avoid username conflicts, we can allow username to be optional or auto-generated,
    # but keeping it standard is easiest. We'll support both.
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Ride(models.Model):
    id_ride = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50, default="pickup")
    id_rider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="rider_rides",
    )
    id_driver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="driver_rides",
        null=True,
        blank=True,
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()

    def __str__(self):
        return f"Ride {self.id_ride} - {self.status}"


class RideEvent(models.Model):
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name="ride_events",
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"Event {self.id_ride_event} for Ride {self.id_ride.id_ride}: {self.description}"
