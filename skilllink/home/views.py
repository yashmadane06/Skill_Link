from skills.models import Skill, ProfileSkill
from django.shortcuts import render

def index(request):
    # Trending skills with top 3 providers each
    skills = []
    for skill in Skill.objects.all():
        providers = ProfileSkill.objects.filter(skill=skill)[:3]  # top 3
        skills.append({'skill': skill, 'providers': providers})

    # Top tutors: order by avg rating or times_taught
    top_tutors = ProfileSkill.objects.all().order_by('-average_rating')[:7]

    # Reviews: dummy for now
    reviews = [
        {"name": "Alice", "text": "SkillLink helped me learn Python fast!"},
        {"name": "Bob", "text": "Amazing platform for peer-to-peer skill sharing."},
        {"name": "Charlie", "text": "Loved connecting with tutors here."},
    ]

    # Manual team info
    team = [
        {"name": "Yash Madane", "role": "Backend Developer", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg"},
        {"name": "Faizan Mulani", "role": "Project Manager", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg"},
        {"name": "Mustkim Maniyar", "role": "Frontend Developer", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg"},
        {"name": "Rushabh Patekar", "role": "UI/UX Designerr", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg"},
        {"name": "Dipak Supekar", "role": "QA & Testing", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.png"},
    ]

    return render(request, 'index.html', {
        'skills': skills,
        'top_tutors': top_tutors,
        'reviews': reviews,
        'team': team,
    })
