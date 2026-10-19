from flask import Blueprint, render_template, session, redirect, url_for

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/dashboard")
def dashboard_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "04 dashboard.html",
        username=session.get("username"),
        full_name=session.get("full_name")
    )