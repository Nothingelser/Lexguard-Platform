from django.contrib.auth.views import LoginView, PasswordChangeDoneView, PasswordChangeView
from django.urls import reverse, reverse_lazy

from .forms import BadgeAuthenticationForm


class RoleAwareLoginView(LoginView):
    authentication_form = BadgeAuthenticationForm

    def get_success_url(self):
        user = self.request.user
        if user.is_super_admin:
            return reverse("admin:index")
        if user.must_change_password:
            return reverse("accounts:password_change")
        return reverse("dashboard")


class ForcedPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        return response


class ForcedPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "registration/password_change_done.html"
