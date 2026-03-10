from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.utils import user_username
from django.contrib.auth import get_user_model

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        
        # If no username is set, create one from the email (e.g. onene244)
        if not user.username:
            username = user.email.split('@')[0]
            # Ensure it's unique
            User = get_user_model()
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{user.email.split('@')[0]}{counter}"
                counter += 1
            user.username = username
            
        return user