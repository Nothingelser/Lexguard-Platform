from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import ForcedPasswordChangeDoneView, ForcedPasswordChangeView, RoleAwareLoginView

app_name = "accounts"

urlpatterns = [
    path("login/", RoleAwareLoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-change/", ForcedPasswordChangeView.as_view(), name="password_change"),
    path("password-change/done/", ForcedPasswordChangeDoneView.as_view(), name="password_change_done"),
]
