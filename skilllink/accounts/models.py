from django.db import models
from django.contrib.auth.models import User

import random

class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.save()
        return self.otp

    def __str__(self):
        return f"{self.user.username} OTP"

# ---------------- PROFILE ----------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=100 ,blank=True, null=True)
    profile_pic = models.ImageField(upload_to="profile_pics/", default="default.png")
    location = models.CharField(max_length=100, blank=True, null=True)
    languages_spoken = models.CharField(max_length=200, blank=True, null=True)
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("expert", "Expert"),
        ],
        default="beginner"
    )
    tokens_balance = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)
    joined_on = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)
    
    def __str__(self):
        return self.user.username

    # --- Token-related calculations ---
    @property
    def total_earned(self):
        from mettings.models import Booking
        return Booking.objects.filter(provider=self, status="completed").aggregate(
            total=models.Sum("tokens_spent")
        )["total"] or 0

    @property
    def total_spent(self):
        from mettings.models import Booking
        return Booking.objects.filter(requester=self, status="completed").aggregate(
            total=models.Sum("tokens_spent")
        )["total"] or 0

    @property
    def total_purchased(self):
        from .models import Transaction
        return Transaction.objects.filter(user=self, transaction_type='purchased').aggregate(
            total=models.Sum("amount")
        )["total"] or 0


    @property
    def token_balance(self):
        totals = Transaction.objects.filter(user=self).values("transaction_type").annotate(total=models.Sum("amount"))
        earned = next((t["total"] for t in totals if t["transaction_type"] == "earned"), 0)
        spent = next((t["total"] for t in totals if t["transaction_type"] == "spent"), 0)
        purchased = next((t["total"] for t in totals if t["transaction_type"] == "purchased"), 0)

        return (purchased + earned) - spent




    def add_tokens(self, amount, description="Purchased tokens"):
        from .models import Transaction
        Transaction.objects.create(
            user=self,
            amount=amount,
            transaction_type='purchased',
            description=description
        )

    def deduct_tokens(self, amount, description="Spent tokens"):
        """Deduct tokens from the profile if balance is sufficient."""
        # Refresh profile to avoid stale balance
        self.refresh_from_db()

        if self.token_balance >= amount:
            Transaction.objects.create(
                user=self,   # Profile FK
                amount=amount,
                transaction_type="spent",
                description=description
            )
            return True
        return False




# ---------------- TRANSACTION ----------------
class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('earned', 'Earned'),
        ('spent', 'Spent'),
        ('purchased', 'Purchased'),
    ]

    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.transaction_type} {self.amount} tokens"
