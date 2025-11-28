import os

from dotenv import load_dotenv
from flask import Flask, request, render_template, flash, session, redirect, url_for

from db.queries import (
    get_user_by_email,
    get_user_by_net_id,
    create_new_user,
    get_all_current_opportunities,
    get_opportunity_details,
)
from utils.auth import compare_password, hash_password, login_required
from utils.validator import (
    validate_email,
    validate_not_empty,
    validate_net_id,
    validate_password,
    validate_role,
)

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return "About Page"


@app.route("/privacy")
def privacy():
    return "Privacy Page"


@app.route("/login", methods=["GET", "POST"])
def login():
    # if user is already logged in, return
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        # validate user input
        if not validate_email(email):
            flash("Please enter a valid email")
            return redirect(url_for("login"))

        if len(password) == 0:
            flash("Please enter your password")
            return redirect(url_for("login"))

        # check if user exists in db
        user = get_user_by_email(email)
        if not user:
            flash("Invalid Credentials")
            return redirect(url_for("login"))

        # compare the user's password
        if not compare_password(password, user["password"]):
            flash("Invalid Credentials")
            return redirect(url_for("login"))

        # add user data to session
        session["user_id"] = user["user_id"]
        session["name"] = user["first_name"]

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # if user is already logged in, return
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        first_name = request.form["firstName"].strip().capitalize()
        last_name = request.form["lastName"].strip().capitalize()
        net_id = request.form["netId"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        role = request.form["role"].strip().lower()

        # validate user input
        if not validate_not_empty(first_name, last_name, net_id, email, password, role):
            flash("Please enter data in all fields")
            return redirect(url_for("register"))

        if not validate_net_id(net_id):
            flash("Please enter a valid Net ID")
            return redirect(url_for("register"))

        if not validate_password(password):
            flash("Your password should be at least 6 characters long")
            return redirect(url_for("register"))

        if not validate_role(role):
            flash("Please pick a valid role - Student or Password")
            return redirect(url_for("register"))

        # check if the user already exists in db
        if get_user_by_email(email) or get_user_by_net_id(net_id):
            flash("The user already exists")
            return redirect(url_for("register"))

        # hash the user's password
        hashed_password = hash_password(password).decode("utf-8")

        # insert the user into the users table and store the user id
        user_id = create_new_user(
            first_name, last_name, net_id, email, hashed_password, role
        )

        # add user data to session
        session["user_id"] = user_id
        session["name"] = first_name

        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/logout", methods=["GET"])
def logout():
    # clear the user session
    session.clear()

    # redirect to the index page
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET"])
@login_required
def profile():
    return "Profile Page"


@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard():
    opportunities = get_all_current_opportunities()
    categories = list(
        set(
            [
                opportunity["category"].replace("_", " ").title()
                for opportunity in opportunities
            ]
        )
    )
    categories.sort()

    return render_template(
        "dashboard.html", opportunities=opportunities, categories=categories
    )


@app.route("/opportunity/<int:opp_id>")
@login_required
def opportunity_details(opp_id: int):
    opp_details = get_opportunity_details(opp_id)

    return render_template("opportunityDetails.html", opp_details=opp_details)


@app.route("/organization/<int:org_id>")
@login_required
def organization_details(org_id: int):
    return f"Organization {org_id} details page"


if __name__ == "__main__":
    app.run(debug=True)
