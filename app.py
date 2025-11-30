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
    get_opportunity_for_org_by_title,
    create_new_opportunity,
    get_all_signups_for_org,
    delete_user_signup,
    get_signup_by_user_and_opp,
    create_new_signup,
    get_signup_count_for_opp,
    get_max_signups,
    update_org,
    delete_org,
    delete_opp,
)
from utils.auth import (
    compare_password,
    hash_password,
    login_required,
    is_representative,
    is_authorized_to_delete_signup,
)
from utils.image_uploader import upload_image
from utils.validator import (
    validate_email,
    validate_not_empty,
    validate_net_id,
    validate_password,
    validate_role,
    validate_description,
    validate_date,
    validate_start_end_dates,
    validate_max_signups,
    compare_date_with_today,
)

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("SECRET_KEY")


# @app.before_request
# def debug_request():
#     print(request.method, request.path)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("AboutUs.html")


@app.route("/internshipApply")
def apply_internship():
    return render_template("apply_forms/internshipApply.html")


@app.route("/scholarshipApply")
def apply_scholarship():
    return render_template("apply_forms/scholarshipApply.html")


@app.route("/researchApply")
def apply_research():
    return render_template("apply_forms/researchApply.html")


@app.route("/eventApply")
def apply_event():
    return render_template("apply_forms/eventApply.html")


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
                flash(e, "error")

            return render_template("partials/flash_messages.html")

        # check if user exists in db
        user = get_user_by_email(email)
        if not user:
            flash("Invalid Credentials", "error")
            return render_template("partials/flash_messages.html")

        # compare the user's password
        if not compare_password(password, user["password"]):
            flash("Invalid Credentials", "error")
            return render_template("partials/flash_messages.html")

        # add user data to session
        session["user_id"] = user["user_id"]
        session["name"] = user["first_name"]

        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "Welcome back",
                        "type": "success",
                    }
                }
            )
            response.headers["HX-Redirect"] = url_for("dashboard")
            return response

        flash("Welcome back", "success")
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
                flash(e, "error")

            return render_template("partials/flash_messages.html")

        # check if the user already exists in db
        if get_user_by_email(email) or get_user_by_net_id(net_id):
            flash("The user already exists", "error")
            return render_template("partials/flash_messages.html")

        # hash the user's password
        hashed_password = hash_password(password).decode("utf-8")

        # insert the user into the users table and store the user id
        user_id = create_new_user(
            first_name, last_name, net_id, email, hashed_password, role
        )

        # add user data to session
        session["user_id"] = user_id
        session["name"] = first_name

        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "Account created successfully",
                        "type": "success",
                    }
                }
            )
            response.headers["HX-Redirect"] = url_for("dashboard")
            return response

        flash("Account created successfully", "success")
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
                flash(e, "error")

            return render_template("partials/flash_messages.html")

        if get_org_by_name(org_name):
            flash(
                "An organization with this name already exists, use a different name",
                "error",
            )
            return render_template("partials/flash_messages.html")

        if "org_image" in request.files:
            org_image = request.files["org_image"]
            try:
                org_image_url = upload_image(org_image)
            except Exception as e:
                flash("Error in image upload, try again", "error")
                return render_template("partials/flash_messages.html")

        create_new_org(org_name, org_type, org_email, org_image_url, org_rep_id)

        if request.headers.get("HX-Request"):
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

        flash("Organization created successfully", "success")
        return redirect(url_for("profile", tab="orgs"))

    return render_template("createOrganization.html")


@app.route("/organization/update/<int:org_id>", methods=["GET", "POST"])
@login_required
@is_representative
def organization_update(org_id: int):
    org_details = get_org_details(org_id)

    if not org_details:
        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "That organization does not exist",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("That organization does not exist", "error")
        return redirect(url_for("profile", tab="orgs"))

    if request.method == "POST":
        org_name = request.form["name"].strip()
        org_type = request.form["org_type"].strip()
        org_email = request.form["org_email"].strip()
        org_image = None
        org_image_url = ""

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
                flash(e, "error")

            return render_template("partials/flash_messages.html")

        if get_org_by_name(org_name) and org_name != org_details["org_name"]:
            flash(
                "An organization with this name already exists, use a different name",
                "error",
            )
            return render_template("partials/flash_messages.html")

        if "org_image" in request.files:
            org_image = request.files["org_image"]
            try:
                org_image_url = upload_image(org_image)
            except Exception as e:
                flash("Error in image upload, try again", "error")
                return render_template("partials/flash_messages.html")
        else:
            org_image_url = org_details["org_image_url"]

        if (
                org_name == org_details["org_name"]
                and org_type == org_details["org_type"]
                and org_email == org_details["org_email"]
                and org_image_url == org_details["org_image_url"]
        ):
            flash("You have not made any changes", "warning")
            return render_template("partials/flash_messages.html")

        update_org(org_name, org_type, org_email, org_image_url, org_id)

        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "Organization updated successfully",
                        "type": "success",
                    }
                }
            )
            response.headers["HX-Redirect"] = url_for("profile", tab="orgs")
            return response

        flash("Organization updated successfully", "success")
        return redirect(url_for("profile", tab="orgs"))

    return render_template("organization_update.html", org=org_details)


@app.route("/organization/delete-confirm/<int:org_id>", methods=["GET"])
@login_required
@is_representative
def organization_delete_confirmation(org_id: int):
    org_details = get_org_details(org_id)

    if not org_details:
        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "That organization does not exist",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("That organization does not exist", "error")
        return redirect(url_for("profile", tab="orgs"))

    return render_template("organization_delete_confirmation.html", org=org_details)


@app.delete("/organization/delete/<int:org_id>")
@login_required
@is_representative
def organization_delete(org_id: int):
    org_details = get_org_details(org_id)

    if not org_details:
        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "That organization does not exist",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("That organization does not exist", "error")
        return redirect(url_for("profile", tab="orgs"))

    delete_org(org_id)

    if request.headers.get("HX-Request"):
        response = make_response("")
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Organization deleted successfully",
                    "type": "success",
                }
            }
        )
        response.headers["HX-Redirect"] = url_for("profile", tab="orgs")
        return response

    flash("Organization deleted successfully", "success")
    return redirect(url_for("profile", tab="orgs"))


@app.route("/organization/manage/<int:org_id>", methods=["GET"])
@login_required
@is_representative
def organization_manage(org_id: int):
    org_details = get_org_details(org_id)

    return render_template("organizationManage.html", org_details=org_details)


@app.route("/organization/manage/<int:org_id>/opportunities", methods=["GET"])
@login_required
@is_representative
def organization_manage_opportunities(org_id: int):
    org_opportunities = get_all_current_opportunities_for_org(org_id)

    for opp in org_opportunities:
        total_signups = get_signup_count_for_opp(opp["opp_id"])
        opp["total_signups"] = total_signups

    return render_template(
        "partials/org_manage_opportunities.html",
        org_opps=org_opportunities,
        org_id=org_id,
    )


@app.route("/organization/manage/<int:org_id>/signups", methods=["GET"])
@login_required
@is_representative
def organization_manage_signups(org_id: int):
    signups = get_all_signups_for_org(org_id)

    # group by opportunities
    opportunities = {}
    for s in signups:
        opp_id = s["opp_id"]

        if opp_id not in opportunities:
            opportunities[opp_id] = {
                "opp_id": opp_id,
                "title": s["title"],
                "start_date": s["start_date"],
                "end_date": s["end_date"],
                "signups": [],
            }

        if s["signup_id"] is not None:
            opportunities[opp_id]["signups"].append(
                {
                    "signup_id": s["signup_id"],
                    "signup_date": s["signup_date"],
                    "status": s["status"],
                    "user": {
                        "user_id": s["user_id"],
                        "first_name": s["first_name"],
                        "last_name": s["last_name"],
                        "email": s["email"],
                    },
                }
            )

    return render_template(
        "partials/org_manage_signups.html", opportunities=opportunities.values()
    )


@app.route("/organization/manage/<int:org_id>/add-opportunity", methods=["GET", "POST"])
@login_required
@is_representative
def opportunity_create(org_id: int):
    if request.method == "POST":
        opp_title = request.form["tile"].strip()
        opp_category = request.form["category"].strip()
        opp_description = request.form["description"].strip()
        opp_start_date = request.form["startDate"].strip()
        opp_end_date = request.form["endDate"].strip()
        opp_max_signups = request.form["maxSignups"].strip()

        opp_image = None
        opp_image_url = ""

        # validate user input
        errors = []

        if not validate_not_empty(
                opp_title, opp_category, opp_description, opp_start_date
        ):
            errors.append("Please enter data in all fields")

        if not validate_description(opp_description):
            errors.append("Please provide a description for the opportunity")

        if not validate_date(opp_start_date):
            errors.append("Please provide valid Start date")

        if opp_end_date and not validate_date(opp_start_date):
            errors.append("Please provide valid End date")

        if "flyer" in request.files and request.files["flyer"].filename == "":
            errors.append("Please provide an image for the opportunity")

        if opp_max_signups and not validate_max_signups(opp_max_signups):
            errors.append("Maximum Signups needs to be an integer greater than 0")

        if errors:
            for e in errors:
                flash(e, "error")

            return render_template("partials/flash_messages.html")

        if opp_end_date:
            if not validate_start_end_dates(opp_start_date, opp_end_date):
                flash(
                    "The Start date cannot be greater than End date",
                    "error",
                )
                return render_template("partials/flash_messages.html")

            if not compare_date_with_today(
                    opp_start_date
            ) and not compare_date_with_today(opp_end_date):
                flash(
                    "You can only add future opportunities",
                    "error",
                )
                return render_template("partials/flash_messages.html")
        else:
            if not compare_date_with_today(opp_start_date):
                flash(
                    "You can only add future opportunities",
                    "error",
                )
                return render_template("partials/flash_messages.html")

        # check if opportunity already exists
        if get_opportunity_for_org_by_title(org_id, opp_title):
            flash(
                "An opportunity with this name already exists, use a different name",
                "error",
            )
            return render_template("partials/flash_messages.html")

        if "flyer" in request.files:
            opp_image = request.files["flyer"]
            try:
                opp_image_url = upload_image(opp_image)
            except Exception as e:
                flash("Error in image upload, try again")
                return render_template("partials/flash_messages.html")

        if not opp_end_date:
            opp_end_date = None

        if not opp_max_signups:
            opp_max_signups = None
        else:
            opp_max_signups = int(opp_max_signups)

        # create the new opportunity
        create_new_opportunity(
            opp_title,
            opp_image_url,
            opp_description,
            opp_category,
            opp_start_date,
            opp_end_date,
            opp_max_signups,
            org_id,
        )

        response = make_response("")
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Opportunity created successfully",
                    "type": "success",
                }
            }
        )
        response.headers["HX-Redirect"] = url_for("organization_manage", org_id=org_id)
        return response

    return render_template("addOpportunity.html", org_id=org_id)


@app.route(
    "/organization/manage/<int:opp_id>/update-opportunity", methods=["GET", "POST"]
)
@login_required
def opportunity_update(opp_id: int):
    opp_details = get_opportunity_details(opp_id)
    user_id = session["user_id"]

    if not opp_details:
        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "That opportunity does not exist",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("That opportunity does not exist", "error")
        return redirect(url_for("profile", tab="orgs"))

    if opp_details["org_rep_id"] != user_id:
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

    return ""


@app.route("/opportunity/delete-confirm/<int:opp_id>", methods=["GET"])
@login_required
def opportunity_delete_confirmation(opp_id: int):
    opp_details = get_opportunity_details(opp_id)
    user_id = session["user_id"]

    if not opp_details:
        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "That opportunity does not exist",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("That opportunity does not exist", "error")
        return redirect(url_for("profile", tab="orgs"))

    if opp_details["org_rep_id"] != user_id:
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

    return render_template("opportunity_delete_confirmation.html", opp=opp_details)


@app.delete("/opportunity/delete/<int:opp_id>")
@login_required
def opportunity_delete(opp_id: int):
    opp_details = get_opportunity_details(opp_id)
    user_id = session["user_id"]

    if not opp_details:
        if request.headers.get("HX-Request"):
            response = make_response("")
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "That opportunity does not exist",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("That opportunity does not exist", "error")
        return redirect(url_for("profile", tab="orgs"))

    if opp_details["org_rep_id"] != user_id:
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

    delete_opp(opp_id)

    if request.headers.get("HX-Request"):
        response = make_response("")
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Opportunity deleted successfully",
                    "type": "success",
                }
            }
        )
        response.headers["HX-Redirect"] = url_for(
            "organization_manage", org_id=opp_details["org_id"]
        )
        return response

    flash("Opportunity deleted successfully", "success")
    return redirect(url_for("organization_manage", org_id=opp_details["org_id"]))


@app.route("/signup/<int:opp_id>", methods=["POST"])
@login_required
def signup(opp_id: int):
    user_id = session["user_id"]

    if not get_opportunity_details(opp_id):
        flash("That opportunity does not exist", "error")
        return redirect(url_for("dashboard"))

    if get_signup_by_user_and_opp(user_id, opp_id):
        if request.headers.get("HX-Request"):
            response = make_response(
                render_template("partials/signup/already_registered.html")
            )
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "You have already registered for this opportunity",
                        "type": "warning",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash("You have already registered for this opportunity", "warning")
        return redirect(url_for("opportunity_details", opp_id=opp_id))

    signup_count = get_signup_count_for_opp(opp_id)
    max_signup_count = get_max_signups(opp_id)

    if max_signup_count and signup_count == max_signup_count:
        if request.headers.get("HX-Request"):
            response = make_response(
                render_template("partials/signup/full_capacity.html")
            )
            response.headers["HX-Trigger"] = json.dumps(
                {
                    "showToast": {
                        "message": "Cannot signup, this opportunity has reached its maximum signup capacity",
                        "type": "error",
                        "fromHTMX": True,
                    }
                }
            )
            return response

        flash(
            "Cannot signup, this opportunity has reached its maximum signup capacity",
            "error",
        )
        return redirect(url_for("opportunity_details", opp_id=opp_id))

    create_new_signup(user_id, opp_id)

    if request.headers.get("HX-Request"):
        response = make_response(render_template("partials/signup/success.html"))
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Signed up successfully",
                    "type": "success",
                    "fromHTMX": True,
                }
            }
        )
        return response

    flash("Signed up successfully", "success")
    return redirect(url_for("opportunity_details", opp_id=opp_id))


@app.route("/signup/<int:signup_id>/delete", methods=["POST"])
@login_required
@is_authorized_to_delete_signup
def signup_delete(signup_id: int):
    delete_user_signup(signup_id)

    if request.headers.get("HX-Request"):
        response = make_response("")
        response.headers["HX-Trigger"] = json.dumps(
            {
                "showToast": {
                    "message": "Signup deleted successfully",
                    "type": "success",
                    "fromHTMX": True,
                }
            }
        )
        return response

    flash("Signup deleted successfully", "success")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True)
