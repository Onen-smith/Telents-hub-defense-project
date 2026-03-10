from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Proposal, Review, Skill, Job, Transaction


# 1. Simple Register Form
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

# 2. User Update Form (Username, Email, Name)
class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

# 3. Profile Update Form (UPDATED with new fields)
class ProfileUpdateForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Profile
        # Added: headline, years_experience, availability, english_level, tools, project_link
        fields = [
            'profile_pic', 'headline', 'bio', 'location', 
            'hourly_rate', 'years_experience', 'availability', 
            'english_level', 'company_name', 'project_link', 
            'tools', 'skills'
        ]
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Developer'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'hourly_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'years_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'availability': forms.Select(attrs={'class': 'form-select'}),
            'english_level': forms.Select(attrs={'class': 'form-select'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'project_link': forms.URLInput(attrs={'class': 'form-control'}),
            'tools': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Comma separated (e.g. Jira, Figma)'}),
        }

# 4. Review Form (Styled for Glass Theme)
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Stars') for i in range(1, 6)],
                attrs={'class': 'form-select'} # Makes it look modern
            ),
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control', 
                    'rows': 3, 
                    'placeholder': 'Share your experience working with this talent...'
                }
            )
        }

class JobForm(forms.ModelForm):
    # This field creates the box for "Python, React, CSS"
    skills_input = forms.CharField(
        label="Required Skills",
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. Python, Django, React (comma separated)',
            'class': 'form-control' # This class is important for styling
        })
    )

    class Meta:
        model = Job
        fields = ['title', 'description', 'job_type', 'budget']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Build a specific E-commerce Website'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe your project in detail...'}),
            'job_type': forms.Select(attrs={'class': 'form-select'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '500.00'}),
        }

    def save_m2m(self):
        instance = self.instance
        skills_string = self.cleaned_data.get('skills_input')
        if skills_string:
            instance.skills_required.clear()
            for skill_name in skills_string.split(','):
                skill_name = skill_name.strip()
                if skill_name:
                    skill, _ = Skill.objects.get_or_create(name__iexact=skill_name, defaults={'name': skill_name})
                    instance.skills_required.add(skill)

# Add this to forms.py
class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['cover_letter', 'bid_amount', 'estimated_days']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Why are you the best fit?'}),
            'bid_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_days': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class DepositForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': 'Amount (e.g. 5000)',
                'min': '100'  # HTML validation: Minimum 100 Naira
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 100:
            raise forms.ValidationError("Minimum deposit is ₦100.")
        return amount
    
class WithdrawForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg', 
                'placeholder': 'Amount to Withdraw',
                'min': '100'
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount < 100:
            raise forms.ValidationError("Minimum withdrawal is ₦100.")
        return amount