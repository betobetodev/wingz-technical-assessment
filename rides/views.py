from django.db.models import F
from rest_framework import permissions, viewsets

from rides.models import Ride
from rides.serializers import RideSerializer


class IsAdminRole(permissions.BasePermission):
    """
    Permission class that only allows users with role == 'admin' to access endpoints.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "role", None) == "admin"


class RideViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Ride instances.
    """

    serializer_class = RideSerializer
    permission_classes = [IsAdminRole]

    def get_queryset(self):
        # Base query using select_related for rider/driver and prefetch_related for events
        queryset = Ride.objects.select_related("id_rider", "id_driver").prefetch_related(
            "ride_events"
        )

        # Filtering by status
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)

        # Filtering by rider email
        rider_email = self.request.query_params.get("rider_email")
        if rider_email:
            queryset = queryset.filter(id_rider__email=rider_email)

        # Retrieve sorting parameters
        ordering = self.request.query_params.get("ordering")
        near_lat = self.request.query_params.get("near_lat")
        near_lng = self.request.query_params.get("near_lng")

        # Handle distance-based sorting if near_lat and near_lng are provided
        if near_lat is not None and near_lng is not None:
            try:
                lat = float(near_lat)
                lng = float(near_lng)
                # Euclidean distance calculation (compatible with PostgreSQL and SQLite)
                queryset = queryset.annotate(
                    distance=(F("pickup_latitude") - lat) * (F("pickup_latitude") - lat)
                    + (F("pickup_longitude") - lng) * (F("pickup_longitude") - lng)
                )
                if ordering == "-distance":
                    queryset = queryset.order_by("-distance")
                else:
                    queryset = queryset.order_by("distance")
            except ValueError:
                pass
        # Handle standard ordering by pickup_time
        elif ordering in ("pickup_time", "-pickup_time"):
            queryset = queryset.order_by(ordering)

        return queryset
