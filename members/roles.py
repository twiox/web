"""Who may do what: the role checks used across all apps.

Roles decide who may enter an area and who may create, edit or delete things; views
use the mixins and decorators below, templates the context variables ({% if is_board %}).

- is_trainer / is_chairman: the bare roles, for role-specific pages and UI
  (e.g. a trainer's own training sessions need request.user.trainer).
- is_privileged: trainer, chairman or superuser – the club's staff.
- is_board: chairman or superuser – board-only pages.
"""
from functools import wraps

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


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


def role_required(check):
    """Decorator for function views: 403 unless the user has the role (put @login_required above it)."""
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not check(request.user):
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return wrapped
    return decorator


privileged_required = role_required(is_privileged)
board_required = role_required(is_board)


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
