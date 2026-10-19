from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db_connection
import random

social_media_privacy = Blueprint(
    "social_media_privacy",
    __name__
)


# --------------------------------------------------
# START SOCIAL MEDIA PRIVACY SIMULATOR
# --------------------------------------------------
@social_media_privacy.route("/social-media-privacy/start")
def start_social_media_privacy():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM social_media_privacy_scenarios
    """)

    all_scenarios = cursor.fetchall()

    cursor.close()
    conn.close()

    if len(all_scenarios) < 3:
        return "Not enough social media privacy scenarios in database."

    # Randomly select exactly 3 scenarios
    scenarios = random.sample(all_scenarios, 3)

    session["social_privacy_scenarios"] = scenarios
    session["social_privacy_current"] = 0
    session["social_privacy_answers"] = []

    return redirect(
        url_for("social_media_privacy.social_media_privacy_page")
    )


# --------------------------------------------------
# SOCIAL MEDIA PRIVACY QUESTIONS
# --------------------------------------------------
@social_media_privacy.route(
    "/social-media-privacy",
    methods=["GET", "POST"]
)
def social_media_privacy_page():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    scenarios = session.get(
        "social_privacy_scenarios",
        []
    )

    current = session.get(
        "social_privacy_current",
        0
    )

    answers = session.get(
        "social_privacy_answers",
        []
    )

    # If no simulation has started
    if not scenarios:
        return redirect(
            url_for(
                "social_media_privacy.start_social_media_privacy"
            )
        )

    # --------------------------------------------------
    # PROCESS ANSWER
    # --------------------------------------------------
    if request.method == "POST":

        user_answer = request.form.get("answer")

        if user_answer not in ["safe", "risky"]:
            return redirect(
                url_for(
                    "social_media_privacy.social_media_privacy_page"
                )
            )

        current_scenario = scenarios[current]

        correct_answer = (
            "risky"
            if int(current_scenario["is_risky"]) == 1
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

        session["social_privacy_answers"] = answers

        current += 1

        session["social_privacy_current"] = current

        # --------------------------------------------------
        # FINISH AFTER 3 QUESTIONS
        # --------------------------------------------------
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

            # Risk level
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
                    "social-media privacy risks. You were able "
                    "to identify most risky situations correctly."
                )

            elif percentage >= 50:

                feedback = (
                    "You showed moderate awareness of social-media "
                    "privacy risks. Review what information you "
                    "share publicly and check your privacy settings."
                )

            else:

                feedback = (
                    "Your responses indicate that you may be "
                    "vulnerable to social-media privacy risks. "
                    "Be careful about sharing personal information, "
                    "locations and accepting unknown accounts."
                )

            session["social_privacy_score"] = score
            session["social_privacy_total"] = total
            session["social_privacy_percentage"] = percentage
            session["social_privacy_risk"] = risk
            session["social_privacy_feedback"] = feedback

            return redirect(
                url_for(
                    "social_media_privacy.social_media_privacy_result"
                )
            )

    # --------------------------------------------------
    # CURRENT QUESTION
    # --------------------------------------------------
    if current >= len(scenarios):

        return redirect(
            url_for(
                "social_media_privacy.social_media_privacy_result"
            )
        )

    current_scenario = scenarios[current]

    return render_template(
        "10 socialmediaprivacy.html",
        scenario=current_scenario,
        question_number=current + 1,
        total_questions=len(scenarios)
    )


# --------------------------------------------------
# RESULT PAGE
# --------------------------------------------------
@social_media_privacy.route(
    "/social-media-privacy/result"
)
def social_media_privacy_result():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    score = session.get(
        "social_privacy_score",
        0
    )

    total = session.get(
        "social_privacy_total",
        3
    )

    percentage = session.get(
        "social_privacy_percentage",
        0
    )

    risk = session.get(
        "social_privacy_risk",
        "High Risk"
    )

    feedback = session.get(
        "social_privacy_feedback",
        "Social Media Privacy simulation completed."
    )

    return render_template(
        "19 report.html",
        module_name="Social Media Privacy Analyzer",
        score=score,
        total=total,
        total_marks=total,
        percentage=percentage,
        risk=risk,
        feedback=feedback
    )