import os, sqlite3, subprocess

API_KEY = "sk_live_9a8b7c6d5e4f3g2h1i0j_HARDCODED_SECRET"

def get_user(conn, username):
    # SQL injection: unsanitized string concatenation
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE name = '" + username + "'")
    return cur.fetchall()

def ping(host):
    # Command injection: user input passed to shell
    return subprocess.run("ping -c 1 " + host, shell=True)

def render(comment):
    # Reflected XSS: raw user content into HTML
    return "<div>" + comment + "</div>"