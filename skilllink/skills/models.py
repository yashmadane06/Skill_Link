from django.db import models
from accounts.models import Profile

# ---------------- SKILL ----------------
class Skill(models.Model):
    name = models.CharField(max_length=30, unique=True)
    category = models.CharField(max_length=30, blank=True, default='')

    experience_choices = [
        (0, 'Just started'),
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Proficient'),
        (4, 'Advanced'),
        (5, 'Expert / Mastery'),
    ]

    description = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return self.name


# ---------------- PROFILE SKILL ----------------
class ProfileSkill(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    personal_description = models.TextField(blank=True)
    experience_level = models.IntegerField(choices=Skill.experience_choices, default=0)

    class Meta:
        unique_together = ('profile', 'skill')

    def __str__(self):
        return f"{self.profile.user.username} - {self.skill.name}"
