from django.urls import include, path
from rest_framework.routers import DefaultRouter

from rides.views import RideViewSet

router = DefaultRouter()
router.register(r"rides", RideViewSet, basename="ride")

urlpatterns = [
    path("", include(router.urls)),
]
