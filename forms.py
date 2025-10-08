from django import forms
from .models import Registration, Event
from django.utils import timezone

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["name", "email", "phone"]

    def __init__(self, *args, event: Event = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if self.event:
            existing = Registration.objects.filter(event=self.event, email=email).exclude(status=Registration.CANCELLED)
            if existing.exists():
                raise forms.ValidationError("This email is already registered for the event.")
        return email

    def clean(self):
        cleaned = super().clean()
        if self.event and self.event.starts_at < timezone.now():
            raise forms.ValidationError("Cannot register for events that already started.")
        return cleaned
