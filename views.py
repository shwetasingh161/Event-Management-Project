from django.views import generic
from .models import Event, Registration
from django.shortcuts import get_object_or_404, redirect, render
from .forms import RegistrationForm
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
import csv
from django.db import transaction

class EventListView(generic.ListView):
    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 20

    def get_queryset(self):
        qs = Event.objects.filter(is_published=True)
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(title__icontains=q)
        return qs.order_by("starts_at")

class EventDetailView(generic.DetailView):
    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

def register_success(request):
    return render(request, "events/register_success.html")

def register_view(request, pk):
    event = get_object_or_404(Event, pk=pk, is_published=True)
    if request.method == "POST":
        form = RegistrationForm(request.POST, event=event)
        if form.is_valid():
            try:
                with transaction.atomic():
                    ev_locked = Event.objects.select_for_update().get(pk=event.pk)
                    confirmed = ev_locked.registrations.filter(status=Registration.REGISTERED).count()
                    if confirmed >= ev_locked.capacity:
                        status = Registration.WAITLISTED
                    else:
                        status = Registration.REGISTERED
                    reg = form.save(commit=False)
                    reg.event = ev_locked
                    reg.status = status
                    reg.save()
                if status == Registration.REGISTERED:
                    messages.success(request, "Registration confirmed. (Demo — no email sent.)")
                else:
                    messages.info(request, "Event is full — you have been added to the waitlist.")
                return redirect(reverse("events:register_success"))
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
    else:
        form = RegistrationForm(event=event)
    return render(request, "events/register_form.html", {"form": form, "event": event})

def staff_required(view_func):
    decorator = user_passes_test(lambda u: u.is_active and u.is_staff, login_url="/admin/login/")
    return decorator(view_func)

@staff_required
def admin_event_registrations(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    regs = ev.registrations.all().order_by("created_at")
    return render(request, "events/admin_registrations.html", {"event": ev, "registrations": regs})

@staff_required
def export_event_csv(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    regs = ev.registrations.all()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="registrations_{ev.id}.csv"'
    writer = csv.writer(response)
    writer.writerow(["id","name","email","phone","status","created_at"])
    for r in regs:
        writer.writerow([r.id, r.name, r.email, r.phone or "", r.status, r.created_at.isoformat()])
    return response

@staff_required
def admin_confirm_registration(request, pk):
    reg = get_object_or_404(Registration, pk=pk)
    ev = reg.event
    if ev.confirmed_count >= ev.capacity:
        messages.error(request, "Event is full; cannot confirm.")
        return redirect(reverse("events:admin_event_registrations", args=[ev.pk]))
    reg.status = Registration.REGISTERED
    reg.save()
    messages.success(request, f"{reg.name} confirmed.")
    return redirect(reverse("events:admin_event_registrations", args=[ev.pk]))

@staff_required
def admin_cancel_registration(request, pk):
    reg = get_object_or_404(Registration, pk=pk)
    ev = reg.event
    reg.status = Registration.CANCELLED
    reg.save()
    # promote earliest waitlisted if any
    next_wait = ev.registrations.filter(status=Registration.WAITLISTED).order_by("created_at").first()
    if next_wait and ev.confirmed_count < ev.capacity:
        next_wait.status = Registration.REGISTERED
        next_wait.save()
        messages.success(request, f"Promoted {next_wait.name} from waitlist to registered.")
    messages.success(request, f"Cancelled {reg.name}.")
    return redirect(reverse("events:admin_event_registrations", args=[ev.pk]))
