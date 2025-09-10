from django.contrib import admin
from .models import Skill

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "description",
        # "created_at",  <-- remove this if your Skill model has no created_at
    )
    search_fields = ("name", "description")
    ordering = ("name",)
