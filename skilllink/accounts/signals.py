# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_profile(sender, instance, created, **kwargs):
    """
    Create a Profile when a new User is created.
    If the profile exists, do nothing (or save safely).
    This function is idempotent and safe to call repeatedly.
    """
    if created:
        # create profile with defaults (won't fail if profile_pic is nullable)
        Profile.objects.create(user=instance)
    else:
        # Only save profile if it exists
        try:
            profile = instance.profile
        except Profile.DoesNotExist:
            # create one if missing (covers edge cases)
            Profile.objects.create(user=instance)
        else:
            # don't force-save fields that might cause DB constraints,
            # but keep it in case you rely on post-save hooks in Profile
            profile.save()
