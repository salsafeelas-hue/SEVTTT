import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="safii5858",
        database="sevt_db"
    )
    return connection