from django import forms
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import get_user_model
from .models import Globals

User = get_user_model()

from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class UserProfileForm(forms.ModelForm):
    new_password1 = forms.CharField(
        label="New password", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    new_password2 = forms.CharField(
        label="Confirm new password", 
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 or new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError("The new passwords do not match.")
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        new_password = self.cleaned_data.get('new_password1')

        if new_password:
            user.set_password(new_password)
        
        if commit:
            user.save()

        return user



class SettingsForm(forms.ModelForm):
    class Meta:
        model = Globals
        fields = [
            'pdfDirectory', 'checkAllStartAtHour', 'checkAllStartAtMin',
            'checkAllIntervalHours', 'checkAllIntervalMins', 'emailNotifyOnNewLink',
            'sendToEmails', 'attachListToEmail',
        ]
        labels = {
            'pdfDirectory': 'Source Directory',
            'checkAllStartAtHour': 'Check All Start Hour (valid range 0-23)',
            'checkAllStartAtMin': 'Check All Start Minute (valid range 0-59)',
            'checkAllIntervalHours': 'Check All Interval Hours',
            'checkAllIntervalMins': 'Check All Interval Minutes',
            'emailNotifyOnNewLink':'Email Notification On New Broken Links',
            'sendToEmails': 'Send Email Notification To (comma separated email addresses)',
            'attachListToEmail':'Attach List',
        }
        widgets = {
            'pdfDirectory': forms.TextInput(attrs={'class': 'form-control'}),
            'checkAllStartAtHour': forms.NumberInput(attrs={'class': 'form-control'}),
            'checkAllStartAtMin': forms.NumberInput(attrs={'class': 'form-control'}),
            'checkAllIntervalHours': forms.NumberInput(attrs={'class': 'form-control'}),
            'checkAllIntervalMins': forms.NumberInput(attrs={'class': 'form-control'}),
            'emailNotifyOnNewLink': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'attachListToEmail': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sendToEmails': forms.TextInput(attrs={'class': 'form-control'}),
        }


class SmtpSettingsForm(forms.ModelForm):
    class Meta:
        model = Globals
        fields = [
            'fromEmail', 'smtpHost', 'smtpPort', 'smtpUsername', 'smtpPassword'
        ]
        labels = {
            'fromEmail': 'From Email',
            'smtpHost': 'SMTP Host',
            'smtpPort': 'STMP Port',
            'smtpUsername': 'SMTP Username',
            'smtpPassword': 'SMTP Password'
        }
        widgets = {
            'fromEmail': forms.TextInput(attrs={'class': 'form-control'}),
            'smtpPort': forms.NumberInput(attrs={'class': 'form-control'}),
            'smtpHost': forms.TextInput(attrs={'class': 'form-control'}),
            'smtpUsername': forms.TextInput(attrs={'class': 'form-control'}),
            'smtpPassword': forms.PasswordInput(render_value = True, attrs={'class': 'form-control', 'placeholder':'********','autocomplete': 'off'}),
        }
