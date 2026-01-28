from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Profile, Transaction
from skills.models import Skill, ProfileSkill
from .models import Booking, BookingHistory, Message
from skilllink.zoom_utils import create_zoom_meeting
import uuid
from datetime import datetime

# ------------------ CREATE BOOKING ------------------
@login_required
def create_booking(request, skill_id, provider_id):
    requester = request.user.profile
    skill = get_object_or_404(Skill, id=skill_id)
    provider = get_object_or_404(Profile, id=provider_id)

    if requester == provider:
        messages.error(request, "You cannot book your own skill.")
        return redirect('index')

    # Check if provider teaches this skill
    profile_skill = ProfileSkill.objects.filter(profile=provider, skill=skill).first()
    if not profile_skill:
        messages.error(request, "This provider does not offer this skill.")
        return redirect('index')

    tokens_needed = profile_skill.token_cost

    # Prevent duplicate pending bookings
    if Booking.objects.filter(
        requester=requester,
        provider=provider,
        skill=skill,
        status__in=['pending', 'accepted', 'scheduled']
    ).exists():
        messages.info(request, "You already have a booking request for this skill.")
        return redirect('booking_list')

    # Deduct tokens atomically
    try:
        with transaction.atomic():
            if requester.token_balance < tokens_needed:
                messages.error(request, "Insufficient tokens to book this skill.")
                return redirect('index')

            # Deduct tokens
            requester.deduct_tokens(tokens_needed, description=f"Booking for {skill.name}")

            # Create booking
            booking = Booking.objects.create(
                requester=requester,
                provider=provider,
                skill=skill,
                tokens_spent=tokens_needed,
                tokens_deducted=True,
                status='pending'
            )

        messages.success(request, f"Booking request sent. {tokens_needed} tokens deducted.")
        return redirect('booking_success')
    except Exception as e:
        messages.error(request, f"Failed to create booking: {e}")
        return redirect('index')


# ------------------ LIST BOOKINGS ------------------
@login_required
def booking_list(request):
    profile = request.user.profile
    bookings_received = Booking.objects.filter(provider=profile).order_by('-requested_at')
    bookings_made = Booking.objects.filter(requester=profile).order_by('-requested_at')
    return render(request, "booking_list.html", {
        "bookings_received": bookings_received,
        "bookings_made": bookings_made
    })


# ------------------ UPDATE BOOKING STATUS ------------------
@login_required
def booking_update_status(request, booking_id, action):
    booking = get_object_or_404(Booking, id=booking_id)
    user_profile = request.user.profile

    # Only provider or requester can update
    if user_profile not in [booking.provider, booking.requester]:
        messages.error(request, "You cannot modify this booking.")
        return redirect('booking_list')

    if action == "accept" and user_profile == booking.provider:
        booking.status = "accepted"
        booking.save()
        messages.success(request, "Booking accepted. Provider will schedule the meeting.")

    elif action == "reject" and user_profile == booking.provider:
        booking.status = "canceled"
        booking.save()
        booking.requester.add_tokens(booking.tokens_spent)
        Transaction.objects.create(
            user=booking.requester,
            amount=booking.tokens_spent,
            transaction_type="refund",
            description=f"Refund for rejected booking {booking.skill.name}"
        )
        messages.info(request, "Booking rejected. Tokens refunded.")

    elif action == "cancel" and user_profile == booking.requester:
        booking.status = "canceled"
        booking.save()
        booking.requester.add_tokens(booking.tokens_spent)
        Transaction.objects.create(
            user=booking.requester,
            amount=booking.tokens_spent,
            transaction_type="refund",
            description=f"Refund for canceled booking {booking.skill.name}"
        )
        messages.info(request, "Booking canceled. Tokens refunded.")

    else:
        messages.error(request, "Invalid action or permission.")
    return redirect('booking_list')


# ------------------ SCHEDULE MEETING ------------------
@login_required
def schedule_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user.profile)

    if request.method == "POST":
        proposed_time_str = request.POST.get("proposed_time")
        if not proposed_time_str:
            messages.error(request, "Select a valid time.")
            return redirect("schedule_meeting", booking_id=booking.id)

        try:
            proposed_time = datetime.strptime(proposed_time_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect("schedule_meeting", booking_id=booking.id)

        BookingHistory.objects.create(
            booking=booking,
            proposer=request.user.profile,
            proposed_time=proposed_time
        )

        booking.proposed_time = proposed_time
        booking.status = "scheduled"

        try:
            zoom_response = create_zoom_meeting(topic=f"{booking.skill.name} with {booking.provider.user.username}")
            booking.meeting_link = zoom_response.get("join_url")
        except Exception as e:
            messages.error(request, f"Zoom error: {e}")

        booking.save()
        messages.success(request, "Meeting scheduled & Zoom link created.")
        return redirect("booking_list")

    history = BookingHistory.objects.filter(booking=booking).order_by("proposed_time")
    return render(request, "schedule_meeting.html", {"booking": booking, "history": history})


# ------------------ START MEETING ------------------
from django.utils import timezone
@login_required
def start_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Only requester or provider can join/start
    if request.user.profile not in [booking.requester, booking.provider]:
        messages.error(request, "You are not allowed to join this meeting.")
        return redirect('booking_list')

    # Create Zoom meeting if not exists
    if not booking.meeting_link:
        try:
            zoom_response = create_zoom_meeting(
                topic=f"{booking.skill.name} with {booking.provider.user.username}",
                duration=60  # in minutes (optional)
            )
            booking.meeting_link = zoom_response.get("join_url")
            booking.meeting_started = True
            booking.meeting_started_at = timezone.now()
            booking.save()
            messages.success(request, "Zoom meeting created. You can join now.")
        except Exception as e:
            messages.error(request, f"Zoom error: {e}")
            return redirect('booking_list')

    # Mark meeting as started
    if not booking.meeting_started:
        booking.meeting_started = True
        booking.meeting_started_at = timezone.now()
        booking.save()

    return redirect(booking.meeting_link)


# ------------------ COMPLETE MEETING ------------------
@login_required
def complete_meeting(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, provider=request.user.profile)

    if booking.status != "scheduled":
        messages.error(request, "Cannot complete meeting that is not scheduled.")
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
        messages.success(request, f"Meeting completed. Provider received {provider_total} tokens.")
    else:
        messages.info(request, "Tokens already released.")

    return redirect("dashboard")
def booking_success(request):
    return render(request, "booking_success.html")

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Booking, BookingHistory

@login_required
def booking_details(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Only allow requester or provider to view
    if request.user.profile not in [booking.requester, booking.provider]:
        messages.error(request, "You are not allowed to view this booking.")
        return redirect('booking_list')

    # Fetch all proposed times
    history = BookingHistory.objects.filter(booking=booking).order_by('proposed_time')
    chat_messages = Message.objects.filter(booking=booking).order_by('timestamp')

    return render(request, 'booking_details.html', {
        'booking': booking,
        'history': history,
        'chat_messages': chat_messages,
    })

from django.http import JsonResponse

@login_required
def send_message(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.profile not in [booking.requester, booking.provider]:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            message = Message.objects.create(
                booking=booking,
                sender=request.user.profile,
                content=content
            )
            return JsonResponse({
                'status': 'success',
                'message': {
                    'sender': message.sender.user.username,
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                }
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def get_messages(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.user.profile not in [booking.requester, booking.provider]:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    messages_list = Message.objects.filter(booking=booking).order_by('timestamp')
    data = []
    for msg in messages_list:
        data.append({
            'sender': msg.sender.user.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_me': msg.sender == request.user.profile
        })
    return JsonResponse({'status': 'success', 'messages': data})
