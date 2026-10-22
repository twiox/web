"""Who may do what: the role checks used across all apps.

Roles decide who may enter an area (board pages, orga pages, check-in, trainer pages).
Fine-grained create/edit/delete actions use the Django permissions, which the role
signals in user_handling keep in sync with the roles (perms.members.change_event etc.).

- is_trainer / is_chairman: the bare roles, for role-specific pages and UI
  (e.g. a trainer's own training sessions need request.user.trainer).
- is_privileged: trainer, chairman or superuser – the club's staff.
- is_board: chairman or superuser – board-only pages.
"""
from django.contrib.auth.mixins import UserPassesTestMixin


def is_trainer(user):
    trainer = getattr(user, "trainer", None)
    return trainer is not None and trainer.active


def is_chairman(user):
    chairman = getattr(user, "chairman", None)
    return chairman is not None and chairman.active


def is_privileged(user):
    return user.is_superuser or is_trainer(user) or is_chairman(user)


def is_board(user):
    return user.is_superuser or is_chairman(user)


class PrivilegedRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_privileged(self.request.user)


class BoardRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_board(self.request.user)


def roles(request):
    """Context processor: the role checks for templates ({% if is_privileged %} …)."""
    user = request.user
    if not user.is_authenticated:
        return {}
    return {
        "is_trainer": is_trainer(user),
        "is_chairman": is_chairman(user),
        "is_privileged": is_privileged(user),
        "is_board": is_board(user),
    }
