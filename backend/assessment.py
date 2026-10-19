from database import get_db_connection


# =========================================================
# SAVE INDIVIDUAL ATTACK ASSESSMENT
# =========================================================

def save_assessment(
    user_id,
    module_name,
    score,
    total,
    percentage,
    risk_level
):

    connection = get_db_connection()

    if connection is None:
        return False

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO vulnerability_assessments
            (
                user_id,
                module_name,
                score,
                total,
                percentage,
                risk_level
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                user_id,
                module_name,
                score,
                total,
                percentage,
                risk_level
            )
        )

        connection.commit()

        return True

    except Exception as error:

        print("Assessment save error:", error)

        connection.rollback()

        return False

    finally:

        cursor.close()
        connection.close()