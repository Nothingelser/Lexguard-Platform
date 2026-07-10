from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse

from apps.accounts.services import (
    lock_account,
    next_commander_badge,
    next_officer_badge,
    provision_commander_account,
    provision_officer_account,
)
from apps.stations.models import PoliceStation

from .models import User


class PersonnelProvisionAddForm(forms.ModelForm):
    password1 = forms.CharField(label="Temporary password", strip=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm temporary password", strip=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "role", "station")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["station"].queryset = PoliceStation.objects.filter(is_active=True).order_by("county", "name")
        self.fields["role"].choices = (
            (User.Role.OFFICER, "Station Officer"),
            (User.Role.COMMANDER, "Regional Commander"),
        )
        self.fields["station"].required = False
        self.fields["station"].help_text = "Required for station officers only."

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        role = cleaned.get("role")
        station = cleaned.get("station")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The temporary passwords do not match.")

        if role == User.Role.OFFICER and not station:
            self.add_error("station", "Select a station for a station officer.")
        if role == User.Role.COMMANDER and station:
            self.add_error("station", "Regional commanders do not use a station.")
        if role not in {User.Role.OFFICER, User.Role.COMMANDER}:
            self.add_error("role", "Only station officers and regional commanders can be created from the admin add page.")

        return cleaned


class OfficerProvisionForm(forms.Form):
    station = forms.ModelChoiceField(queryset=PoliceStation.objects.filter(is_active=True).order_by("county", "name"))
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(required=False)


class CommanderProvisionForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(required=False)


class LockAccountForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("username"),
        label="Account to lock",
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "badge_number", "role", "station", "must_change_password", "is_active")
    list_filter = ("role", "station", "must_change_password", "is_active")
    readonly_fields = ("badge_number",)
    add_form = PersonnelProvisionAddForm
    fieldsets = BaseUserAdmin.fieldsets + (
        ("LexGuard Profile", {"fields": ("badge_number", "role", "must_change_password", "station")}),
    )
    add_fieldsets = (
        (None, {"fields": ("first_name", "last_name", "email")}),
        ("LexGuard Profile", {"fields": ("role", "station")}),
        ("Temporary Access", {"fields": ("password1", "password2")}),
    )
    change_list_template = "admin/accounts/user/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("personnel/", self.admin_site.admin_view(self.personnel_control_view), name="accounts_user_personnel_control"),
        ]
        return custom_urls + urls

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        role = form.cleaned_data["role"]
        password = form.cleaned_data["password1"]
        station = form.cleaned_data.get("station")

        if role == User.Role.OFFICER:
            badge_number = next_officer_badge(station)
        elif role == User.Role.COMMANDER:
            badge_number = next_commander_badge()
            station = None
        else:
            raise ValidationError("Only station officers and regional commanders can be created from this screen.")

        obj.username = badge_number
        obj.badge_number = badge_number
        obj.station = station
        obj.must_change_password = True
        obj.is_active = True
        obj.set_password(password)
        obj.save()

    def personnel_control_view(self, request):
        officer_form = OfficerProvisionForm()
        commander_form = CommanderProvisionForm()
        lock_form = LockAccountForm()

        if request.method == "POST" and "provision_officer" in request.POST:
            officer_form = OfficerProvisionForm(request.POST)
            if officer_form.is_valid():
                user = provision_officer_account(
                    station=officer_form.cleaned_data["station"],
                    first_name=officer_form.cleaned_data["first_name"],
                    last_name=officer_form.cleaned_data["last_name"],
                    password=officer_form.cleaned_data["password"],
                    email=officer_form.cleaned_data.get("email"),
                )
                self.message_user(
                    request,
                    f"Provisioned officer {user.get_full_name() or user.username} with login {user.badge_number}.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(reverse("admin:accounts_user_changelist"))

        if request.method == "POST" and "provision_commander" in request.POST:
            commander_form = CommanderProvisionForm(request.POST)
            if commander_form.is_valid():
                user = provision_commander_account(
                    first_name=commander_form.cleaned_data["first_name"],
                    last_name=commander_form.cleaned_data["last_name"],
                    password=commander_form.cleaned_data["password"],
                    email=commander_form.cleaned_data.get("email"),
                )
                self.message_user(
                    request,
                    f"Provisioned commander {user.get_full_name() or user.username} with login {user.badge_number}.",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(reverse("admin:accounts_user_changelist"))

        if request.method == "POST" and "lock_account" in request.POST:
            lock_form = LockAccountForm(request.POST)
            if lock_form.is_valid():
                user = lock_form.cleaned_data["user"]
                lock_account(user)
                self.message_user(
                    request,
                    f"Locked account {user.username} ({user.badge_number}).",
                    level=messages.WARNING,
                )
                return HttpResponseRedirect(reverse("admin:accounts_user_changelist"))

        context = {
            **self.admin_site.each_context(request),
            "title": "Personnel Control",
            "officer_form": officer_form,
            "commander_form": commander_form,
            "lock_form": lock_form,
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
            "has_change_permission": self.has_change_permission(request),
            "has_add_permission": self.has_add_permission(request),
            "has_delete_permission": self.has_delete_permission(request),
            "cl_url": reverse("admin:accounts_user_changelist"),
        }
        return TemplateResponse(request, "admin/accounts/user/personnel_control.html", context)
