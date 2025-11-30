import json
import os

from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    render_template,
    flash,
    session,
    redirect,
    url_for,
    make_response,
)

from db.queries import (
    get_user_by_email,
    get_user_by_net_id,
    get_user_by_id,
    get_user_signups,
    create_new_user,
    get_all_current_opportunities,
    get_opportunity_details,
    get_all_user_orgs,
    get_org_by_name,
    create_new_org,
    get_org_details,
    get_all_current_opportunities_for_org,
    delete_user_signup,
)
from utils.auth import compare_password, hash_password, login_required
from utils.image_uploader import upload_image
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


@app.before_request
def debug_request():
    print(request.method, request.path)


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
        errors = []

        if not validate_email(email):
            errors.append("Please enter a valid email")

        if len(password) == 0:
            errors.append("Please enter your password")

        if errors:
            for e in errors:
                flash(e)

            return render_template("partials/errorMessages.html")

        # check if user exists in db
        user = get_user_by_email(email)
        if not user:
            flash("Invalid Credentials")
            return render_template("partials/errorMessages.html")

        # compare the user's password
        if not compare_password(password, user["password"]):
            flash("Invalid Credentials")
            return render_template("partials/errorMessages.html")

        # add user data to session
        session["user_id"] = user["user_id"]
        session["name"] = user["first_name"]

        response = make_response("")
        response.headers["HX-Redirect"] = url_for("dashboard")
        return response

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
        errors = []

        if not validate_not_empty(first_name, last_name, net_id, email, password, role):
            errors.append("Please enter data in all fields")

        if not validate_net_id(net_id):
            errors.append("Please enter a valid Net ID")

        if not validate_password(password):
            errors.append("Your password should be at least 6 characters long")

        if not validate_role(role):
            errors.append("Please pick a valid role - Student or Password")

        if errors:
            for e in errors:
                flash(e)

            return render_template("partials/errorMessages.html")

        # check if the user already exists in db
        if get_user_by_email(email) or get_user_by_net_id(net_id):
            flash("The user already exists")
            return render_template("partials/errorMessages.html")

        # hash the user's password
        hashed_password = hash_password(password).decode("utf-8")

        # insert the user into the users table and store the user id
        user_id = create_new_user(
            first_name, last_name, net_id, email, hashed_password, role
        )

        # add user data to session
        session["user_id"] = user_id
        session["name"] = first_name

        response = make_response("")
        response.headers["HX-Redirect"] = url_for("dashboard")
        return response

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
    user_id = session.get("user_id")
    user = get_user_by_id(user_id)

    return render_template("profile.html", user=user)


@app.route("/profile/tabs/signups", methods=["GET"])
@login_required
def profile_signups():
    user_id = session["user_id"]
    signups = get_user_signups(user_id)

    return render_template("partials/profile_signups.html", signups=signups)


@app.route("/profile/tabs/organizations", methods=["GET"])
@login_required
def profile_orgs():
    user_id = session.get("user_id")
    organizations = get_all_user_orgs(user_id)

    return render_template("partials/profile_orgs.html", organizations=organizations)


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


@app.route("/opportunity/<int:opp_id>", methods=["GET"])
@login_required
def opportunity_details(opp_id: int):
    opp_details = get_opportunity_details(opp_id)

    return render_template("opportunityDetails.html", opp_details=opp_details)


@app.route("/organization/<int:org_id>", methods=["GET"])
@login_required
def organization_details(org_id: int):
    org_details = get_org_details(org_id)
    org_opportunities = get_all_current_opportunities_for_org(org_id)

    return render_template(
        "organizationDetails.html", org_details=org_details, org_opps=org_opportunities
    )


@app.route("/organization/create", methods=["GET", "POST"])
@login_required
def organization_create():
    if request.method == "POST":
        org_name = request.form["name"].strip()
        org_type = request.form["org_type"].strip()
        org_email = request.form["org_email"].strip()
        org_image = None
        org_image_url = ""
        org_rep_id = session["user_id"]

        # validate user input
        errors = []

        if not validate_not_empty(org_name, org_type, org_email):
            errors.append("Please enter data in all fields")

        if not validate_email(org_email):
            errors.append("Please enter a valid email")

        if "org_image" in request.files and request.files["org_image"].filename == "":
            errors.append("Please provide an image for the organization")

        if errors:
            for e in errors:
                flash(e)

            return render_template("partials/errorMessages.html")

        if get_org_by_name(org_name):
            flash("An organization with this name already exists, use a different name")
            return render_template("partials/errorMessages.html")

        if "org_image" in request.files:
            org_image = request.files["org_image"]
            try:
                org_image_url = upload_image(org_image)
            except Exception as e:
                flash("Error in image upload, try again")
                return render_template("partials/errorMessages.html")

        create_new_org(org_name, org_type, org_email, org_image_url, org_rep_id)

        response = make_response("")
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Organization created successfully",
                    "type": "success",
                }
            }
        )
        response.headers["HX-Redirect"] = url_for("profile", tab="orgs")
        return response

    return render_template("createOrganization.html")


# also check if the org belongs to this user
@app.route("/organization/manage/<int:org_id>", methods=["GET"])
@login_required
def organization_manage(org_id: int):
    org_details = get_org_details(org_id)

    return render_template("organizationManage.html", org_details=org_details)


@app.route("/organization/manage/<int:org_id>/opportunities", methods=["GET"])
@login_required
def organization_manage_opportunities(org_id: int):
    org_opportunities = get_all_current_opportunities_for_org(org_id)

    return render_template(
        "partials/org_manage_opportunities.html",
        org_opps=org_opportunities,
        org_id=org_id,
    )


@app.route("/organization/manage/<int:org_id>/signups", methods=["GET"])
@login_required
def organization_manage_signups(org_id: int):
    return "Hello"


@app.route("/organization/manage/<int:org_id>/add-opportunity", methods=["GET", "POST"])
@login_required
def opportunity_create(org_id: int):
    if request.method == "POST":
        print(request.form)

        opp_title = request.form["tile"].strip()
        opp_description = request.form["description"].strip()
        opp_start_date = request.form["startDate"].strip()
        opp_end_date = request.form["endDate"].strip()
        opp_max_signups = request.form["maxSignups"].strip()

        opp_image = None
        opp_image_url = ""

        # validate user input
        errors = []

        if not validate_not_empty(
                opp_title, opp_description, opp_start_date, opp_end_date, opp_max_signups
        ):
            errors.append("Please enter data in all fields")

        # check if description is provided (<p><br></p>)

        # check is the star_date and end_date are valid

        if "flyer" in request.files and request.files["flyer"].filename == "":
            errors.append("Please provide an image for the organization")

        if errors:
            for e in errors:
                flash(e)

            return render_template("partials/errorMessages.html")

        # check if opportunity already exists

        if "flyer" in request.files:
            opp_image = request.files["flyer"]
            try:
                opp_image_url = upload_image(opp_image)
            except Exception as e:
                flash("Error in image upload, try again")
                return render_template("partials/errorMessages.html")

        # create the new opportunity

        response = make_response("")
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Opportunity created successfully",
                    "type": "success",
                }
            }
        )
        response.headers["HX-Redirect"] = url_for("organization_manage")
        return response

    return render_template("addOpportunity.html", org_id=org_id)


@app.route("/signup/<int:signup_id>/delete", methods=["POST"])
@login_required
def signup_delete(signup_id: int):
    user_id = session["user_id"]

    print(signup_id)

    delete_user_signup(signup_id, user_id)
    return ""


if __name__ == "__main__":
    app.run(debug=True)
