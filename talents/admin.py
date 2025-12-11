from django.contrib import admin
from .models import Skill, Profile
from .models import Skill, Profile, Review, ContactMessage, Subscriber
from .models import BlogPost # Add BlogPost to imports
admin.site.register(BlogPost)

admin.site.register(Skill)
admin.site.register(Profile)
admin.site.register(ContactMessage)
admin.site.register(Subscriber) 