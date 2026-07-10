from django import forms
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User


class BadgeAuthenticationForm(forms.Form):
    badge_number = forms.CharField(
        label=_("Badge number"),
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    error_messages = {
        "invalid_login": _("Please enter a correct badge number and password."),
        "inactive": _("This account is inactive."),
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        badge_number = self.cleaned_data.get("badge_number")
        password = self.cleaned_data.get("password")

        if badge_number and password:
            try:
                user_obj = User.objects.get(badge_number=badge_number)
            except User.DoesNotExist as exc:
                raise ValidationError(self.error_messages["invalid_login"], code="invalid_login") from exc

            self.user_cache = authenticate(self.request, username=user_obj.username, password=password)
            if self.user_cache is None:
                raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")
            if not self.user_cache.is_active:
                raise ValidationError(self.error_messages["inactive"], code="inactive")

        return self.cleaned_data

    def get_user(self):
        return self.user_cache
