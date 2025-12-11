from django.db import models
from django.contrib.auth.models import User

# 1. Skill/Category Model
class Skill(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Basic Info
    phone_number = models.CharField(max_length=15, blank=True)
    location = models.CharField(max_length=100, help_text="City, State")
    bio = models.TextField(blank=True, help_text="Describe your services")
    
    # The Talent part
    profile_pic = models.ImageField(upload_to='profile_pics/', default='default.jpg')
    # --- DELETED THE DUPLICATE LINE HERE ---
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cover_photo = models.ImageField(upload_to='cover_photos/', blank=True, null=True)
    
    # Relationships
    skills = models.ManyToManyField(Skill, blank=True) 
    
    # Verification
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

# 3. The Review Model (MUST BE AT THE BOTTOM)
class Review(models.Model):
    # Notice we put 'Profile' in quotes just to be safe
    talent = models.ForeignKey('Profile', on_delete=models.CASCADE, related_name='reviews')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0, choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.rating} for {self.talent}"

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"

# 5. Newsletter Subscriber Model
class Subscriber(models.Model):
    email = models.EmailField(unique=True) # unique=True prevents duplicates
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    
class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, default='News') # e.g., Tips, Community
    image_url = models.URLField(default="https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d") # Using URL to keep it simple with Unsplash
    excerpt = models.TextField(help_text="Short summary for the card")
    content = models.TextField(help_text="Full article content")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"