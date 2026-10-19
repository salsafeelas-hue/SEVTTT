from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random


fakejoboff_bp = Blueprint("fakejoboff", __name__)


# -------------------------------------------------
# START FAKE JOB OFFER SIMULATOR
# -------------------------------------------------
@fakejoboff_bp.route("/fakejoboff/start")
def start_fakejoboff():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM fake_job_scenarios
        ORDER BY RAND()
        LIMIT 3
    """)

    scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(scenarios) < 3:
        return "Not enough Fake Job Offer scenarios in database."

    # Store selected scenarios in session
    session["fakejob_scenarios"] = scenarios
    session["fakejob_current"] = 0
    session["fakejob_answers"] = []
    session.pop("fakejob_score", None)

    return redirect(url_for("fakejoboff.fakejoboff_page"))


# -------------------------------------------------
# FAKE JOB OFFER PAGE
# -------------------------------------------------
@fakejoboff_bp.route("/fakejoboff", methods=["GET", "POST"])
def fakejoboff_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get("fakejob_scenarios", [])
    current = session.get("fakejob_current", 0)
    answers = session.get("fakejob_answers", [])

    # If no scenarios exist, start a new attempt
    if not scenarios:
        return redirect(url_for("fakejoboff.start_fakejoboff"))

    # Safety check
    if current >= len(scenarios):
        return redirect(url_for("fakejoboff.fakejob_result"))

    # -------------------------------------------------
    # PROCESS ANSWER
    # -------------------------------------------------
    if request.method == "POST":

        user_answer = request.form.get("answer")

        current_scenario = scenarios[current]

        correct_answer = (
            "scam" if int(current_scenario["is_scam"]) == 1
            else "safe"
        )

        is_correct = user_answer == correct_answer

        answers.append({
            "scenario_id": current_scenario["scenario_id"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

        session["fakejob_answers"] = answers

        # Move to next scenario
        current += 1
        session["fakejob_current"] = current

        # -------------------------------------------------
        # AFTER ALL 3 SCENARIOS
        # -------------------------------------------------
        if current >= len(scenarios):

            score = sum(
                1
                for answer in answers
                if answer["is_correct"]
            )

            session["fakejob_score"] = score

            return redirect(
                url_for("fakejoboff.fakejob_result")
            )

    # -------------------------------------------------
    # DISPLAY CURRENT SCENARIO
    # -------------------------------------------------
    current_scenario = scenarios[current]

    return render_template(
        "07 fakejoboff.html",
        scenario=current_scenario,
        question_number=current + 1,
        total_questions=len(scenarios)
    )


# -------------------------------------------------
# RESULT PAGE
# -------------------------------------------------
@fakejoboff_bp.route("/fakejoboff/result")
def fakejob_result():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    score = session.get("fakejob_score", 0)

    scenarios = session.get("fakejob_scenarios", [])

    total = len(scenarios)

    # -------------------------------------------------
    # CALCULATE PERCENTAGE
    # -------------------------------------------------

    if total > 0:

        percentage = round(
            (score / total) * 100,
            2
        )

    else:

        percentage = 0


    # -------------------------------------------------
    # DETERMINE RISK
    # -------------------------------------------------

    if percentage >= 80:

        risk = "Low Risk"

    elif percentage >= 50:

        risk = "Moderate Risk"

    else:

        risk = "High Risk"


    # -------------------------------------------------
    # FEEDBACK
    # -------------------------------------------------

    if percentage >= 80:

        feedback = (
            "Excellent job-offer scam awareness. "
            "You demonstrated a strong ability to identify "
            "fraudulent employment opportunities."
        )

    elif percentage >= 50:

        feedback = (
            "Your job-offer scam awareness is moderate. "
            "Pay closer attention to unusual payment requests, "
            "unrealistic offers and requests for sensitive information."
        )

    else:

        feedback = (
            "Your job-offer scam awareness needs improvement. "
            "Be cautious of unsolicited job offers, unrealistic salaries, "
            "upfront payments and requests for personal information."
        )


    # -------------------------------------------------
    # SAVE RESULT TO CONSOLIDATED ASSESSMENT
    # -------------------------------------------------

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Remove previous Fake Job Offer result
        # so repeated attempts do not create duplicates.

        cursor.execute("""
            DELETE FROM vulnerability_assessments
            WHERE user_id = %s
            AND module_name = %s
        """, (
            user_id,
            "Fake Job Offer Simulator"
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
            "Fake Job Offer Simulator",
            score,
            total,
            percentage,
            risk
        ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


    # -------------------------------------------------
    # INDIVIDUAL REPORT
    # -------------------------------------------------

    return render_template(
        "19 report.html",
        module_name="Fake Job Offer Simulator",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )
        