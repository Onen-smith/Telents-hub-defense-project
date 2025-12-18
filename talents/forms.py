from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Review  # Make sure Review is imported here!

# 1. User Registration Form
class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

from django import forms
from django.contrib.auth.models import User
from .models import Profile

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # MUST INCLUDE 'cover_photo' HERE
        fields = ['profile_pic', 'cover_photo', 'bio', 'location', 'hourly_rate', 'skills']
        
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
# 3. Review Form (The one that was breaking)
class ReviewForm(forms.ModelForm):  # Changed 'models.ModelForm' to 'forms.ModelForm'
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Write your experience...'})
        }


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user