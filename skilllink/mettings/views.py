from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from skills.models import Skill
from accounts.models import Profile, Transaction
from .models import Booking, BookingHistory
from skills.models import ProfileSkill
import uuid
from django.utils import timezone
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Profile, Transaction
from skills.models import Skill, ProfileSkill
from .models import Booking
import uuid
from skilllink.zoom_utils import create_zoom_meeting

@login_required
def create_booking(request, skill_id, provider_id):
    requester = request.user.profile
    skill = get_object_or_404(Skill, id=skill_id)
    provider = get_object_or_404(Profile, id=provider_id)

    if requester == provider:
        messages.error(request, "You cannot book your own skill.")
        return redirect('index')

    # ✅ Get token cost from ProfileSkill
    profile_skill = get_object_or_404(ProfileSkill, profile=provider, skill=skill)
    tokens_to_deduct = profile_skill.token_cost

    if not requester.deduct_tokens(tokens_to_deduct):
        messages.error(request, f"You need {tokens_to_deduct} tokens to book this skill.")
        return redirect('index')

    # Create booking
    booking = Booking.objects.create(
        requester=requester,
        provider=provider,
        skill=skill,
        tokens_spent=tokens_to_deduct,
        tokens_deducted=True
    )

    # Log transaction
    Transaction.objects.create(
        user=requester,
        amount=tokens_to_deduct,
        transaction_type='spent',
        description=f"Booking for {skill.name}"
    )

    messages.success(request, f"Booking request sent. {tokens_to_deduct} tokens deducted.")
    return redirect('booking_success')




@login_required
def booking_list(request):
    profile = request.user.profile
    bookings_received = Booking.objects.filter(provider=profile).order_by('-requested_at')
    bookings_made = Booking.objects.filter(requester=profile).order_by('-requested_at')
    return render(request, "booking_list.html", {
        "bookings_received": bookings_received,
        "bookings_made": bookings_made
    })
    
    


def booking_update_status(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.provider != request.user.profile:
        messages.error(request, "You cannot modify this booking.")
        return redirect('booking_list')

    if action == "accept":
        booking.status = "accepted"
        booking.save()
        messages.success(request, "Booking accepted. Tokens will be released as meeting progresses.")

    elif action == "reject":
        booking.status = "rejected"
        booking.save()

    # Refund exactly what was deducted
        booking.requester.add_tokens(booking.tokens_spent)

        Transaction.objects.create(
            user=booking.requester,
            amount=booking.tokens_spent,
            transaction_type="refund",
            description=f"Refund for rejected booking {booking.skill.name}"
        )

        messages.info(request, f"Booking rejected. {booking.tokens_spent} tokens refunded.")
    return redirect('booking_list')





@login_required
def schedule_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user.profile)

    if request.method == "POST":
        if booking.status != "pending":
            messages.info(request, "This booking is already scheduled.")
            return redirect("booking_list")

        booking.proposed_time = request.POST.get("proposed_time")
        booking.status = "scheduled"

        # Create Zoom
        zoom_response = create_zoom_meeting(
            topic=f"{booking.skill.name} with {booking.provider.user.username}"
        )
        join_url = zoom_response.get("join_url")
        if join_url:
            booking.meeting_link = join_url
        else:
            messages.error(request, "Failed to create Zoom meeting.")
            return redirect("booking_list")

        booking.save()
        messages.success(request, "Meeting scheduled & Zoom link created.")
        return redirect("booking_list")

    return render(request, "schedule_meeting.html", {"booking": booking})




@login_required
def video_call(request, booking_id, token):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.profile not in [booking.requester, booking.provider]:
        messages.error(request, "You are not allowed to join this meeting.")
        return redirect('booking_list')

    return render(request, "video_call.html", {"booking": booking, "token": token})


@login_required
def booking_success(request):
    return render(request, "booking_success.html")






@login_required
def complete_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user.profile)

    if booking.status != "scheduled":
        messages.error(request, "Cannot complete meeting that is not scheduled.")
        return redirect("dashboard")

    # ✅ Ensure meeting started time exists
    if not booking.meeting_started_at:
        messages.error(request, "Meeting has not started yet.")
        return redirect("dashboard")

    # ✅ Check if 30 minutes passed since meeting started
    if timezone.now() < booking.meeting_started_at + timedelta(minutes=30):
        remaining_time = (booking.meeting_started_at + timedelta(minutes=30)) - timezone.now()
        minutes_left = remaining_time.seconds // 60
        messages.warning(request, f"Meeting must run at least 30 minutes. Wait {minutes_left} more minutes.")
        return redirect("dashboard")

    if not booking.tokens_released:
        commission = int(booking.tokens_spent * 0.3)
        provider_total = booking.tokens_spent - commission

        booking.provider.add_tokens(provider_total)
        Transaction.objects.create(
            user=booking.provider,
            amount=provider_total,
            transaction_type="earned",
            description=f"Payment for booking {booking.skill.name} (after commission)"
        )

        booking.tokens_released = True
        booking.status = "completed"
        booking.save()

        messages.success(request, f"Meeting completed. Provider received {provider_total} tokens after commission.")
    else:
        messages.info(request, "Tokens already released.")

    return redirect("dashboard")


@login_required
def start_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user.profile)

    if booking.meeting_link:
        booking.meeting_started = True
        booking.save()
        return redirect(booking.meeting_link)  # Redirect provider to Zoom
    else:
        messages.error(request, "Meeting link not found.")
        return redirect('booking_list')


def generate_meeting_link(booking):
    token = uuid.uuid4().hex
    return f"/meetings/video/{booking.id}/{token}/"
