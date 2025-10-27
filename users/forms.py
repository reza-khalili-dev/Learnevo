from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
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


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'role', 'is_active', 'is_staff')
        widgets = {
            'password': forms.PasswordInput(render_value=True),
        }