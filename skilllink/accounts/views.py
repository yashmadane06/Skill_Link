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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from mettings.models import Booking

# ---------------- AUTH ----------------
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


@csrf_protect
def register_page(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if User.objects.filter(username=email).exists():
            messages.warning(request, 'Email is already taken.')
            return HttpResponseRedirect(request.path_info)

        user_obj = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=email,
            password=password
        )
        messages.success(request, 'Registration successful')
        return redirect('dashboard')
    return render(request, 'register.html')

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
        skill_name = request.POST.get("skill_name").strip()
        experience_level = request.POST.get("experience_level")
        personal_description = request.POST.get("personal_description", "")

        if skill_name:
            skill_obj, created = Skill.objects.get_or_create(name=skill_name)
            # Link to user's profile
            ProfileSkill.objects.create(
                profile=profile,
                skill=skill_obj,
                experience_level=experience_level,
                personal_description=personal_description
            )
            messages.success(request, f"Skill '{skill_name}' added successfully.")
        else:
            messages.error(request, "Please enter a skill name.")

        return redirect("profile_edit")

    return redirect("@login_required")
def add_skill(request):
    profile = request.user.profile

    if request.method == "POST":
        skill_name = request.POST.get("skill_name").strip()
        experience_level = request.POST.get("experience_level")
        personal_description = request.POST.get("personal_description", "")

        if skill_name:
            skill_obj, created = Skill.objects.get_or_create(name=skill_name)
            # Link to user's profile
            ProfileSkill.objects.create(
                profile=profile,
                skill=skill_obj,
                experience_level=experience_level,
                personal_description=personal_description
            )
            messages.success(request, f"Skill '{skill_name}' added successfully.")
        else:
            messages.error(request, "Please enter a skill name.")

        return redirect("profile_edit")
    messages.success(request, "skill aded succesfully")
    return redirect("profile_edit")

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
    skill.delete()
    messages.success(request, f"Skill '{skill.skill_name}' deleted.")
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

