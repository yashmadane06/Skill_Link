from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import uuid
from ...models import Booking
from django.urls import reverse

class Command(BaseCommand):
    help = "Update meetings: generate links and auto-complete"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # Generate meeting links 5 min before start
        for booking in Booking.objects.filter(status='scheduled', meeting_link__isnull=True):
            if booking.proposed_time:  # ✅ skip None
                if now >= booking.proposed_time - timedelta(minutes=5):
                    token = uuid.uuid4().hex
                    booking.meeting_link = reverse('video_call', args=[booking.id, token])
                    booking.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Generated link for booking {booking.id}"
                    ))

        # Complete meetings 1 hour after start
        for booking in Booking.objects.filter(status='scheduled', tokens_released=False):
            if booking.proposed_time:  # ✅ skip None
                if now >= booking.proposed_time + timedelta(hours=1):
                    booking.status = 'completed'
                    booking.tokens_released = True
                    booking.provider.add_tokens(booking.tokens_spent // 2)
                    booking.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"Completed booking {booking.id} and released tokens"
                    ))
