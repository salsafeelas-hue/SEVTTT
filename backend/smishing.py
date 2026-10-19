from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random


smishing = Blueprint(
    "smishing",
    __name__
)


# ============================================================
# START SMISHING SIMULATOR
# ============================================================

@smishing.route("/smishing/start")
def start_smishing():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM smishing_scenarios
    """)

    all_scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(all_scenarios) < 3:
        return "Not enough smishing scenarios in database."

    # Randomly select 3 scenarios
    scenarios = random.sample(all_scenarios, 3)

    # Store selected scenarios in session
    session["smishing_scenarios"] = scenarios
    session["smishing_current"] = 0
    session["smishing_answers"] = []

    return redirect(
        url_for("smishing.smishing_page")
    )


# ============================================================
# SMISHING SIMULATOR PAGE
# ============================================================

@smishing.route(
    "/smishing",
    methods=["GET", "POST"]
)
def smishing_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get(
        "smishing_scenarios",
        []
    )

    current = session.get(
        "smishing_current",
        0
    )

    answers = session.get(
        "smishing_answers",
        []
    )

    # If no simulation is active
    if not scenarios:
        return redirect(
            url_for(
                "smishing.start_smishing"
            )
        )

    # ========================================================
    # PROCESS USER ANSWER
    # ========================================================

    if request.method == "POST":

        user_answer = request.form.get("answer")

        if user_answer not in ["safe", "scam"]:
            return redirect(
                url_for(
                    "smishing.smishing_page"
                )
            )

        current_scenario = scenarios[current]

        # Determine correct answer
        correct_answer = (
            "scam"
            if int(current_scenario["is_scam"]) == 1
            else "safe"
        )

        is_correct = (
            user_answer == correct_answer
        )

        # Store answer
        answers.append({
            "scenario_id": current_scenario["scenario_id"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

        session["smishing_answers"] = answers

        # Move to next scenario
        current += 1

        session["smishing_current"] = current

        # ====================================================
        # ALL 3 SCENARIOS COMPLETED
        # ====================================================

        if current >= len(scenarios):

            score = sum(
                1
                for answer in answers
                if answer["is_correct"]
            )

            total = len(scenarios)

            percentage = int(
                (score / total) * 100
            )

            # Risk calculation
            if percentage >= 80:
                risk = "Low Risk"

            elif percentage >= 50:
                risk = "Moderate Risk"

            else:
                risk = "High Risk"

            # Final feedback
            if percentage >= 80:

                feedback = (
                    "You demonstrated strong awareness of "
                    "smishing techniques. You were able to "
                    "identify suspicious SMS messages and "
                    "recognize common social-engineering warning signs."
                )

            elif percentage >= 50:

                feedback = (
                    "You showed moderate awareness of smishing "
                    "risks. Pay closer attention to suspicious "
                    "links, urgent requests, account warnings "
                    "and unexpected payment messages."
                )

            else:

                feedback = (
                    "Your responses indicate that you may be "
                    "vulnerable to smishing attacks. Be cautious "
                    "with unexpected SMS messages, suspicious "
                    "links, urgent requests and messages asking "
                    "for passwords, OTPs or payments."
                )

            # Save results in session
            session["smishing_score"] = score
            session["smishing_total"] = total
            session["smishing_percentage"] = percentage
            session["smishing_risk"] = risk
            session["smishing_feedback"] = feedback

            return redirect(
                url_for(
                    "smishing.smishing_result"
                )
            )

    # ========================================================
    # SAFETY CHECK
    # ========================================================

    if current >= len(scenarios):

        return redirect(
            url_for(
                "smishing.smishing_result"
            )
        )

    # Get current SMS scenario
    current_scenario = scenarios[current]

    return render_template(
        "12 smishing.html",
        scenario=current_scenario,
        question_number=current + 1,
        total_questions=len(scenarios)
    )


# ============================================================
# SMISHING RESULT / REPORT
# ============================================================

@smishing.route(
    "/smishing/result"
)
def smishing_result():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    score = session.get(
        "smishing_score",
        0
    )

    total = session.get(
        "smishing_total",
        3
    )

    percentage = session.get(
        "smishing_percentage",
        0
    )

    risk = session.get(
        "smishing_risk",
        "High Risk"
    )

    feedback = session.get(
        "smishing_feedback",
        "Smishing simulation completed."
    )

    return render_template(
        "19 report.html",
        module_name="Smishing Attack",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )