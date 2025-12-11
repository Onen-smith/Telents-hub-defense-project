import os
from django.core.management.base import BaseCommand
from django.conf import settings
from talents.models import Profile

class Command(BaseCommand):
    help = 'Assigns all images found in media/profile_pics to existing profiles'

    def handle(self, *args, **kwargs):
        # 1. Locate the folder
        pics_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pics')
        
        self.stdout.write(f"Looking for images in: {pics_dir}")

        # 2. Get all image files
        try:
            all_files = os.listdir(pics_dir)
            # Filter to ensure we only get image files
            images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Folder not found! Please create: {pics_dir}"))
            return

        if not images:
            self.stdout.write(self.style.WARNING("No images found in that folder! Please paste some .jpg or .png files there first."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(images)} images. Assigning them to profiles..."))

        # 3. Get all Profiles
        profiles = Profile.objects.all()
        count = 0

        # 4. Loop through profiles and assign images
        for i, profile in enumerate(profiles):
            # Skip the admin if you want (optional)
            if profile.user.is_superuser:
                continue

            # This math logic cycles the images endlessly
            # If i = 0, it picks image 0. If i = 50 and you have 20 images, it picks image 10.
            image_name = images[i % len(images)]
            
            # Assign the path relative to MEDIA_ROOT
            profile.profile_pic = os.path.join('profile_pics', image_name)
            profile.save()
            
            self.stdout.write(f"[{i+1}] Assigned {image_name} to {profile.user.username}")
            count += 1

        self.stdout.write(self.style.SUCCESS(f"-----------------------------------"))
        self.stdout.write(self.style.SUCCESS(f"Done! Successfully updated {count} profiles."))