from django.urls import path
from .views import create_booking, booking_list, booking_update_status, schedule_meeting, booking_success,complete_meeting,schedule_meeting,start_meeting

urlpatterns = [
    path('create/<int:skill_id>/<int:provider_id>/', create_booking, name='create_booking'),
    path('', booking_list, name='booking_list'),
    path('<int:booking_id>/update/<str:action>/', booking_update_status, name='booking_update_status'),
    path('<int:booking_id>/schedule/', schedule_meeting, name='schedule_meeting'),
    path('success/', booking_success, name='booking_success'),
    path('<int:booking_id>/complete/', complete_meeting, name='complete_meeting'),
    path("booking/<int:booking_id>/schedule/", schedule_meeting, name="schedule_meeting"),
    path('meetings/start/<int:booking_id>/', start_meeting, name='start_meeting'),
]
