from django.shortcuts import render, get_object_or_404
from .models import Skill, ProfileSkill
from accounts.models import Profile

def skill_list(request):
    skills = Skill.objects.all()
    return render(request, "skills/skill_list.html", {"skills": skills})

def skill_detail(request, skill_id):
    skill = get_object_or_404(Skill, id=skill_id)
    providers_list = []
    for profile in skill.profiles_offered.all():
        try:
            profile_skill = ProfileSkill.objects.get(profile=profile, skill=skill)
        except ProfileSkill.DoesNotExist:
            profile_skill = None
        providers_list.append({
            "profile": profile,
            "profile_skill": profile_skill
        })

    return render(request, "skills/skill_detail.html", {"skill": skill, "providers": providers_list})
