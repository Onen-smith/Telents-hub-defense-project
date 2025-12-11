import os
import random
from django.core.management.base import BaseCommand
from talents.models import Profile
from django.conf import settings

class Command(BaseCommand):
    help = 'Assigns random images to existing profiles'

    def handle(self, *args, **kwargs):
        # 1. Define the list of image filenames you saved
        # Make sure these match EXACTLY what you saved in media/profile_pics/
        AVAILABLE_IMAGES = [
            'profile_pics/1.avif',
            'profile_pics/2.avif',
            'profile_pics/3.avif',
            'profile_pics/4.avif',
            'profile_pics/5.avif',
            'profile_pics/6.avif',
            'profile_pics/7.avif',
            'profile_pics/8.avif',
            'profile_pics/9.avif',
            'profile_pics/10.avif',
            'profile_pics/11.jpg',
            'profile_pics/CV.jpg',
            # Add more if you have them: 'profile_pics/6.jpg', etc.
        ]

        profiles = Profile.objects.all()
        count = 0

        self.stdout.write('Assigning images...')

        for profile in profiles:
            # Skip the admin (superuser) if you want to keep your own photo
            if profile.user.is_superuser:
                continue

            # Pick a random image from the list
            random_image = random.choice(AVAILABLE_IMAGES)
            
            # Assign it
            profile.profile_pic = random_image
            profile.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully updated {count} profiles with random images!'))