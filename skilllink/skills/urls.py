from django.urls import path
from .views import skill_list, skill_detail

urlpatterns = [
    path('', skill_list, name='skill_list'),
    path('<int:skill_id>/', skill_detail, name='skill_detail'),
]
