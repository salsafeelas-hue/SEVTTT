from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random


fake_otp = Blueprint(
    "fake_otp",
    __name__
)


# ---------------------------------------------------------
# START FAKE OTP SIMULATOR
# ---------------------------------------------------------

@fake_otp.route("/fake-otp/start")
def start_fake_otp():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT scenario_id
        FROM fake_otp_scenarios
    """)

    all_scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(all_scenarios) < 3:
        return "Not enough fake OTP scenarios in database."

    # Select 3 random scenario IDs
    selected = random.sample(all_scenarios, 3)

    scenario_ids = [
        row["scenario_id"]
        for row in selected
    ]

    # Store ONLY IDs in session
    # This prevents the Flask session cookie
    # from becoming too large.
    session["fake_otp_scenario_ids"] = scenario_ids
    session["fake_otp_current"] = 0
    session["fake_otp_answers"] = []

    # Remove old data if it exists
    session.pop("fake_otp_scenarios", None)
    session.pop("fake_otp_score", None)
    session.pop("fake_otp_total", None)
    session.pop("fake_otp_percentage", None)
    session.pop("fake_otp_risk", None)
    session.pop("fake_otp_feedback", None)

    return redirect(
        url_for("fake_otp.fake_otp_page")
    )


# ---------------------------------------------------------
# FAKE OTP QUESTIONS
# ---------------------------------------------------------

@fake_otp.route(
    "/fake-otp",
    methods=["GET", "POST"]
)
def fake_otp_page():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    scenario_ids = session.get(
        "fake_otp_scenario_ids",
        []
    )

    current = session.get(
        "fake_otp_current",
        0
    )

    answers = session.get(
        "fake_otp_answers",
        []
    )

    # If no simulation has started
    if not scenario_ids:
        return redirect(
            url_for("fake_otp.start_fake_otp")
        )

    # -----------------------------------------------------
    # GET CURRENT SCENARIO FROM DATABASE
    # -----------------------------------------------------

    if current >= len(scenario_ids):

        return redirect(
            url_for("fake_otp.fake_otp_result")
        )

    current_id = scenario_ids[current]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM fake_otp_scenarios
        WHERE scenario_id = %s
    """, (current_id,))

    current_scenario = cursor.fetchone()

    cursor.close()
    conn.close()

    if not current_scenario:
        return "Fake OTP scenario not found."

    # -----------------------------------------------------
    # PROCESS USER ANSWER
    # -----------------------------------------------------

    if request.method == "POST":

        user_answer = request.form.get("answer")

        if user_answer not in [
            "1",
            "2",
            "3"
        ]:
            return redirect(
                url_for(
                    "fake_otp.fake_otp_page"
                )
            )

        correct_answer = str(
            current_scenario["correct_action"]
        )

        is_correct = (
            user_answer == correct_answer
        )

        answers.append({
            "scenario_id":
                current_scenario["scenario_id"],

            "user_answer":
                user_answer,

            "correct_answer":
                correct_answer,

            "is_correct":
                is_correct
        })

        session["fake_otp_answers"] = answers

        # Move to next scenario
        current += 1

        session["fake_otp_current"] = current

        # -------------------------------------------------
        # FINISHED ALL 3 QUESTIONS
        # -------------------------------------------------

        if current >= len(scenario_ids):

            score = sum(
                1
                for answer in answers
                if answer["is_correct"]
            )

            total = len(scenario_ids)

            percentage = int(
                (score / total) * 100
            )

            # Risk
            if percentage >= 80:

                risk = "Low Risk"

            elif percentage >= 50:

                risk = "Moderate Risk"

            else:

                risk = "High Risk"

            # Feedback
            if percentage >= 80:

                feedback = (
                    "You demonstrated strong awareness "
                    "of OTP-based social engineering. "
                    "You correctly recognized suspicious "
                    "requests and understood that OTPs "
                    "should never be disclosed to another "
                    "person."
                )

            elif percentage >= 50:

                feedback = (
                    "You demonstrated moderate awareness "
                    "of OTP security. Be more careful when "
                    "someone asks you to provide an OTP, "
                    "especially when the request creates "
                    "urgency or comes from an unexpected "
                    "caller or message."
                )

            else:

                feedback = (
                    "Your responses indicate that you may "
                    "be vulnerable to OTP-based social "
                    "engineering. Never disclose OTPs to "
                    "callers, support representatives or "
                    "unknown people. Verify requests "
                    "through official channels."
                )

            # Store only small values in session
            session["fake_otp_score"] = score
            session["fake_otp_total"] = total
            session["fake_otp_percentage"] = percentage
            session["fake_otp_risk"] = risk
            session["fake_otp_feedback"] = feedback

            return redirect(
                url_for(
                    "fake_otp.fake_otp_result"
                )
            )

    # -----------------------------------------------------
    # DISPLAY QUESTION
    # -----------------------------------------------------

    return render_template(
        "13 fakeotp.html",
        scenario=current_scenario,
        question_number=current + 1,
        total_questions=len(scenario_ids)
    )


# ---------------------------------------------------------
# FAKE OTP RESULT / REPORT
# ---------------------------------------------------------

@fake_otp.route(
    "/fake-otp/result"
)
def fake_otp_result():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    score = session.get(
        "fake_otp_score",
        0
    )

    total = session.get(
        "fake_otp_total",
        3
    )

    percentage = session.get(
        "fake_otp_percentage",
        0
    )

    risk = session.get(
        "fake_otp_risk",
        "High Risk"
    )

    feedback = session.get(
        "fake_otp_feedback",
        "OTP security simulation completed."
    )

    return render_template(
        "19 report.html",
        module_name="Fake OTP Request",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )