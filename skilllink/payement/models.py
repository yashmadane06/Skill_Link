from django.db import models
from accounts.models import Profile

class Payment(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()
    payment_gateway = models.CharField(max_length=50, default='Razorpay')
    payment_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=[('pending','Pending'),('success','Success'),('failed','Failed')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.user.username} - {self.amount} via {self.payment_gateway}"
