# forms.py
from django import forms
from .models import Profile
from skills.models import ProfileSkill, Skill


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_pic', 'location']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ProfileSkillForm(forms.ModelForm):
    new_skill_name = forms.CharField(max_length=100, required=False, label="Add New Skill")

    class Meta:
        model = ProfileSkill
        fields = [
            'skill',
            'experience_level',
            'learning_status',
            'personal_description',
            'available_for_teaching',
            'token_cost',
        ]

    def save(self, commit=True):
        skill_instance = self.cleaned_data.get('skill')
        new_skill_name = self.cleaned_data.get('new_skill_name')

        if new_skill_name:
            # Create new Skill if not exists
            skill_instance, created = Skill.objects.get_or_create(name=new_skill_name)

        self.instance.skill = skill_instance
        return super().save(commit=commit)
