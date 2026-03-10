from django.contrib import admin
from .models import Profile, Skill, Job, Proposal, Contract, Review, Notification, BlogPost, ContactMessage, Subscriber, Message, Transaction


# Register your models here
admin.site.register(Profile)
admin.site.register(Skill)
admin.site.register(Job)        # <--- THIS WAS MISSING
admin.site.register(Proposal)
admin.site.register(Contract)
admin.site.register(Review)
admin.site.register(Notification)
admin.site.register(BlogPost)
admin.site.register(ContactMessage)
admin.site.register(Subscriber)
admin.site.register(Message)
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status')
    search_fields = ('user__username', 'reference')