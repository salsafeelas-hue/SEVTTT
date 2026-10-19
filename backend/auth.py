from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection

auth = Blueprint("auth", __name__)


# ----------------------------
# REGISTER
# ----------------------------
@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("auth.register"))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s OR username=%s",
            (email, username)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            flash("Email or Username already exists!", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (full_name, username, email, password)
            VALUES (%s, %s, %s, %s)
        """, (
            full_name,
            username,
            email,
            hashed_password
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Registration Successful!", "success")

        return redirect(url_for("auth.login"))

    return render_template("03 reg.html")


# ----------------------------
# LOGIN
# ----------------------------
@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:

            if check_password_hash(user["password"], password):

                session["logged_in"] = True
                session["user_id"] = user["user_id"]
                session["full_name"] = user["full_name"]
                session["username"] = user["username"]

                flash("Login Successful!", "success")

                return redirect(url_for("dashboard.dashboard_page"))

        flash("Invalid Email or Password!", "danger")

        return redirect(url_for("auth.login"))

    return render_template("02 login.html")


# ----------------------------
# LOGOUT
# ----------------------------
@auth.route("/logout")
def logout():

    session.clear()

    flash("Logged Out Successfully!", "success")

    return redirect(url_for("home"))