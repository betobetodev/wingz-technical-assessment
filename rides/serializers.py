from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from rides.models import Ride, RideEvent, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id_user",
            "username",
            "role",
            "first_name",
            "last_name",
            "email",
            "phone_number",
        ]


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ["id_ride_event", "id_ride", "description", "created_at"]


class RideSerializer(serializers.ModelSerializer):
    id_rider = UserSerializer(read_only=True)
    id_driver = UserSerializer(read_only=True)
    ride_events = RideEventSerializer(many=True, read_only=True)
    todays_ride_events = serializers.SerializerMethodField()

    class Meta:
        model = Ride
        fields = [
            "id_ride",
            "status",
            "id_rider",
            "id_driver",
            "pickup_latitude",
            "pickup_longitude",
            "dropoff_latitude",
            "dropoff_longitude",
            "pickup_time",
            "ride_events",
            "todays_ride_events",
        ]

    def get_todays_ride_events(self, obj):
        # Filter events created within the last 24 hours.
        # Optimization: Use in-memory filtering from prefetched cache (obj.ride_events.all())
        # to avoid triggering a SQL query for each row (N+1 query problem).
        now = timezone.now()
        time_threshold = now - timedelta(hours=24)
        events = obj.ride_events.all()
        todays_events = [e for e in events if e.created_at >= time_threshold]
        return RideEventSerializer(todays_events, many=True).data
