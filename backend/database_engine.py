import sqlite3

# These consist of backend functions for the database
# Connect Function will cause the frontend to immediately connect with
# sqlite3 db and establish a table if one doesnt exist
def connect():
    conn = sqlite3.connect("algodistro.db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS useremail (id INTEGER PRIMARY KEY, username text, email text)")
    conn.commit()
    conn.close
    return

# The Insert Function will insert a user and their email into the sqlite3 db
# The book has '3' values, NULL assigns a random numberic id value,
def insert(username, email):
    conn = sqlite3.connect("algodistro.db")
    cur = conn.cursor()
    # NULL is to pass the random 'id' INTEGER PRIMARY KEY
    cur.execute("INSERT INTO useremail VALUES (NULL, ?, ?)", (username, email)) 
    conn.commit()
    conn.close
    return

def update_user_email(username, email):
    conn = sqlite3.connect("algodistro.db")
    cur = conn.cursor()
    cur.execute("UPDATE useremail SET email=? WHERE username=?", (email, username))
    conn.commit()
    print("{}'s email updated to {}".format(username, email))
    conn.close
    return

def query_username(username):
    conn = sqlite3.connect("algodistro.db")
    cur = conn.cursor()
    cur.execute("SELECT username FROM useremail")
    rows = cur.fetchall()
    if (username,) in rows:
        print("Username: {} in Database!".format(username))
    else:
        print("Username: {} not in Database!".format(username))
        email = input("Add {}'s email: ".format(username))
        insert(username, email)
    email = query_email_exists(username)
    conn.close()
    return email

def query_email_exists(username):
    conn = sqlite3.connect("algodistro.db")
    cur = conn.cursor()
    cur.execute('SELECT email FROM useremail WHERE username=?', (username,))
    email = cur.fetchall()
    email = email[0]
    if email is not None:
        print("{}'s email is {}.".format(username, email[0]))
    else:
        print("{}'s email does not exist!".format(username))
        email = input("Please add {}'s email: ".format(username))
        update_user_email(username, email)
    conn.close()
    return email
