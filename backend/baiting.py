from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random


# =====================================================
# BAITING BLUEPRINT
# =====================================================

baiting = Blueprint("baiting", __name__)


# =====================================================
# START BAITING SIMULATOR
# =====================================================

@baiting.route("/baiting/start")
def start_baiting():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get all baiting scenarios
    cursor.execute("""
        SELECT *
        FROM baiting_scenarios
    """)

    all_scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    # Safety check
    if len(all_scenarios) < 3:
        return "Not enough baiting scenarios in database."

    # Select exactly 3 random scenarios
    scenarios = random.sample(all_scenarios, 3)

    # Store attempt in session
    session["baiting_scenarios"] = scenarios
    session["baiting_current"] = 0
    session["baiting_answers"] = []
    session["baiting_feedback"] = None

    # Clear previous result
    session.pop("baiting_score", None)
    session.pop("baiting_total", None)
    session.pop("baiting_percentage", None)
    session.pop("baiting_risk", None)
    session.pop("baiting_final_feedback", None)

    # Start simulator
    return redirect(url_for("baiting.baiting_page"))


# =====================================================
# BAITING SIMULATOR PAGE
# =====================================================

@baiting.route("/baiting", methods=["GET", "POST"])
def baiting_page():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get("baiting_scenarios", [])
    current = session.get("baiting_current", 0)
    answers = session.get("baiting_answers", [])

    # If no attempt exists, start one
    if not scenarios:
        return redirect(url_for("baiting.start_baiting"))

    # Safety check
    if current >= len(scenarios):
        return redirect(url_for("baiting.baiting_result"))

    # =================================================
    # PROCESS ANSWER
    # =================================================

    if request.method == "POST":

        user_answer = request.form.get("answer")

        # Make sure answer is valid
        if user_answer not in ["safe", "scam"]:
            return redirect(url_for("baiting.baiting_page"))

        current_scenario = scenarios[current]

        # Determine correct answer
        correct_answer = (
            "scam"
            if int(current_scenario["is_scam"]) == 1
            else "safe"
        )

        # Check answer
        is_correct = user_answer == correct_answer

        # Store answer
        answers.append({
            "scenario_id": current_scenario["scenario_id"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

        session["baiting_answers"] = answers

        # Store explanation for selected scenario
        session["baiting_feedback"] = {
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "explanation": current_scenario["explanation"]
        }

        # Move to next scenario
        current += 1
        session["baiting_current"] = current

        # =================================================
        # AFTER ALL 3 SCENARIOS
        # =================================================

        if current >= len(scenarios):

            score = sum(
                1
                for answer in answers
                if answer["is_correct"]
            )

            total = len(scenarios)

            percentage = int((score / total) * 100)

            # Risk level
            if percentage >= 80:
                risk = "Low Risk"

            elif percentage >= 50:
                risk = "Moderate Risk"

            else:
                risk = "High Risk"

            # Generate final feedback
            if percentage >= 80:

                feedback = (
                    "You demonstrated strong awareness of baiting techniques. "
                    "You were able to identify most suspicious situations correctly."
                )

            elif percentage >= 50:

                feedback = (
                    "You showed moderate awareness of baiting techniques. "
                    "Some suspicious situations may still require closer attention."
                )

            else:

                feedback = (
                    "Your responses indicate that you may be vulnerable to baiting techniques. "
                    "Be cautious with unexpected offers, devices, downloads and requests."
                )

            # Store final result
            session["baiting_score"] = score
            session["baiting_total"] = total
            session["baiting_percentage"] = percentage
            session["baiting_risk"] = risk
            session["baiting_final_feedback"] = feedback

            # Go to result
            return redirect(
                url_for("baiting.baiting_result")
            )

    # =================================================
    # DISPLAY CURRENT SCENARIO
    # =================================================

    if current >= len(scenarios):

        return redirect(
            url_for("baiting.baiting_result")
        )

    current_scenario = scenarios[current]

    # Get feedback from previous answer
    feedback = session.get("baiting_feedback")

    # Clear feedback after reading it
    session["baiting_feedback"] = None

    return render_template(
        "09 baiting.html",
        scenario=current_scenario,
        question_number=current + 1,
        total_questions=len(scenarios),
        feedback=feedback
    )


# =====================================================
# BAITING RESULT PAGE
# =====================================================

@baiting.route("/baiting/result")
def baiting_result():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get result
    score = session.get("baiting_score", 0)
    total = session.get("baiting_total", 3)
    percentage = session.get("baiting_percentage", 0)
    risk = session.get("baiting_risk", "High Risk")

    feedback = session.get(
        "baiting_final_feedback",
        "Baiting simulation completed."
    )

    # =================================================
    # SAVE RESULT TO CONSOLIDATED ASSESSMENT
    # =================================================

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Remove previous Baiting result
        # so repeated attempts do not create duplicates.

        cursor.execute("""
            DELETE FROM vulnerability_assessments
            WHERE user_id = %s
            AND module_name = %s
        """, (
            user_id,
            "Baiting Simulator"
        ))

        # Insert latest Baiting result

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
            "Baiting Simulator",
            score,
            total,
            percentage,
            risk
        ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()

    # =================================================
    # INDIVIDUAL BAITING REPORT
    # =================================================

    return render_template(
        "19 report.html",
        module_name="Baiting Simulator",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )