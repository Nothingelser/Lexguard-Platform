from django.urls import path

from . import views

app_name = "suspects"

urlpatterns = [
    path("search/", views.suspect_search, name="search"),
    path("new/", views.suspect_create, name="create"),
    path("<int:pk>/", views.suspect_profile, name="profile"),
]
