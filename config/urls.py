from django.urls import include, path

urlpatterns = [
    path("api/", include("rides.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
