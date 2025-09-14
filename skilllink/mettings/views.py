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
from django.http import Http404

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

    # Pick a ProfileSkill safely (if multiple exist choose first; you can refine selection later)
    profile_skill_qs = ProfileSkill.objects.filter(profile=provider, skill=skill)
    if not profile_skill_qs.exists():
        messages.error(request, "This provider does not offer the selected skill.")
        return redirect('index')
    profile_skill = profile_skill_qs.first()
    tokens_to_deduct = profile_skill.token_cost

    # Prevent duplicate active bookings (idempotency)
    existing = Booking.objects.filter(
        requester=requester,
        provider=provider,
        skill=skill,
        status__in=['pending', 'accepted', 'scheduled']
    ).first()
    if existing:
        messages.info(request, "You already have a booking request for this skill. Check your bookings.")
        return redirect('booking_list')

    # Atomic block: lock requester row, re-check balance, deduct once, create booking
    try:
        with transaction.atomic():
            # lock the requester row to avoid race conditions
            req_locked = Profile.objects.select_for_update().get(pk=requester.pk)

            # Replace `tokens` with your Profile's token field name if different
            available = getattr(req_locked, 'tokens', None)
            if available is None:
                # If you have a helper method (deduct_tokens), use it instead below
                messages.error(request, "Token balance not found on profile model.")
                return redirect('index')

            if available < tokens_to_deduct:
                messages.error(request, f"You need {tokens_to_deduct} tokens to book this skill.")
                return redirect('index')

            # Deduct tokens using atomic DB update (F expression)
            Profile.objects.filter(pk=req_locked.pk).update(tokens=F('tokens') - tokens_to_deduct)

            # Create booking and mark tokens_deducted True so refunds won't double-refund
            booking = Booking.objects.create(
                requester=req_locked,
                provider=provider,
                skill=skill,
                tokens_spent=tokens_to_deduct,
                tokens_deducted=True,
            )

            # Create transaction log
            Transaction.objects.create(
                user=req_locked,
                amount=tokens_to_deduct,
                transaction_type='spent',
                description=f"Booking for {skill.name}"
            )

    except Exception as e:
        # safe fallback; don't expose raw error to user
        messages.error(request, "Failed to create booking. Please try again.")
        # optional: log.exception(e)
        return redirect('index')

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
        proposed_time = request.POST.get("proposed_time")

        # Save history for multiple proposals
        BookingHistory.objects.create(
            booking=booking,
            proposer=request.user.profile,
            proposed_time=proposed_time
        )

        # Update booking with latest selected time
        booking.status = "scheduled"
        booking.proposed_time = proposed_time

        # Create Zoom meeting
        zoom_response = create_zoom_meeting(
            topic=f"{booking.skill.name} with {booking.provider.user.username}",
            start_time=proposed_time
        )
        join_url = zoom_response.get("join_url")
        if join_url:
            booking.meeting_link = join_url
        booking.save()

        messages.success(request, "Meeting scheduled & Zoom link created.")
        return redirect("booking_list")

    # Show all proposed times for this booking
    history = BookingHistory.objects.filter(booking=booking).order_by('proposed_time')
    return render(request, "schedule_meeting.html", {"booking": booking, "history": history})





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
    booking = get_object_or_404(Booking, id=booking_id)

    # Restrict join 5 minutes before start
    if booking.proposed_time - timedelta(minutes=5) > timezone.now():
        messages.warning(request, "You can join 5 minutes before the meeting starts.")
        return redirect("booking_list")

    if booking.meeting_link:
        if not booking.meeting_started:
            booking.meeting_started = True
            booking.meeting_started_at = timezone.now()
            booking.save()
        return redirect(booking.meeting_link)
    else:
        messages.error(request, "Meeting link not found.")
        return redirect("booking_list")

