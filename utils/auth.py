import json
from functools import wraps

import bcrypt
from flask import session, redirect, url_for, flash, make_response, request

from db.queries import check_is_representative, get_signup_details_by_id


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def compare_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def is_representative(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session["user_id"]
        org_id = kwargs["org_id"]

        if not check_is_representative(user_id, org_id):
            if request.headers.get("HX-Request"):
                response = make_response("")
                response.headers["HX-Trigger"] = json.dumps(
                    {
                        "showToast": {
                            "message": "You do not manage that organization",
                            "type": "error",
                        }
                    }
                )
                response.headers["HX-Redirect"] = url_for("dashboard")
                return response

            # Non-HTMX request
            flash("You do not manage that organization", "error")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function


def is_authorized_to_delete_signup(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session["user_id"]
        signup_id = kwargs["signup_id"]

        signup_details = get_signup_details_by_id(signup_id)

        if not signup_details:
            if request.headers.get("HX-Request"):
                response = make_response("")
                response.headers["HX-Trigger"] = json.dumps(
                    {
                        "showToast": {
                            "message": "Invalid Signup ID",
                            "type": "error",
                        }
                    }
                )
                response.headers["HX-Redirect"] = url_for("dashboard")
                return response

            flash("Invalid Signup ID", "error")
            return redirect(url_for("dashboard"))

        if (
            signup_details["user_id"] != user_id
            and signup_details["org_rep_id"] != user_id
        ):
            if request.headers.get("HX-Request"):
                response = make_response("")
                response.headers["HX-Trigger"] = json.dumps(
                    {
                        "showToast": {
                            "message": "You are not authorized to make this request",
                            "type": "error",
                        }
                    }
                )
                response.headers["HX-Redirect"] = url_for("dashboard")
                return response

            flash("You are not authorized to make this request", "error")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function
