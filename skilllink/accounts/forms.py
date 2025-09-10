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
    # treat skill as a plain CharField, not ForeignKey
    skill_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter skill name'})
    )

    class Meta:
        model = ProfileSkill
        fields = ['experience_level', 'personal_description']  # 🚨 skill removed here
        widgets = {
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'personal_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add description'
            }),
        }
