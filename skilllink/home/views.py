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
        {"name": "Alice", "text": "SkillLink helped me learn Python fast!","profile_pic":"https://res.cloudinary.com/dctwxqpeo/image/upload/v1757868228/default_ehmhxs.png"},
        {"name": "Bob", "text": "Amazing platform for peer-to-peer skill sharing.","profile_pic":"https://res.cloudinary.com/dctwxqpeo/image/upload/v1757868228/default_ehmhxs.png"},
        {"name": "Charlie", "text": "Loved connecting with tutors here.","profile_pic":"https://res.cloudinary.com/dctwxqpeo/image/upload/v1757868228/default_ehmhxs.png"},
    ]

    # Manual team info
    team = [
        {"name": "Faizan Mulani", "role": "Project Manager", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg",
        "social": {
            "instagram": "https://instagram.com/faizan.m_75",
        }},
        {"name": "Yash Madane", "role": "Backend Developer", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg",
        "social": {
            "instagram": "https://instagram.com/yash20_06",
            "linkedin": "https://linkedin.com/in/yash-madane",
            "github": "https://github.com/yashmadane06"
        }},
        {"name": "Mustkim Maniyar", "role": "Frontend Developer", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg",
        "social": {
            "instagram": "https://instagram.com/_mustkim_maniyar_585",
        }},
        {"name": "Rushabh Patekar", "role": "UI/UX Designerr", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg",
        "social": {
            "instagram": "https://instagram.com/rushabh_patekar_",
        }},
        {"name": "Dipak Supekar", "role": "QA & Testing", "image": "https://wallpapers-clan.com/wp-content/uploads/2023/06/cool-pfp-02.jpg",
        "social": {
            "instagram": "https://instagram.com/dipaksupekar_09",
        }},
    ]

    return render(request, 'index.html', {
        'skills': skills,
        'top_tutors': top_tutors,
        'reviews': reviews,
        'team': team,
    })
