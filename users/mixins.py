from django.contrib.auth.mixins import UserPassesTestMixin

class RoleRequiredMixin(UserPassesTestMixin):

    allowed_roles = None 

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False

        allowed = self.allowed_roles
        if isinstance(allowed, str):
            allowed = [allowed]

        if getattr(user, 'role', None) in allowed:
            return True

        if user.groups.filter(name__in=allowed).exists():
            return True

        return False
