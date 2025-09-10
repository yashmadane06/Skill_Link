from django.db import models
from accounts.models import Profile
from skills.models import Skill

# ---------------- BOOKING ----------------
class Booking(models.Model):
    requester = models.ForeignKey(Profile, related_name='bookings_made', on_delete=models.CASCADE)
    provider = models.ForeignKey(Profile, related_name='bookings_received', on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    meeting_link = models.URLField(null=True, blank=True)  
    host_link = models.URLField(null=True, blank=True)   
    
    status = models.CharField(max_length=10, choices=[
        ('pending','Pending'),
        ('accepted','Accepted'),
        ('rejected','Rejected'),
        ('scheduled','Scheduled'),
        ('cancelled','Cancelled'),
        ('completed','Completed')],
        default='pending'
    )

    tokens_spent = models.PositiveIntegerField(default=0)
    tokens_deducted = models.BooleanField(default=False)        # <- tokens deducted from requester
    tokens_scheduled_given = models.BooleanField(default=False) # <- 3 tokens to provider at scheduling
    tokens_completed_given = models.BooleanField(default=False) # <- 4 tokens to provider at completion

    proposed_time = models.DateTimeField(null=True, blank=True)
    meeting_link = models.URLField(null=True, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    meeting_started = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.requester.user.username} booked {self.skill.name} from {self.provider.user.username}"




# ---------------- BOOKING HISTORY ----------------
class BookingHistory(models.Model):
    booking = models.ForeignKey(Booking, related_name="history", on_delete=models.CASCADE)
    proposer = models.ForeignKey(Profile, on_delete=models.CASCADE)
    proposed_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking {self.booking.id} proposed {self.proposed_time} by {self.proposer.user.username}"
