from django.contrib import admin
from .models import Event, Registration

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "venue", "starts_at", "capacity", "is_published", "created_by")
    list_filter = ("is_published",)
    search_fields = ("title", "venue", "description")
    actions = ["export_registrations_csv"]

    def export_registrations_csv(self, request, queryset):
        from django.http import HttpResponse
        import csv
        if queryset.count() != 1:
            self.message_user(request, "Select exactly one event to export registrations.")
            return
        ev = queryset.first()
        regs = ev.registrations.all()
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="registrations_{ev.id}.csv"'
        writer = csv.writer(response)
        writer.writerow(["id","name","email","phone","status","created_at"])
        for r in regs:
            writer.writerow([r.id, r.name, r.email, r.phone or "", r.status, r.created_at.isoformat()])
        return response
    export_registrations_csv.short_description = "Export registrations (CSV)"

@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "event", "status", "created_at")
    list_filter = ("status", "event")
    search_fields = ("name", "email")
