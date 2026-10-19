from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random

fake_shopping = Blueprint(
    "fake_shopping",
    __name__
)


# ---------------------------------------------------------
# START FAKE SHOPPING SIMULATION
# ---------------------------------------------------------
@fake_shopping.route("/fake-shopping/start")
def start_fake_shopping():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM fake_shopping_scenarios
    """)

    all_scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(all_scenarios) < 3:
        return "Not enough fake shopping scenarios in database."

    # Randomly select exactly 3 scenarios
    scenarios = random.sample(all_scenarios, 3)

    session["fake_shopping_scenarios"] = scenarios
    session["fake_shopping_current"] = 0
    session["fake_shopping_answers"] = []

    return redirect(
        url_for("fake_shopping.fake_shopping_page")
    )


# ---------------------------------------------------------
# FAKE SHOPPING SIMULATION PAGE
# ---------------------------------------------------------
@fake_shopping.route(
    "/fake-shopping",
    methods=["GET", "POST"]
)
def fake_shopping_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get(
        "fake_shopping_scenarios",
        []
    )

    current = session.get(
        "fake_shopping_current",
        0
    )

    answers = session.get(
        "fake_shopping_answers",
        []
    )

    if not scenarios:
        return redirect(
            url_for(
                "fake_shopping.start_fake_shopping"
            )
        )

    # -----------------------------------------------------
    # PROCESS USER DECISION
    # -----------------------------------------------------
    if request.method == "POST":

        user_answer = request.form.get("answer")

        if user_answer not in ["safe", "scam"]:
            return redirect(
                url_for(
                    "fake_shopping.fake_shopping_page"
                )
            )

        current_scenario = scenarios[current]

        correct_answer = (
            "scam"
            if int(current_scenario["is_scam"]) == 1
            else "safe"
        )

        is_correct = (
            user_answer == correct_answer
        )

        answers.append({
            "scenario_id": current_scenario["scenario_id"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct
        })

        session["fake_shopping_answers"] = answers

        # Move to next scenario
        current += 1

        session["fake_shopping_current"] = current

        # -------------------------------------------------
        # ALL 3 SCENARIOS COMPLETED
        # -------------------------------------------------
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
                    "fake shopping website indicators. "
                    "You were able to identify suspicious "
                    "shopping situations effectively."
                )

            elif percentage >= 50:

                feedback = (
                    "You showed moderate awareness of "
                    "fake shopping website risks. "
                    "Pay closer attention to unusual "
                    "discounts, payment requests and "
                    "website details."
                )

            else:

                feedback = (
                    "Your responses indicate that you may "
                    "be vulnerable to fake shopping websites. "
                    "Always verify the website, seller, "
                    "payment method and unusual offers "
                    "before making a purchase."
                )

            # Store final result
            session["fake_shopping_score"] = score
            session["fake_shopping_total"] = total
            session["fake_shopping_percentage"] = percentage
            session["fake_shopping_risk"] = risk
            session["fake_shopping_feedback"] = feedback

            return redirect(
                url_for(
                    "fake_shopping.fake_shopping_result"
                )
            )

    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------
    if current >= len(scenarios):

        return redirect(
            url_for(
                "fake_shopping.fake_shopping_result"
            )
        )

    current_scenario = scenarios[current]

    # -----------------------------------------------------
    # DISPLAY SHOPPING WEBSITE
    # -----------------------------------------------------
    return render_template(
        "11 fakeshopping.html",
        scenario=current_scenario,
        question_number=current + 1,
        total_questions=len(scenarios)
    )


# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------
@fake_shopping.route(
    "/fake-shopping/result"
)
def fake_shopping_result():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    score = session.get(
        "fake_shopping_score",
        0
    )

    total = session.get(
        "fake_shopping_total",
        3
    )

    percentage = session.get(
        "fake_shopping_percentage",
        0
    )

    risk = session.get(
        "fake_shopping_risk",
        "High Risk"
    )

    feedback = session.get(
        "fake_shopping_feedback",
        "Fake Shopping Website simulation completed."
    )

    return render_template(
        "19 report.html",
        module_name="Fake Shopping Website Attack",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )