from django.urls import path
from django.contrib.auth import views as auth_views # Import this
from . import views
from .views import ProfileDetailView, profile_update
from .views import dashboard

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    
    # Auth Routes
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='talents/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='talents/logout.html'), name='logout'),
    path('profile/edit/', views.profile_update, name='profile_update'),
    path('about/', views.about, name='about'),
    path('careers/', views.careers, name='careers'),
    path('blog/', views.blog, name='blog'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy, name='privacy'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('browse/', views.browse, name='browse'),
    path('blog/<int:pk>/', views.blog_detail, name='blog_detail'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('profile/<int:pk>/', ProfileDetailView.as_view(), name='profile_detail'),
    path('dashboard/', dashboard, name='dashboard'),
]