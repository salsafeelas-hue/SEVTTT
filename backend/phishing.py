import random

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for
)

from database import get_db_connection


phishing_bp = Blueprint(
    "phishing",
    __name__
)


# ---------------------------------
# Get 3 Random Scenarios
# ---------------------------------

def get_random_scenarios():

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM phishing_scenarios
        ORDER BY RAND()
        LIMIT 3
    """)

    scenarios = cursor.fetchall()

    cursor.close()
    connection.close()

    return scenarios


# ---------------------------------
# Start Phishing Module
# ---------------------------------

@phishing_bp.route("/phishing/start")
def start_phishing():

    # Make sure user is logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = get_random_scenarios()

    if len(scenarios) < 3:
        return "Not enough phishing scenarios available."

    session["phishing_scenarios"] = scenarios
    session["current_question"] = 0

    return redirect(url_for("phishing.show_question"))


# ---------------------------------
# Display Current Question
# ---------------------------------

@phishing_bp.route("/phishing")
def show_question():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get("phishing_scenarios")

    if not scenarios:
        return redirect(url_for("phishing.start_phishing"))

    current = session.get("current_question", 0)

    if current >= len(scenarios):
        return redirect(url_for("phishing.complete_phishing"))

    scenario = scenarios[current]

    return render_template(
        "05 phishing.html",
        scenario=scenario,
        question_number=current + 1,
        total_questions=len(scenarios)
    )


# ---------------------------------
# Submit Answer
# ---------------------------------

@phishing_bp.route("/phishing/submit", methods=["POST"])
def submit_answer():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get("phishing_scenarios")

    if not scenarios:
        return redirect(url_for("phishing.start_phishing"))

    current = session.get("current_question", 0)

    if current >= len(scenarios):
        return redirect(url_for("phishing.complete_phishing"))

    scenario = scenarios[current]

    user_answer = request.form.get("answer")

    is_correct = (
        user_answer == scenario["correct_answer"]
    )

    connection = get_db_connection()
    cursor = connection.cursor()

    # ---------------------------------
    # Save individual answer
    # ---------------------------------

    cursor.execute("""
        INSERT INTO phishing_results
        (user_id, scenario_id, user_answer, is_correct)
        VALUES (%s, %s, %s, %s)
    """, (
        session["user_id"],
        scenario["scenario_id"],
        user_answer,
        is_correct
    ))

    connection.commit()

    cursor.close()
    connection.close()

    # Move to next question
    session["current_question"] = current + 1

    # ---------------------------------
    # If all 3 questions completed
    # ---------------------------------

    if session["current_question"] >= len(scenarios):

        session.pop("phishing_scenarios", None)
        session.pop("current_question", None)

        return redirect(
            url_for("phishing.complete_phishing")
        )

    return redirect(
        url_for("phishing.show_question")
    )


# ---------------------------------
# Completion Page
# ---------------------------------

@phishing_bp.route("/phishing/completed")
def complete_phishing():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # ---------------------------------
    # Get the latest 3 phishing answers
    # ---------------------------------

    cursor.execute("""
        SELECT
            is_correct
        FROM phishing_results
        WHERE user_id = %s
        ORDER BY result_id DESC
        LIMIT 3
    """, (user_id,))

    results = cursor.fetchall()

    # ---------------------------------
    # Calculate score
    # ---------------------------------

    score = sum(
        1
        for result in results
        if result["is_correct"]
    )

    total = len(results)

    if total > 0:
        percentage = round(
            (score / total) * 100,
            2
        )
    else:
        percentage = 0


    # ---------------------------------
    # Determine risk level
    # ---------------------------------

    if percentage >= 80:

        risk_level = "Low Risk"

    elif percentage >= 50:

        risk_level = "Moderate Risk"

    else:

        risk_level = "High Risk"


    # ---------------------------------
    # Save consolidated result
    # ---------------------------------

    if total > 0:

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
            "Phishing Attack",
            score,
            total,
            percentage,
            risk_level
        ))

        connection.commit()


    cursor.close()
    connection.close()


    # ---------------------------------
    # Existing completion page
    # ---------------------------------

       # ---------------------------------
    # Phishing Individual Report
    # ---------------------------------

    if percentage >= 80:
        feedback = (
            "Excellent phishing awareness. "
            "You demonstrated a strong ability to identify "
            "suspicious emails and social engineering attempts."
        )

    elif percentage >= 50:
        feedback = (
            "Your phishing awareness is moderate. "
            "Pay closer attention to suspicious senders, "
            "unexpected requests and unusual links."
        )

    else:
        feedback = (
            "Your phishing awareness needs improvement. "
            "Always verify the sender, inspect links carefully "
            "and avoid responding to unexpected requests."
        )


    return render_template(
        "19 report.html",
        module_name="Phishing Attack",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk_level,
        feedback=feedback
    )