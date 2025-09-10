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

    tokens_to_deduct = 10  # total tokens for this booking

    if not requester.deduct_tokens(tokens_to_deduct):
        messages.error(request, "Insufficient tokens to book this skill.")
        return redirect('index')


    # Create booking with deduction flag
    booking = Booking.objects.create(
        requester=requester,
        provider=provider,
        skill=skill,
        tokens_spent=tokens_to_deduct,
        tokens_deducted=True  # mark that tokens have been taken from requester
    )

    Transaction.objects.create(
    user=request.user.profile,  # NOT request.user
    amount=10,
    transaction_type='spent',
    description="Booking deduction" 
    )


    messages.success(request, "Booking request sent. 10 tokens deducted from your account.")
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
        # Refund tokens to requester
        booking.requester.add_tokens(booking.tokens_spent)
        Transaction.objects.create(
            user=booking.requester,
            amount=booking.tokens_spent,
            transaction_type='earned',
            description=f"Refund for rejected booking {booking.skill.name}"
        )
        messages.info(request, "Booking rejected. Tokens refunded to requester.")

    return redirect('booking_list')





@login_required
def schedule_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user.profile)

    if request.method == "POST":
        if not booking.tokens_scheduled_given:
            booking.proposed_time = request.POST.get("proposed_time")
            booking.status = "scheduled"
            booking.tokens_scheduled_given = True

            # 🔹 Create Zoom meeting
            from skilllink.zoom_utils import create_zoom_meeting
            zoom_response = create_zoom_meeting(
                topic=f"{booking.skill.name} with {booking.provider.user.username}"
            )
            join_url = zoom_response.get("join_url")
            start_url = zoom_response.get("start_url")

            if join_url:
                booking.meeting_link = join_url
            else:
                messages.error(request, "Failed to create Zoom meeting. Try again.")
                return redirect("booking_list")

            booking.save()

            # 🔹 Give 3 tokens to provider (old logic stays same)
            booking.provider.add_tokens(3)
            Transaction.objects.create(
                user=booking.provider,
                amount=3,
                transaction_type='earned',
                description=f"3 tokens for scheduling/attending meeting {booking.skill.name}"
            )

            messages.success(request, "Meeting scheduled & Zoom link created. Provider received 3 tokens.")
        else:
            messages.info(request, "Tokens already given for scheduling this meeting.")

        return redirect('booking_list')  # always return an HttpResponse

    # If GET or any other method, render the form
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
        return redirect('dashboard')

    if not booking.tokens_released:
        commission = int(booking.tokens_spent * 0.3)
        provider_total = booking.tokens_spent - commission
        remaining_tokens = provider_total - (provider_total // 2)  # remaining half

        booking.provider.add_tokens(remaining_tokens)
        Transaction.objects.create(
            user=booking.provider,
            amount=remaining_tokens,
            transaction_type='earned',
            description=f"Remaining tokens (after 30% commission) for booking {booking.skill.name}"
        )

        booking.tokens_released = True
        booking.status = "completed"
        booking.save()
        messages.success(request, f"Meeting completed. Provider received remaining {remaining_tokens} tokens.")

    else:
        messages.info(request, "Tokens already fully released for this meeting.")

    return redirect('dashboard')


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
