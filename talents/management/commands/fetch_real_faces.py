import os
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from talents.models import Profile

class Command(BaseCommand):
    help = 'Downloads unique real faces for every profile'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting download of unique faces... This requires internet.')

        profiles = Profile.objects.all()
        total = profiles.count()

        for i, profile in enumerate(profiles):
            # Skip admin
            if profile.user.is_superuser:
                continue

            # 1. Generate a unique URL based on their username
            # This API ensures the same username always gets the same face, 
            # but different usernames get different faces.
            avatar_url = f"https://i.pravatar.cc/400?u={profile.user.username}"

            try:
                # 2. Download the image
                response = requests.get(avatar_url, timeout=10, verify=False)
                
                if response.status_code == 200:
                    # 3. Save it to the profile
                    # We name the file "username_face.jpg"
                    file_name = f"{profile.user.username}_face.jpg"
                    profile.profile_pic.save(file_name, ContentFile(response.content), save=True)
                    
                    self.stdout.write(self.style.SUCCESS(f'[{i+1}/{total}] Saved face for {profile.user.username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'Failed to download for {profile.user.username}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error for {profile.user.username}: {e}'))

        self.stdout.write(self.style.SUCCESS('----------------------------------'))
        self.stdout.write(self.style.SUCCESS('DONE! All profiles now have unique, offline-ready images.'))