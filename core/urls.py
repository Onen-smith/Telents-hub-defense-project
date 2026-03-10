from django.contrib import admin
from django.urls import path, include # Import include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Social Login (Google/GitHub)
    path('accounts/', include('allauth.urls')),

    # 2. STANDARD PASSWORD RESET (ADD THIS MISSING LINE)
    # This activates the 'password_reset/' URLs causing your 404 error
    path('accounts/', include('django.contrib.auth.urls')), 

    # 3. Your App URLs
    path('', include('talents.urls')), 
]

# This part is required to serve images during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)