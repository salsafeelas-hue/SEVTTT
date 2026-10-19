from flask import Blueprint, render_template, redirect, url_for, session, request
import mysql.connector
import random

url_inspection = Blueprint("url_inspection", __name__)


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="safii5858",
        database="sevt_db"
    )


# ---------------------------------------------------------
# START URL INSPECTION
# ---------------------------------------------------------
@url_inspection.route("/url-inspection/start")
def start_url_inspection():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT scenario_id
        FROM url_inspection_scenarios
    """)

    scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(scenarios) < 3:
        return "Not enough URL inspection scenarios in database."

    # Select 3 random scenarios
    selected = random.sample(scenarios, 3)

    scenario_ids = [
        scenario["scenario_id"]
        for scenario in selected
    ]

    # Store only IDs in session
    session["url_inspection_scenario_ids"] = scenario_ids
    session["url_inspection_current"] = 0
    session["url_inspection_answers"] = []

    # Clear previous result
    session.pop("url_inspection_score", None)
    session.pop("url_inspection_total", None)
    session.pop("url_inspection_percentage", None)
    session.pop("url_inspection_risk", None)
    session.pop("url_inspection_feedback", None)

    return redirect(url_for("url_inspection.url_inspection_page"))


# ---------------------------------------------------------
# URL INSPECTION QUESTIONS
# ---------------------------------------------------------
@url_inspection.route("/url-inspection", methods=["GET", "POST"])
def url_inspection_page():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenario_ids = session.get("url_inspection_scenario_ids")

    if not scenario_ids:
        return redirect(url_for("url_inspection.start_url_inspection"))

    current = session.get("url_inspection_current", 0)

    # Make sure current question exists
    if current >= len(scenario_ids):
        return redirect(url_for("url_inspection.url_inspection_result"))

    # -----------------------------------------------------
    # HANDLE ANSWER
    # -----------------------------------------------------
    if request.method == "POST":

        answer = request.form.get("answer")

        if answer not in ["1", "2", "3", "4"]:
            return redirect(
                url_for("url_inspection.url_inspection_page")
            )

        answer = int(answer)

        # Get current scenario
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT *
            FROM url_inspection_scenarios
            WHERE scenario_id = %s
        """, (scenario_ids[current],))

        scenario = cursor.fetchone()

        cursor.close()
        conn.close()

        if not scenario:
            return "Scenario not found."

        # Check answer
        is_correct = answer == scenario["correct_action"]

        session["url_inspection_answers"].append({
            "scenario_id": scenario["scenario_id"],
            "answer": answer,
            "correct": is_correct
        })

        session["url_inspection_current"] = current + 1

        # After 3 questions
        if session["url_inspection_current"] >= len(scenario_ids):

            answers = session["url_inspection_answers"]

            score = sum(
                1 for item in answers
                if item["correct"]
            )

            total = len(answers)

            percentage = int((score / total) * 100)

            # Risk level
            if percentage >= 80:
                risk = "Low Risk"
            elif percentage >= 50:
                risk = "Moderate Risk"
            else:
                risk = "High Risk"

            # Feedback
            if percentage >= 80:
                feedback = (
                    "Excellent URL awareness. "
                    "You demonstrated a strong ability to "
                    "identify suspicious links and verify domains."
                )

            elif percentage >= 50:
                feedback = (
                    "Your URL awareness is moderate. "
                    "Pay closer attention to domain names, "
                    "unexpected links and suspicious requests."
                )

            else:
                feedback = (
                    "Your URL awareness needs improvement. "
                    "Always inspect the complete domain before "
                    "opening links or entering sensitive information."
                )

            # Save results
            session["url_inspection_score"] = score
            session["url_inspection_total"] = total
            session["url_inspection_percentage"] = percentage
            session["url_inspection_risk"] = risk
            session["url_inspection_feedback"] = feedback

            return redirect(
                url_for("url_inspection.url_inspection_result")
            )

        return redirect(
            url_for("url_inspection.url_inspection_page")
        )

    # -----------------------------------------------------
    # GET CURRENT SCENARIO
    # -----------------------------------------------------
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM url_inspection_scenarios
        WHERE scenario_id = %s
    """, (scenario_ids[current],))

    scenario = cursor.fetchone()

    cursor.close()
    conn.close()

    if not scenario:
        return "Scenario not found."

    return render_template(
        "15 urlinspection.html",
        scenario=scenario,
        question_number=current + 1,
        total_questions=len(scenario_ids)
    )


# ---------------------------------------------------------
# RESULT / REPORT
# ---------------------------------------------------------
@url_inspection.route("/url-inspection/result")
def url_inspection_result():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    score = session.get("url_inspection_score", 0)
    total = session.get("url_inspection_total", 3)
    percentage = session.get("url_inspection_percentage", 0)
    risk = session.get("url_inspection_risk", "Unknown")
    feedback = session.get(
        "url_inspection_feedback",
        "No feedback available."
    )

    return render_template(
        "19 report.html",
        module_name="URL Inspection",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )