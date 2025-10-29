from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter  # if you still use router for other endpoints, optional

urlpatterns = [
    path("status/", views.top_level_status, name="status"),
    path("countries/refresh/", views.refresh_countries, name="countries-refresh"),
    path("countries/image/", views.countries_image, name="countries-image"),
    path("countries/", views.list_countries, name="countries-list"),
    path("countries/<str:name>/", views.get_country, name="countries-detail"),
    path("countries/<str:name>", views.delete_country, name="countries-delete"),
]
