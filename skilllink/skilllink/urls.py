import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Apps
    path('', include('home.urls')), 
    path('accounts/', include('accounts.urls')),
    path('skills/', include('skills.urls')),
    path('meetings/', include('mettings.urls')),
    path('payment/', include('payement.urls')),
]

# Media & static files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'public/static'))
