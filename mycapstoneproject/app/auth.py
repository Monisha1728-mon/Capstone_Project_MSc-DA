from functools import wraps

from flask import session, redirect, url_for

# ---------------------------------------------------------
# Normal logged-in user
# ---------------------------------------------------------


def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped


# ---------------------------------------------------------
# Admin only
# ---------------------------------------------------------


def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            return redirect(url_for("form"))

        return view(*args, **kwargs)

    return wrapped
