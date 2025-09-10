from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "bio",
        "location",
        # "tokens",  <-- remove this or replace with a property
    )
    search_fields = ("user__username", "bio")
    ordering = ("user__username",)
