from django.contrib import admin
from .models import Skill, ProfileSkill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'skill_icon')
    search_fields = ('name', 'category')
    list_filter = ('category',)
    ordering = ('name',)

@admin.register(ProfileSkill)
class ProfileSkillAdmin(admin.ModelAdmin):
    list_display = ('profile', 'skill')  # remove level and experience if not in model
    search_fields = ('profile__user__username', 'skill__name')
    list_filter = ('skill',)  # only include actual fields
    ordering = ('profile', 'skill')
