from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings

from django.contrib.auth.models import User
from .models import Profile, Transaction
from .forms import ProfileForm, ProfileSkillForm
from skills.models import Skill, ProfileSkill
import razorpay

from mettings.models import Booking

from django.shortcuts import render, redirect

from django.contrib import messages
from django.core.mail import send_mail
from .models import EmailOTP
import random
# ---------------- AUTH ----------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        user_id = request.session.get('register_user_id')
        if not user_id:
            return JsonResponse({'success': False})

        user = User.objects.get(id=user_id)
        otp_obj = EmailOTP.objects.get(user=user)
        otp = otp_obj.generate_otp()  # regenerate OTP

        send_mail(
            'SkillLink Registration OTP - Resend',
            f'Your new OTP is: {otp}',
            'your_email@gmail.com',
            [user.email],
            fail_silently=False
        )

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@csrf_protect
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # Create profile if it doesn't exist
            Profile.objects.get_or_create(user=user)

            return redirect('dashboard')
        messages.error(request, "Invalid credentials")
    return render(request, 'login.html')


# Registration Page


def register_page(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered ❌")
            return redirect("register")

        # create user (inactive/verified=False initially)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # create profile
        Profile.objects.create(user=user, verified=False)

        # generate otp
        otp_obj, _ = EmailOTP.objects.get_or_create(user=user)
        otp = otp_obj.generate_otp()

        # send mail
        send_mail(
            subject="SkillLink Registration OTP",
            message=f"Your OTP for SkillLink registration is: {otp}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        # save user id in session for verification later
        request.session["pending_user_id"] = user.id
        messages.info(request, "We sent an OTP to your email 📧")
        return redirect("verify_otp")

    return render(request, "register.html")



def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        user_id = request.session.get("pending_user_id")

        if not user_id:
            messages.error(request, "Session expired, please register again ❌")
            return redirect("register")

        user = User.objects.get(id=user_id)
        otp_obj = EmailOTP.objects.get(user=user)

        if otp_obj.otp == entered_otp:
            # mark profile as verified
            profile = Profile.objects.get(user=user)
            profile.verified = True
            profile.save()

            messages.success(request, "Registration successful 🎉 You can now login")
            return redirect("login")
        else:
            messages.error(request, "Invalid OTP ❌")

    return render(request, "verify_otp.html")






@csrf_exempt
def logout_view(request):
    logout(request)
    return redirect('dashboard')


# ---------------- PROFILE ----------------
@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    user_skills = ProfileSkill.objects.filter(profile=profile)
    return render(request, 'profile.html', {'profile': profile, 'user_skills': user_skills})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProfileForm, ProfileSkillForm
from .models import Profile
from skills.models import ProfileSkill

@login_required
def profile_edit(request):
    profile = request.user.profile
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile_edit")
    else:
        profile_form = ProfileForm(instance=profile)

    skills = profile.skills.all()
    return render(request, "profile_edit.html", {
        "profile_form": profile_form,
        "skills": skills,
    })

@login_required
def add_skill(request):
    profile = request.user.profile

    if request.method == "POST":
        # Get data from form
        skill_name = request.POST.get("skill_name", "").strip()
        experience_level = request.POST.get("experience_level")
        learning_status = request.POST.get("learning_status")
        personal_description = request.POST.get("personal_description", "")
        token_cost = request.POST.get("token_cost", 0)
        available_for_teaching = request.POST.get("available_for_teaching") == "on"
        certificate_url = request.POST.get("certificate_url", "")
        skill_icon = request.FILES.get("skill_icon")

        if skill_name:
            # Create skill if not exists
            skill_obj, created = Skill.objects.get_or_create(name=skill_name)
            
            # Update skill icon if uploaded
            if skill_icon:
                skill_obj.skill_icon = skill_icon
                skill_obj.save()

            # Link skill to profile
            ProfileSkill.objects.create(
                profile=profile,
                skill=skill_obj,
                experience_level=experience_level,
                learning_status=learning_status,
                personal_description=personal_description,
                token_cost=token_cost,
                available_for_teaching=available_for_teaching,
                certificate_url=certificate_url,
            )
            messages.success(request, f"Skill '{skill_name}' added successfully.")
            return redirect("profile_edit")
        else:
            messages.error(request, "Please enter a skill name.")

    # On GET, show the form
    return render(request, "skill_add.html")

@login_required
def edit_profile(request):
    profile = request.user.profile
    skills = ProfileSkill.objects.filter(profile=profile)

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("edit_profile")
    else:
        profile_form = ProfileForm(instance=profile)

    context = {
        "profile_form": profile_form,
        "skills": skills,
    }
    return render(request, "accounts/edit_profile.html", context)


@login_required
def edit_skill(request, pk):
    profile = request.user.profile
    skill_instance = get_object_or_404(ProfileSkill, pk=pk, profile=profile)

    if request.method == "POST":
        form = ProfileSkillForm(request.POST, instance=skill_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Skill '{skill_instance.skill.name}' updated successfully.")
            return redirect("edit_profile")
    else:
        form = ProfileSkillForm(instance=skill_instance)

    return render(request, "skill_edit.html", {
        "form": form,
        "skill_instance": skill_instance,
    })



@login_required
def delete_skill(request, pk):
    skill = get_object_or_404(ProfileSkill, pk=pk, profile=request.user.profile)
    skill_name = skill.skill.name  # save name before deleting
    skill.delete()
    messages.success(request, f"Skill '{skill_name}' deleted.")

    # Redirect: since skill is deleted, redirect to profile_edit
    return redirect("profile_edit")



# ---------------- TOKENS ----------------

@login_required
def add_tokens_view(request):
    if request.method == "POST":
        amount = int(request.POST.get("amount", 0))
        profile = request.user.profile
        profile.add_tokens(amount)
        messages.success(request, f"{amount} tokens added successfully!")
        return redirect('dashboard')


@login_required
def token_balance(request):
    profile = request.user.profile
    token_history = Transaction.objects.filter(user=profile).order_by("-timestamp")[:10]  # latest 10

    return render(request, "token_balance.html", {
        "profile": profile,
        "token_history": token_history,
    })


@login_required
def spend_tokens(request):
    if request.method == "POST":
        amount = int(request.POST.get("amount"))
        profile = request.user.profile
        if profile.deduct_tokens(amount):
            Transaction.objects.create(user=profile, amount=amount, transaction_type='spent', description="Spent tokens")
            messages.success(request, f"{amount} tokens spent successfully!")
        else:
            messages.error(request, "Insufficient tokens.")
        return redirect('token_balance')
    return render(request, "spend_tokens.html")

@login_required
def payment_success(request):
    tokens = request.session.get('token_amount')
    order_id = request.session.get('payment_order_id')

    if not tokens or not order_id:
        messages.error(request, "Payment session expired or invalid.")
        return redirect('token_balance')


    profile = request.user.profile
    profile.add_tokens(tokens, description="Purchased tokens via Razorpay")


    request.session.pop('token_amount', None)
    request.session.pop('payment_order_id', None)

    messages.success(request, f"{tokens} tokens added to your account!")
    return redirect('token_balance')






@login_required
def dashboard(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    # Provider bookings
    provider_bookings = Booking.objects.filter(provider=profile).order_by('-requested_at')
    incoming_requests = provider_bookings.filter(status='pending')
    accepted_bookings_provider = provider_bookings.filter(status__in=['accepted', 'scheduled'])
    past_bookings_provider = provider_bookings.filter(status__in=['completed', 'rejected', 'cancelled'])

    # Requester bookings
    requester_bookings = Booking.objects.filter(requester=profile).order_by('-requested_at')
    pending_bookings_requester = requester_bookings.filter(status='pending')
    accepted_bookings_requester = requester_bookings.filter(status__in=['accepted', 'scheduled'])
    past_bookings_requester = requester_bookings.filter(status__in=['completed', 'rejected', 'cancelled'])

    # Skills
    user_skills = ProfileSkill.objects.filter(profile=profile)

    context = {
        "profile": profile,
        "user_skills": user_skills,
        "incoming_requests": incoming_requests,
        "accepted_bookings_provider": accepted_bookings_provider,
        "past_bookings_provider": past_bookings_provider,
        "pending_bookings_requester": pending_bookings_requester,
        "accepted_bookings_requester": accepted_bookings_requester,
        "past_bookings_requester": past_bookings_requester,
    }
    return render(request, "dashboard.html", context)

