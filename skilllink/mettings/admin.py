from django.contrib import admin
from .models import Booking, BookingHistory
from django.utils.html import format_html

# ---------------- BOOKING ADMIN ----------------
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "requester",
        "provider",
        "skill",
        "status",
        "tokens_spent",
        "tokens_scheduled_given",
        "tokens_completed_given",
        "proposed_time",
        "meeting_link",
        "updated_at",
    )
    list_filter = ("status", "tokens_scheduled_given", "tokens_completed_given")
    search_fields = (
        "requester__user__username",
        "provider__user__username",
        "skill__name",
    )
    ordering = ("-updated_at",)
    readonly_fields = ("requested_at", "updated_at")

    def meeting_link_display(self, obj):
        if obj.meeting_link:
            return format_html('<a href="{}" target="_blank">Join Zoom</a>', obj.meeting_link)
        return "No link"
    meeting_link_display.short_description = "Meeting Link"

# ---------------- BOOKING HISTORY ADMIN ----------------
@admin.register(BookingHistory)
class BookingHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "booking",
        "proposer",
        "proposed_time",
        "created_at",
    )
    search_fields = (
        "booking__id",
        "proposer__user__username",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
