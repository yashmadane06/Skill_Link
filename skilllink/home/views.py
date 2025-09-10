from skills.models import Skill, ProfileSkill
from django.shortcuts import render

def index(request):
    skills = Skill.objects.all()
    skill_list = []

    for skill in skills:
        providers = ProfileSkill.objects.filter(skill=skill)
        skill_list.append({
            "skill": skill,
            "providers": providers
        })

    return render(request, "index.html", {"skills": skill_list})