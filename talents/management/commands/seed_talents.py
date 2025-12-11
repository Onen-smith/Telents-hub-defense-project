import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from talents.models import Profile, Skill
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Seeds 5 talents for every specific category'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting targeted seeding...')

        # 1. Your Specific Categories
        CATEGORIES = [
            'Account Management', 
            'Business Development', 
            'Customer Care & Success', 
            'Finance', 
            'IT / Software', 
            'Marketing', 
            'People / Talent Acquisition', 
            'PR & Communications', 
            'Product Design', 
            'Product Management', 
            'Sales', 
            'Operations'
        ]
        
        LOCATIONS = ['Lagos', 'Abuja', 'Port Harcourt', 'Ibadan', 'Enugu', 'Remote']

        # 2. Loop through each category
        for category_name in CATEGORIES:
            self.stdout.write(f"--- Seeding 5 talents for: {category_name} ---")
            
            # Create the Skill object if it doesn't exist
            skill_obj, _ = Skill.objects.get_or_create(name=category_name)

            # Create 5 Users for this category
            for i in range(5):
                first_name = fake.first_name()
                last_name = fake.last_name()
                # Create a unique username based on category to avoid clashes
                username = f"{category_name[:3].lower()}_{first_name.lower()}{random.randint(100,999)}"
                email = f"{username}@example.com"

                # Create User
                if not User.objects.filter(username=username).exists():
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password='password123',
                        first_name=first_name,
                        last_name=last_name
                    )

                    # Get Profile
                    profile, created = Profile.objects.get_or_create(user=user)
                    
                    # Add Details
                    profile.location = random.choice(LOCATIONS)
                    profile.bio = fake.text(max_nb_chars=120)
                    profile.hourly_rate = random.randint(30, 200)
                    profile.is_verified = random.choice([True, True, False]) # Higher chance of verified
                    
                    # Assign the specific skill
                    profile.skills.add(skill_obj)
                    
                    # Save
                    profile.save()
                    self.stdout.write(self.style.SUCCESS(f"Created {first_name} in {category_name}"))

        self.stdout.write(self.style.SUCCESS('--------------------------------------'))
        self.stdout.write(self.style.SUCCESS('DONE! Each category now has at least 5 talents.'))