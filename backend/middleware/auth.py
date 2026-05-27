from functools import wraps
from flask import session, redirect, url_for, g
from backend.config.settings import settings


def current_user():
    return session.get("user")


def resolve_role(email: str, approved_staff: set[str]):
    if email == settings.SUPER_ADMIN_EMAIL:
        return "super_admin"
    if email in approved_staff:
        return "staff_admin"
    return "user"


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("web.login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if not user or user.get("role") not in roles:
                return redirect(url_for("web.home"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def attach_user_context():
    g.user = current_user()
