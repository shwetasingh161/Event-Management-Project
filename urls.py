from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="home"),
    path("events/<int:pk>/", views.EventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/register/", views.register_view, name="event_register"),
    path("register/success/", views.register_success, name="register_success"),
    path("admin/events/<int:pk>/registrations/", views.admin_event_registrations, name="admin_event_registrations"),
    path("admin/registrations/<int:pk>/confirm/", views.admin_confirm_registration, name="admin_confirm_registration"),
    path("admin/registrations/<int:pk>/cancel/", views.admin_cancel_registration, name="admin_cancel_registration"),
    path("admin/events/<int:pk>/export_csv/", views.export_event_csv, name="export_event_csv"),
]
