import psycopg2
from psycopg2 import sql
import getpass
import os
import subprocess

DB_NAME = "leadge_test"
TS_NAME = "ts_leadge"
DRIVE_LOC = "/mnt/nvme"

PARAMS = {
    'user': "",
    'password': "",
    'host': 'localhost',
    'port': '5432',
    'dbname': 'postgres'
}

def connect():
    global conn
    conn = psycopg2.connect(**PARAMS)
    conn.autocommit = True
    global cursor
    cursor = conn.cursor()

def check_path(path):
    print(f"Setting permissions and ownership of {path}")

    try:
        subprocess.run(("sudo", "chown", "-c", "postgres:postgres", path), check = True)
        subprocess.run(("sudo", "chmod", "-c", "-R", "1744", path), check = True)
    except:
        print(f"Error setting permissions/ownership on {path}. Please run as sudo.")
        exit(1)

    try:
        file = os.path.join(path, 'temp.txt')
        with open(file, 'w') as fp:
            fp.write("pg")
        with open(file, 'r') as fp:
            fc = fp.read()
            if fc != "pg":
                raise ValueError("Contents invalid")
                
    except Exception as e:
        print(f"File read/write error, please check permissions/existence of {path}")
        exit(1)
    try:
        os.remove(file)
    except Exception as e:
        print(f"Error occurred on removal: {e}")

    print(f"Path {path} verified...")


def pg_login():

    logged = False

    while not logged:
        PARAMS['user'] = input("Postgres Username: ")
        PARAMS['password'] = getpass.getpass("Postgres Password: ")

        try:
            connect()
        except:
            print("Authentication failed. Please try again.")
            continue
        
        print(f"Now logged in as user {PARAMS['user']}.")
        print("----------------------------------------------------------------")
        logged = True
     
def create_db():
    print(f"Enter drive location for database")
    user_loc = input("Leave blank for /mnt/nvme: ")
    if user_loc.strip() != "":
        global DRIVE_LOC
        DRIVE_LOC = user_loc

    check_path(DRIVE_LOC)

    cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tablespace WHERE spcname = %s)", (TS_NAME,))
    if not cursor.fetchone()[0]:
        print("No tablespace, creating...")
        cursor.execute(sql.SQL("CREATE TABLESPACE {} LOCATION {}").format(
            sql.Identifier(TS_NAME),
            sql.Literal(DRIVE_LOC)
        ))

    conn.commit()

    print("Creating db...")
    cursor.execute(sql.SQL("CREATE DATABASE {} TABLESPACE {}").format(
        sql.Identifier(DB_NAME),
        sql.Identifier(TS_NAME)
    ))  

    conn.commit()
    cursor.close()
    conn.close()


# Sets LEAdge tables for MeterEvents
def set_tables():
    # Log in and connect to new DB
    PARAMS['dbname'] = DB_NAME
    connect()

    print("Setting LEAdge DB table...")

    # Create table
    cursor.execute('CREATE TABLE IF NOT EXISTS MeterEvents (\
        id SERIAL PRIMARY KEY,\
        datestamp timestamp,\
        deviceid int\
    )')

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Successfully created database {DB_NAME} at {DRIVE_LOC}")


if __name__ == "__main__":
    print("© 2023 Brookgreen Technologies, LLC")
    print("This tool will automatically set up a Postgres LEAdge database for you.")
    print("----------------------------------------------------------------")
    pg_login()
    create_db()
    set_tables()