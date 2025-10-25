from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Profile

class UserRegisterForm(UserCreationForm):
    image = forms.ImageField(required=False, label="Profile Picture")

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'role', 'image', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit)
        image = self.cleaned_data.get('image')

        if commit:
            profile = getattr(user, "profile", None)
            if profile and image:
                profile.image = image
                profile.save()

        return user