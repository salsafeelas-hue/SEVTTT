import os
import requests
import mysql.connector

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    request,
    send_file
)

from dotenv import load_dotenv


# =========================================================
# BLUEPRINT
# =========================================================

deepfake_voice = Blueprint(
    "deepfake_voice",
    __name__
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PROJECT_DIR = os.path.dirname(
    BASE_DIR
)

STATIC_DIR = os.path.join(
    PROJECT_DIR,
    "static"
)

AUDIO_DIR = os.path.join(
    STATIC_DIR,
    "deepfake_audio"
)

os.makedirs(
    AUDIO_DIR,
    exist_ok=True
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv(
    os.path.join(
        BASE_DIR,
        ".env"
    )
)

ELEVENLABS_API_KEY = os.getenv(
    "ELEVENLABS_API_KEY"
)

# ElevenLabs voice selected for the training simulator
VOICE_ID = "w2VczpnpJO48HDyBg1xV"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",

        # IMPORTANT:
        # Replace this with the SAME MySQL password
        # used by your working SEVT files.

        password="safii5858",

        database="sevt_db"
    )


# =========================================================
# START DEEPFAKE VOICE MODULE
# =========================================================

@deepfake_voice.route(
    "/deepfake-voice/start"
)
def start_deepfake_voice():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT scenario_id
            FROM deepfake_voice_scenarios
            ORDER BY RAND()
            LIMIT 3
            """
        )

        rows = cursor.fetchall()

        cursor.close()
        db.close()

        scenario_ids = [
            row["scenario_id"]
            for row in rows
        ]

        if len(scenario_ids) == 0:

            return (
                "No deepfake voice scenarios "
                "found in the database."
            ), 500

        # Store ONLY IDs in the session
        session[
            "deepfake_scenario_ids"
        ] = scenario_ids

        session[
            "deepfake_current"
        ] = 0

        session[
            "deepfake_score"
        ] = 0

        session[
            "deepfake_answers"
        ] = []

        return redirect(
            url_for(
                "deepfake_voice.deepfake_voice_page"
            )
        )

    except Exception as e:

        print(
            "Deepfake start error:",
            str(e)
        )

        return (
            "Unable to start Deepfake Voice module: "
            + str(e)
        ), 500


# =========================================================
# MAIN DEEPFAKE VOICE SIMULATOR
# =========================================================

@deepfake_voice.route(
    "/deepfake-voice",
    methods=["GET", "POST"]
)
def deepfake_voice_page():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    scenario_ids = session.get(
        "deepfake_scenario_ids",
        []
    )

    current = session.get(
        "deepfake_current",
        0
    )

    # No active attempt
    if not scenario_ids:

        return redirect(
            url_for(
                "deepfake_voice.start_deepfake_voice"
            )
        )

    # All scenarios completed
    if current >= len(scenario_ids):

        return redirect(
            url_for(
                "deepfake_voice.deepfake_voice_result"
            )
        )

    scenario_id = scenario_ids[current]

    try:

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT *
            FROM deepfake_voice_scenarios
            WHERE scenario_id = %s
            """,
            (scenario_id,)
        )

        scenario = cursor.fetchone()

        cursor.close()
        db.close()

    except Exception as e:

        print(
            "Scenario database error:",
            str(e)
        )

        return (
            "Database error: "
            + str(e)
        ), 500

    if not scenario:

        return (
            "Deepfake voice scenario "
            "not found."
        ), 404

    # =====================================================
    # SUBMIT ANSWER
    # =====================================================

    if request.method == "POST":

        answer = request.form.get(
            "answer"
        )

        if answer not in ["1", "2"]:

            return redirect(
                url_for(
                    "deepfake_voice.deepfake_voice_page"
                )
            )

        answer = int(answer)

        correct_answer = int(
            scenario["correct_action"]
        )

        is_correct = (
            answer == correct_answer
        )

        # Update score
        if is_correct:

            session[
                "deepfake_score"
            ] = (
                session.get(
                    "deepfake_score",
                    0
                ) + 1
            )

        # Store answer information
        answers = session.get(
            "deepfake_answers",
            []
        )

        answers.append(
            {
                "scenario_id": scenario_id,
                "answer": answer,
                "correct": is_correct
            }
        )

        session[
            "deepfake_answers"
        ] = answers

        # Move to next scenario
        session[
            "deepfake_current"
        ] = current + 1

        return redirect(
            url_for(
                "deepfake_voice.deepfake_voice_page"
            )
        )

    # =====================================================
    # SHOW SCENARIO
    # =====================================================

    return render_template(
        "16 deepfakevoice.html",
        scenario=scenario,
        current=current + 1,
        total=len(scenario_ids)
    )


# =========================================================
# GENERATE AND SERVE AI VOICE
# =========================================================

@deepfake_voice.route(
    "/deepfake-voice/audio/<int:scenario_id>"
)
def deepfake_voice_audio(
    scenario_id
):

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "user_id" not in session:

        return (
            "Login required"
        ), 401

    # -----------------------------------------------------
    # CHECK SELECTED SCENARIO
    # -----------------------------------------------------

    selected_ids = session.get(
        "deepfake_scenario_ids",
        []
    )

    if scenario_id not in selected_ids:

        return (
            "Invalid scenario"
        ), 404

    # -----------------------------------------------------
    # CHECK API KEY
    # -----------------------------------------------------

    if not ELEVENLABS_API_KEY:

        return (
            "ELEVENLABS_API_KEY is missing "
            "from backend/.env"
        ), 500

    # -----------------------------------------------------
    # AUDIO FILE LOCATION
    # -----------------------------------------------------

    audio_file = os.path.join(
        AUDIO_DIR,
        f"scenario_{scenario_id}.mp3"
    )

    # -----------------------------------------------------
    # USE EXISTING FILE IF AVAILABLE
    # -----------------------------------------------------

    if os.path.exists(audio_file):

        if os.path.getsize(
            audio_file
        ) > 0:

            print(
                "Using existing audio:",
                audio_file
            )

            return send_file(
                audio_file,
                mimetype="audio/mpeg",
                as_attachment=False,
                max_age=0
            )

    try:

        # =================================================
        # GET SCENARIO TEXT
        # =================================================

        db = get_db_connection()

        cursor = db.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT message_text
            FROM deepfake_voice_scenarios
            WHERE scenario_id = %s
            """,
            (scenario_id,)
        )

        scenario = cursor.fetchone()

        cursor.close()
        db.close()

        if not scenario:

            return (
                "Scenario not found"
            ), 404

        text = scenario[
            "message_text"
        ]

        # =================================================
        # ELEVENLABS API URL
        # =================================================

        api_url = (
            "https://api.elevenlabs.io/v1/"
            "text-to-speech/"
            + VOICE_ID
            + "?output_format=mp3_44100_128"
        )

        # =================================================
        # HEADERS
        # =================================================

        headers = {
            "xi-api-key":
                ELEVENLABS_API_KEY,

            "Content-Type":
                "application/json",

            "Accept":
                "audio/mpeg"
        }

        # =================================================
        # REQUEST DATA
        # =================================================

        data = {

            "text": text,

            "model_id":
                "eleven_multilingual_v2"
        }

        print(
            "\n=============================="
        )

        print(
            "Generating AI voice..."
        )

        print(
            "Scenario:",
            scenario_id
        )

        print(
            "Voice ID:",
            VOICE_ID
        )

        print(
            "=============================="
        )

        # =================================================
        # SEND REQUEST
        # =================================================

        response = requests.post(

            api_url,

            headers=headers,

            json=data,

            timeout=60
        )

        # =================================================
        # CHECK RESPONSE
        # =================================================

        if response.status_code != 200:

            print(
                "\n=============================="
            )

            print(
                "ELEVENLABS ERROR"
            )

            print(
                "Status:",
                response.status_code
            )

            print(
                "Response:",
                response.text
            )

            print(
                "==============================\n"
            )

            return (
                "ElevenLabs error: "
                + response.text
            ), 500

        # =================================================
        # CHECK AUDIO RESPONSE
        # =================================================

        if not response.content:

            return (
                "ElevenLabs returned "
                "empty audio."
            ), 500

        # =================================================
        # SAVE MP3
        # =================================================

        with open(
            audio_file,
            "wb"
        ) as file:

            file.write(
                response.content
            )

        # =================================================
        # VERIFY MP3
        # =================================================

        if not os.path.exists(
            audio_file
        ):

            return (
                "Audio file was not created."
            ), 500

        file_size = os.path.getsize(
            audio_file
        )

        print(
            "Audio file created:"
        )

        print(
            audio_file
        )

        print(
            "File size:",
            file_size,
            "bytes"
        )

        # -------------------------------------------------
        # Empty file check
        # -------------------------------------------------

        if file_size == 0:

            return (
                "Generated audio file "
                "is empty."
            ), 500

        print(
            "\nAI VOICE GENERATED "
            "SUCCESSFULLY\n"
        )

        # =================================================
        # SEND MP3 TO BROWSER
        # =================================================

        return send_file(

            audio_file,

            mimetype="audio/mpeg",

            as_attachment=False,

            download_name=(
                f"deepfake_voice_"
                f"{scenario_id}.mp3"
            ),

            max_age=0
        )

    except requests.exceptions.Timeout:

        print(
            "ElevenLabs request timed out."
        )

        return (
            "ElevenLabs request timed out."
        ), 500

    except requests.exceptions.RequestException as e:

        print(
            "ElevenLabs connection error:",
            str(e)
        )

        return (
            "ElevenLabs connection error: "
            + str(e)
        ), 500

    except Exception as e:

        print(
            "\n=============================="
        )

        print(
            "DEEPFAKE AUDIO ERROR"
        )

        print(
            str(e)
        )

        print(
            "==============================\n"
        )

        return (
            "Audio generation error: "
            + str(e)
        ), 500


# =========================================================
# RESULT PAGE
# =========================================================

@deepfake_voice.route(
    "/deepfake-voice/result"
)
def deepfake_voice_result():

    if "user_id" not in session:

        return redirect(
            url_for("auth.login")
        )

    score = session.get(
        "deepfake_score",
        0
    )

    scenario_ids = session.get(
        "deepfake_scenario_ids",
        []
    )

    total = len(
        scenario_ids
    )

    if total == 0:

        total = 3

    # =====================================================
    # CALCULATE PERCENTAGE
    # =====================================================

    percentage = int(
        (score / total) * 100
    )

    # =====================================================
    # RISK
    # =====================================================

    if percentage >= 80:

        risk = "Low Risk"

        feedback = (
            "You showed strong awareness "
            "of suspicious voice-based "
            "social engineering techniques."
        )

    elif percentage >= 50:

        risk = "Moderate Risk"

        feedback = (
            "You identified some warning "
            "signs, but should verify "
            "unexpected voice requests "
            "more carefully."
        )

    else:

        risk = "High Risk"

        feedback = (
            "You should improve your ability "
            "to identify deepfake voice scams "
            "and urgent social engineering "
            "requests."
        )

    # =====================================================
    # SAVE ASSESSMENT
    # =====================================================

    try:

        db = get_db_connection()

        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO vulnerability_assessments
            (
                user_id,
                module_name,
                score,
                total_questions,
                percentage,
                risk_level
            )
            VALUES
            (%s, %s, %s, %s, %s, %s)
            """,
            (
                session["user_id"],

                "AI Deepfake Voice Scam",

                score,

                total,

                percentage,

                risk
            )
        )

        db.commit()

        cursor.close()

        db.close()

        print(
            "Deepfake voice assessment saved."
        )

    except Exception as e:

        print(
            "Assessment save error:",
            str(e)
        )

    # =====================================================
    # SHOW REPORT
    # =====================================================

    return render_template(
        "19 report.html",

        module_name=
            "AI Deepfake Voice Scam",

        score=score,

        total=total,

        percentage=percentage,

        risk=risk,

        feedback=feedback
    )