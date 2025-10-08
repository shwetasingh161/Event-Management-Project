from django.test import TestCase
from django.utils import timezone
from .models import Event, Registration

class RegistrationFlowTests(TestCase):
    def setUp(self):
        now = timezone.now()
        self.ev = Event.objects.create(title="T", description="d", venue="v", starts_at=now + timezone.timedelta(days=1), capacity=2, is_published=True)

    def test_waitlist_promotion_and_duplicate(self):
        Registration.objects.create(event=self.ev, name="A", email="a@x.com", status=Registration.REGISTERED)
        Registration.objects.create(event=self.ev, name="B", email="b@x.com", status=Registration.REGISTERED)
        r3 = Registration.objects.create(event=self.ev, name="C", email="c@x.com", status=Registration.WAITLISTED)
        self.assertEqual(self.ev.registrations.filter(status=Registration.WAITLISTED).count(), 1)
        r1 = self.ev.registrations.filter(status=Registration.REGISTERED).first()
        r1.status = Registration.CANCELLED
        r1.save()
        next_wait = self.ev.registrations.filter(status=Registration.WAITLISTED).order_by("created_at").first()
        if next_wait:
            next_wait.status = Registration.REGISTERED
            next_wait.save()
        self.assertEqual(self.ev.registrations.filter(status=Registration.REGISTERED).count(), 2)

    def test_duplicate_prevention(self):
        Registration.objects.create(event=self.ev, name="A", email="dup@x.com", status=Registration.REGISTERED)
        with self.assertRaises(Exception):
            Registration.objects.create(event=self.ev, name="A2", email="dup@x.com", status=Registration.REGISTERED)
