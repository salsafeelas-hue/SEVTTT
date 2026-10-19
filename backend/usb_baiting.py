from flask import Blueprint, render_template, session, redirect, url_for, request
from database import get_db_connection
import random


# --------------------------------------------------
# USB BAITING BLUEPRINT
# --------------------------------------------------

usb_baiting = Blueprint("usb_baiting", __name__)


# --------------------------------------------------
# START USB BAITING SIMULATOR
# --------------------------------------------------

@usb_baiting.route("/usb-baiting")
@usb_baiting.route("/usb_baiting")
def start_usb_baiting():

    # Check whether the user is logged in
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Connect to database
    connection = get_db_connection()

    if connection is None:
        return "Database connection failed."

    cursor = connection.cursor(dictionary=True)

    try:

        # Get all USB Baiting scenarios
        cursor.execute("""
            SELECT *
            FROM usb_baiting_scenarios
        """)

        scenarios = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    # Make sure there are at least 2 scenarios
    if len(scenarios) < 2:
        return "Not enough USB Baiting scenarios in database."

    # Randomly select exactly 2 scenarios
    selected_scenarios = random.sample(scenarios, 2)

    # Store the selected scenarios in the user's session
    session["usb_scenarios"] = selected_scenarios
    session["usb_current"] = 0
    session["usb_score"] = 0
    session["usb_answers"] = []

    # Open the first scenario
    return redirect(url_for("usb_baiting.show_scenario"))


# --------------------------------------------------
# SHOW CURRENT USB BAITING SCENARIO
# --------------------------------------------------

@usb_baiting.route("/usb-baiting/scenario")
def show_scenario():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get selected scenarios
    scenarios = session.get("usb_scenarios")

    # If no scenarios exist, start a new attempt
    if not scenarios:
        return redirect(url_for("usb_baiting.start_usb_baiting"))

    # Get current scenario number
    current = session.get("usb_current", 0)

    # If all scenarios are completed
    if current >= len(scenarios):
        return redirect(url_for("usb_baiting.result"))

    # Get current scenario
    scenario = scenarios[current]

    # Display the scenario
    return render_template(
        "06 USBbaiting.html",
        scenario=scenario,
        current=current + 1,
        total=len(scenarios)
    )


# --------------------------------------------------
# SUBMIT USB BAITING ANSWER
# --------------------------------------------------

@usb_baiting.route("/usb-baiting/answer", methods=["POST"])
def submit_answer():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get scenarios from session
    scenarios = session.get("usb_scenarios", [])

    # Get current scenario number
    current = session.get("usb_current", 0)

    # If there are no scenarios or all are completed
    if not scenarios or current >= len(scenarios):
        return redirect(url_for("usb_baiting.result"))

    # Get current scenario
    scenario = scenarios[current]

    # Get selected answer from form
    selected_answer = request.form.get("answer")

    # Get correct answer from database
    correct_answer = scenario["correct_answer"]

    # Check answer
    if selected_answer == correct_answer:

        session["usb_score"] = session.get("usb_score", 0) + 1

        is_correct = True

    else:

        is_correct = False

    # Get previous answers
    answers = session.get("usb_answers", [])

    # Store this answer
    answers.append({
        "scenario_id": scenario["scenario_id"],
        "selected_answer": selected_answer,
        "correct_answer": correct_answer,
        "is_correct": is_correct,
        "explanation": scenario["explanation"]
    })

    # Save answers back into session
    session["usb_answers"] = answers

    # Move to the next scenario
    session["usb_current"] = current + 1

    # Show feedback
    return render_template(
        "usb_feedback.html",
        scenario=scenario,
        selected_answer=selected_answer,
        is_correct=is_correct,
        current=current + 1,
        total=len(scenarios)
    )


# --------------------------------------------------
# USB BAITING RESULT
# --------------------------------------------------

@usb_baiting.route("/usb-baiting/result")
@usb_baiting.route("/usb_baiting/result")
def result():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    # Get score
    score = session.get("usb_score", 0)

    # Total number of scenarios
    total = 2

    # --------------------------------------------------
    # CALCULATE PERCENTAGE
    # --------------------------------------------------

    percentage = round((score / total) * 100, 2)


    # --------------------------------------------------
    # DETERMINE RISK LEVEL
    # --------------------------------------------------

    if percentage >= 80:

        risk_level = "Low Risk"

    elif percentage >= 50:

        risk_level = "Moderate Risk"

    else:

        risk_level = "High Risk"


    # --------------------------------------------------
    # SAVE USB RESULT TO CONSOLIDATED ASSESSMENT
    # --------------------------------------------------

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        # Remove the previous consolidated USB result
        # so repeated attempts do not create duplicate
        # entries for the same module.

        cursor.execute("""
            DELETE FROM vulnerability_assessments
            WHERE user_id = %s
            AND module_name = %s
        """, (
            user_id,
            "USB Baiting"
        ))


        # Insert the latest USB Baiting result

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
            "USB Baiting",
            score,
            total,
            percentage,
            risk_level
        ))

        connection.commit()

    finally:

        cursor.close()
        connection.close()


    # --------------------------------------------------
    # EXISTING USB RESULT PAGE
    # --------------------------------------------------

        # --------------------------------------------------
    # USB BAITING INDIVIDUAL REPORT
    # --------------------------------------------------

    if percentage >= 80:

        feedback = (
            "Excellent USB security awareness. "
            "You demonstrated a strong ability to recognize "
            "suspicious USB devices and baiting attempts."
        )

    elif percentage >= 50:

        feedback = (
            "Your USB security awareness is moderate. "
            "Be more cautious when encountering unknown USB "
            "devices, storage media or unexpected files."
        )

    else:

        feedback = (
            "Your USB security awareness needs improvement. "
            "Never connect unknown USB devices to your computer "
            "without verifying their source and purpose."
        )


    return render_template(
        "19 report.html",
        module_name="USB Baiting",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk_level,
        feedback=feedback
    )