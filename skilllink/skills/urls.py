from django.urls import path,include
from .views import skill_list, skill_detail,share_skill,skills_available

urlpatterns = [
    path('', skill_list, name='skill_list'),
    path('<int:skill_id>/', skill_detail, name='skill_detail'),
    path('share/', share_skill, name='share_skill'),

]