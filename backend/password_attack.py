from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection


password_attack = Blueprint("password_attack", __name__)


# =========================================================
# PASSWORD ATTACK SIMULATOR
# =========================================================

@password_attack.route("/password-attack", methods=["GET", "POST"])
def password_attack_page():

    # Check whether user is logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # -----------------------------
    # SHOW PASSWORD SIMULATOR
    # -----------------------------
    if request.method == "GET":
        return render_template("08 passwordattack.html")

    # -----------------------------
    # GET PASSWORD FROM FRONTEND
    # -----------------------------
    password = request.form.get("password", "").strip()

    if not password:
        return render_template(
            "08 passwordattack.html",
            error="Please enter a password to analyze."
        )

    # -----------------------------
    # INITIAL VALUES
    # -----------------------------
    score = 0
    findings = []

    # -----------------------------
    # 1. PASSWORD LENGTH
    # -----------------------------
    length = len(password)

    if length >= 16:
        score += 30

    elif length >= 12:
        score += 25

    elif length >= 8:
        score += 15

    elif length >= 6:
        score += 5

    else:
        findings.append(
            "Password is too short."
        )

    # -----------------------------
    # 2. LOWERCASE CHECK
    # -----------------------------
    if any(character.islower() for character in password):
        score += 10
    else:
        findings.append(
            "Password does not contain lowercase letters."
        )

    # -----------------------------
    # 3. UPPERCASE CHECK
    # -----------------------------
    if any(character.isupper() for character in password):
        score += 10
    else:
        findings.append(
            "Password does not contain uppercase letters."
        )

    # -----------------------------
    # 4. NUMBER CHECK
    # -----------------------------
    if any(character.isdigit() for character in password):
        score += 10
    else:
        findings.append(
            "Password does not contain numbers."
        )

    # -----------------------------
    # 5. SPECIAL CHARACTER CHECK
    # -----------------------------
    special_characters = "!@#$%^&*()-_=+[]{};:,.<>?/"

    if any(
        character in special_characters
        for character in password
    ):
        score += 15
    else:
        findings.append(
            "Password does not contain special characters."
        )

    # -----------------------------
    # 6. COMMON PASSWORD CHECK
    # -----------------------------
    common_passwords = [
        "password",
        "password123",
        "123456",
        "12345678",
        "qwerty",
        "qwerty123",
        "admin",
        "welcome",
        "letmein",
        "iloveyou"
    ]

    if password.lower() in common_passwords:

        score -= 30

        findings.append(
            "Password matches a commonly used password."
        )

    # -----------------------------
    # 7. REPEATED CHARACTER CHECK
    # -----------------------------
    repeated_characters = False

    if len(password) >= 3:

        for i in range(len(password) - 2):

            if (
                password[i]
                == password[i + 1]
                == password[i + 2]
            ):
                repeated_characters = True
                break

    if repeated_characters:

        score -= 10

        findings.append(
            "Password contains repeated characters."
        )

    # -----------------------------
    # 8. SEQUENTIAL NUMBER CHECK
    # -----------------------------
    sequential_patterns = [
        "123",
        "234",
        "345",
        "456",
        "567",
        "678",
        "789",
        "890"
    ]

    if any(
        pattern in password
        for pattern in sequential_patterns
    ):

        score -= 10

        findings.append(
            "Password contains sequential numbers."
        )

    # -----------------------------
    # 9. COMMON WORD CHECK
    # -----------------------------
    password_lower = password.lower()

    common_words = [
        "admin",
        "user",
        "name",
        "password"
    ]

    for word in common_words:

        if word in password_lower:

            score -= 5

            findings.append(
                "Password contains a predictable common word."
            )

            break

    # -----------------------------
    # KEEP SCORE BETWEEN 0 AND 100
    # -----------------------------
    score = max(0, min(score, 100))

    # -----------------------------
    # DETERMINE PASSWORD STRENGTH
    # -----------------------------
    if score < 20:

        strength = "VERY WEAK"
        risk = "HIGH RISK"

    elif score < 40:

        strength = "WEAK"
        risk = "HIGH RISK"

    elif score < 60:

        strength = "MODERATE"
        risk = "MEDIUM RISK"

    elif score < 80:

        strength = "STRONG"
        risk = "LOW RISK"

    else:

        strength = "VERY STRONG"
        risk = "LOW RISK"

    # -----------------------------
    # ATTACK SIMULATION RESULTS
    # -----------------------------
    attack_results = {

        "dictionary_attack":
            "VULNERABLE"
            if score < 40
            else "RESISTANT",

        "pattern_guessing":
            "VULNERABLE"
            if score < 50
            else "RESISTANT",

        "password_reuse":
            "HIGH RISK"
            if score < 50
            else "LOW RISK",

        "brute_force":
            "HIGH RISK"
            if length < 8
            else "LOWER RISK"
    }

    # -----------------------------
    # FEEDBACK
    # -----------------------------
    if not findings:

        feedback = (
            "No major password weaknesses were detected. "
            "Continue using unique passwords and never reuse "
            "the same password across important accounts."
        )

    else:

        feedback = " ".join(findings)

    # -----------------------------
    # SAVE RESULT IN SESSION
    # -----------------------------
    session["password_attack_result"] = {

        "score": score,
        "strength": strength,
        "risk": risk,
        "findings": findings,
        "attack_results": attack_results,
        "feedback": feedback
    }

    # -----------------------------
    # GO TO REPORT
    # -----------------------------
    return redirect(
        url_for(
            "password_attack.password_attack_result"
        )
    )


# =========================================================
# PASSWORD ATTACK REPORT
# =========================================================

@password_attack.route("/password-attack/result")
def password_attack_result():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get result
    result = session.get(
        "password_attack_result"
    )

    # If no result exists
    if not result:

        return redirect(
            url_for(
                "password_attack.password_attack_page"
            )
        )

    # -----------------------------------------------------
    # SAVE RESULT TO CONSOLIDATED ASSESSMENT
    # -----------------------------------------------------

    user_id = session["user_id"]

    score = result["score"]

    # Password simulator score is already out of 100
    total = 100

    percentage = score

    # Convert the existing password risk into
    # the standard consolidated risk format.

    if percentage >= 80:

        consolidated_risk = "Low Risk"

    elif percentage >= 50:

        consolidated_risk = "Moderate Risk"

    else:

        consolidated_risk = "High Risk"


    # -----------------------------------------------------
    # SAVE TO DATABASE
    # -----------------------------------------------------

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Remove previous Password Attack result
        # so repeated attempts do not create duplicates.

        cursor.execute("""
            DELETE FROM vulnerability_assessments
            WHERE user_id = %s
            AND module_name = %s
        """, (
            user_id,
            "Password Attack Simulator"
        ))


        # Insert latest result

        cursor.execute("""
            INSERT INTO vulnerability_assessments
            (
                user_id,
                module_name,
                score,
                total,
                percentage,
                risk_level
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            "Password Attack Simulator",
            score,
            total,
            percentage,
            consolidated_risk
        ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


    # -----------------------------------------------------
    # DISPLAY EXISTING SEVT REPORT
    # -----------------------------------------------------

        return render_template(
        "19 report.html",

        module_name="Password Attack Simulator",

        score=result["score"],

        total=100,

        total_marks=100,

        percentage=result["score"],

        risk=result["risk"],

        feedback=result["feedback"],

        strength=result["strength"],

        attack_results=result["attack_results"]
    )