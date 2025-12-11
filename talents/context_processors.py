from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        # Get top 5 newest notifications
        notifs = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
        # Count how many are unread
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        
        return {
            'notifications': notifs,
            'unread_count': unread_count
        }
    return {
        'notifications': [],
        'unread_count': 0
    }