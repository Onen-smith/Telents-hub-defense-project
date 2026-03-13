from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- 1. LANDING & STATIC PAGES ---
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('careers/', views.careers, name='careers'),
    path('contact/', views.contact, name='contact'),
    path('blog/', views.blog, name='blog'),
    path('blog/<int:pk>/', views.blog_detail, name='blog_detail'),

    # --- 2. AUTHENTICATION ---
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='talents/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # --- 3. DASHBOARD & ONBOARDING ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complete-onboarding/', views.complete_onboarding, name='complete_onboarding'),
    path('notifications/', views.notifications, name='notifications'),
    
    # --- 4. PROFILES ---
    path('profile/edit/', views.profile_update, name='profile_update'),
    path('profile/<slug:slug>/', views.profile_detail, name='profile_detail'),
    path('browse/', views.browse, name='browse'), # Talent Directory
    path('follow/<int:profile_id>/', views.toggle_follow, name='toggle_follow'),

    # --- 5. JOBS ---
    path('find-work/', views.job_list, name='job_list'),
    path('post-job/', views.post_job, name='post_job'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('job/<slug:slug>/', views.job_detail, name='job_detail'),
    path('job/<slug:slug>/save/', views.toggle_save_job, name='toggle_save_job'),
    path('job/<slug:slug>/apply/', views.apply_to_job, name='apply_to_job'),
    path('job/<slug:slug>/manage/', views.manage_job, name='manage_job'),
    path('job/<slug:slug>/edit/', views.edit_job, name='edit_job'),
    path('proposal/<int:proposal_id>/hire/', views.create_contract, name='create_contract'),
    path('contract/<int:pk>/', views.contract_detail, name='contract_detail'),
    
    # --- 6. MESSAGES ---
    path('messages/', views.inbox, name='inbox'),
    path('messages/<str:username>/', views.chat_detail, name='chat_detail'),
    
    # --- 7. WALLET & PAYMENTS ---
    path('wallet/', views.wallet, name='wallet'),
    path('payment/checkout/<str:reference>/', views.payment_checkout, name='payment_checkout'),
    path('payment/verify/<str:reference>/', views.verify_payment, name='verify_payment'),
    
    # --- 8. SETTINGS & UTILS ---
    path('settings/', views.settings_view, name='settings'),
    path('verify-identity/', views.verify_identity, name='verify_identity'),
    path('leave-review/', views.leave_review, name='leave_review'),
    path('profile/@<str:username>/', views.public_profile, name='profile_view'),    
    path('hire/<int:freelancer_id>/', views.hire_freelancer, name='hire_freelancer'),
]