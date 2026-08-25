import sqlite3, subprocess
DB_PASSWORD = "prod_db_pw_supersecret_123"
def lookup(conn, uid):
    return conn.execute("SELECT * FROM accounts WHERE id = %s" % uid).fetchall()
def run(cmd):
    return subprocess.check_output("sh -c " + cmd, shell=True)