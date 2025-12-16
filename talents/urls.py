from django.urls import path
from . import views

urlpatterns = [
    # Core Pages
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    
    # Dashboard & Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/update/', views.profile_update, name='profile_update'),
    
    # This is the line that fixed the error (It uses views.profile_detail now)
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),

    # Communication
    path('contact/', views.contact, name='contact'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),

    # Static Pages
    path('about/', views.about, name='about'),
    path('careers/', views.careers, name='careers'),
    path('blog/', views.blog, name='blog'),
    path('blog/<int:pk>/', views.blog_detail, name='blog_detail'),
    path('privacy/', views.privacy, name='privacy'),
]