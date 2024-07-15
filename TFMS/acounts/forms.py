from django import forms
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm
import re
from .models import *


class UserRegistrationForm(UserCreationForm):
    role_choices = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
    )
    gender_choices = (
        ('male', 'Male'),
        ('female', 'Female')
    )
    first_name = forms.CharField(label='First Name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Last Name', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    location = forms.CharField(label='Location', widget=forms.TextInput(attrs={'class': 'form-control'}))
    sex = forms.ChoiceField(label='Gender', choices=gender_choices, widget=forms.Select(attrs={'class': 'form-control'}))
    phone = forms.CharField(label='Phone', widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(label='Role', choices=role_choices, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'location', 'sex', 'phone', 'role']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Check if the phone number starts with '07' and convert it to '2557...'
        if phone.startswith('07') and len(phone) == 10:
            phone = '255' + phone[1:]
        # Validate the converted phone number
        if not re.match(r'^255[0-9]{9}$', phone):
            raise ValidationError("Phone number must be in the format 255XXXXXXXXX or 07XXXXXXXX.")
        return phone


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'sex', 'location']
        labels = {
            'phone': 'Phone Number',
            'sex': 'Sex',
            'location': 'Location',
        }
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'sex': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }


class LoanRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(LoanRequestForm, self).__init__(*args, **kwargs)
        self.fields['amount_requested'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Enter Amount Requested'})
        self.fields['reason'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Reason'})

    class Meta:
        model = LoanRequest
        fields = ['amount_requested', 'reason']

    def __init__(self, *args, **kwargs):
        super(LoanRequestForm, self).__init__(*args, **kwargs)
        self.fields['amount_requested'].label = 'Requested Amount'
        self.fields['amount_requested'].widget.attrs['placeholder'] = 'Enter the amount you want to request'
        self.fields['reason'].label = 'Reason for Loan'
        self.fields['reason'].widget.attrs['placeholder'] = 'Enter the reason for your loan request'


class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(queryset=User.objects.filter(profile__role='buyer'))

    class Meta:
        model = Message
        fields = ['receiver', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }


class FeedbackLoanForm(forms.Form):
    FEEDBACK_CHOICES = (
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    feedback = forms.ChoiceField(choices=FEEDBACK_CHOICES, widget=forms.RadioSelect)


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'cols': 40}),
        }
