from django.contrib import admin
from django.urls import path, include # Import include
from django.conf import settings # Import settings
from django.conf.urls.static import static # Import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('talents.urls')), # Connect our app here
]

# This part is required to serve images during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)