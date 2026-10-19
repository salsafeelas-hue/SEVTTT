from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random


permission_checker = Blueprint(
    "permission_checker",
    __name__
)


# ---------------------------------------------------------
# START PERMISSION CHECKER
# ---------------------------------------------------------

@permission_checker.route("/permission-checker/start")
def start_permission_checker():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT scenario_id
        FROM permission_checker_scenarios
    """)

    all_scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(all_scenarios) < 3:
        return "Not enough permission checker scenarios in database."

    # Select 3 random scenarios
    selected = random.sample(all_scenarios, 3)

    scenario_ids = [
        row["scenario_id"]
        for row in selected
    ]

    # Store only IDs in the session
    session["permission_scenario_ids"] = scenario_ids
    session["permission_current"] = 0
    session["permission_answers"] = []

    # Remove old result data
    session.pop("permission_score", None)
    session.pop("permission_total", None)
    session.pop("permission_percentage", None)
    session.pop("permission_risk", None)
    session.pop("permission_feedback", None)

    return redirect(
        url_for(
            "permission_checker.permission_page"
        )
    )


# ---------------------------------------------------------
# PERMISSION CHECKER QUESTIONS
# ---------------------------------------------------------

@permission_checker.route(
    "/permission-checker",
    methods=["GET", "POST"]
)
def permission_page():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    scenario_ids = session.get(
        "permission_scenario_ids",
        []
    )

    current = session.get(
        "permission_current",
        0
    )

    answers = session.get(
        "permission_answers",
        []
    )

    # If no simulation has started
    if not scenario_ids:
        return redirect(
            url_for(
                "permission_checker.start_permission_checker"
            )
        )

    # If all scenarios are completed
    if current >= len(scenario_ids):
        return redirect(
            url_for(
                "permission_checker.permission_result"
            )
        )

    # -----------------------------------------------------
    # GET CURRENT SCENARIO FROM DATABASE
    # -----------------------------------------------------

    current_id = scenario_ids[current]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM permission_checker_scenarios
        WHERE scenario_id = %s
    """, (current_id,))

    scenario = cursor.fetchone()

    cursor.close()
    conn.close()

    if not scenario:
        return "Permission checker scenario not found."

    # -----------------------------------------------------
    # PROCESS USER ANSWER
    # -----------------------------------------------------

    if request.method == "POST":

        user_answer = request.form.get("answer")

        if user_answer not in [
            "1",
            "2",
            "3",
            "4"
        ]:
            return redirect(
                url_for(
                    "permission_checker.permission_page"
                )
            )

        correct_answer = str(
            scenario["correct_action"]
        )

        is_correct = (
            user_answer == correct_answer
        )

        answers.append({
            "scenario_id":
                scenario["scenario_id"],

            "user_answer":
                user_answer,

            "correct_answer":
                correct_answer,

            "is_correct":
                is_correct
        })

        session["permission_answers"] = answers

        # Move to next scenario
        current += 1

        session["permission_current"] = current

        # -------------------------------------------------
        # FINISHED ALL 3 SCENARIOS
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

            # Risk calculation
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
                    "of application permissions. You "
                    "were able to distinguish permissions "
                    "that are relevant to an application's "
                    "purpose from unnecessary or suspicious "
                    "requests."
                )

            elif percentage >= 50:

                feedback = (
                    "You demonstrated moderate awareness "
                    "of permission security. Before allowing "
                    "a permission, check whether it is "
                    "actually required for the application's "
                    "main function."
                )

            else:

                feedback = (
                    "Your responses indicate that you may "
                    "be vulnerable to excessive permission "
                    "requests. Avoid automatically allowing "
                    "permissions and review why an application "
                    "needs access to sensitive information."
                )

            # Store result
            session["permission_score"] = score
            session["permission_total"] = total
            session["permission_percentage"] = percentage
            session["permission_risk"] = risk
            session["permission_feedback"] = feedback

            return redirect(
                url_for(
                    "permission_checker.permission_result"
                )
            )

    # -----------------------------------------------------
    # DISPLAY CURRENT SCENARIO
    # -----------------------------------------------------

    return render_template(
        "14 permissionchecker.html",
        scenario=scenario,
        question_number=current + 1,
        total_questions=len(scenario_ids)
    )


# ---------------------------------------------------------
# PERMISSION CHECKER RESULT
# ---------------------------------------------------------

@permission_checker.route(
    "/permission-checker/result"
)
def permission_result():

    if "user_id" not in session:
        return redirect(
            url_for("auth.login")
        )

    score = session.get(
        "permission_score",
        0
    )

    total = session.get(
        "permission_total",
        3
    )

    percentage = session.get(
        "permission_percentage",
        0
    )

    risk = session.get(
        "permission_risk",
        "High Risk"
    )

    feedback = session.get(
        "permission_feedback",
        "Permission security simulation completed."
    )

    return render_template(
        "19 report.html",
        module_name="Permission Checker",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )