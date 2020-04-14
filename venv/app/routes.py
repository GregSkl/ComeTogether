from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_bcrypt import Bcrypt
from app.db import DBConnection
import re
import datetime
import string, random
from os import urandom
from app import app

result_limit = 100

@app.route("/")
def index():
    conn = DBConnection()
    cursor = conn.cursor()
    db = conn.db
    lectures_list = []
    groups_list = []

    if not session["username"]: #not logged in, give events by order of date
        args = (result_limit,)
        cursor.execute("SELECT * FROM lectures LIMIT ? ORDER BY date", args)
        lectures_list = cursor.fetchall()
        cursor.execute("SELECT * FROM groups LIMIT ? ORDER BY date", args)
        groups_list = cursor.fetchall()

    else:
        args = (session["id"], ) #get his fav categories
        cursor.row_factory = lambda cursor, row: row[0]
        cursor.execute("SELECT category.id FROM (user_to_category NATURAL_JOIN categories) WHERE user.id=?", args)
        user_categories = cursor.fetchall()

        args = tuple(user_categories) + (session[id],) #select events according to his categories
        cursor.row_factory = None
        cursor.execute("SELECT * FROM lectures WHERE subject IN (%s) LIMIT ? ORDER BY date" %','.join('?'*len(user_categories)), args)
        lectures_list = cursor.fetchall()
        cursor.execute("SELECT * FROM groups WHERE subject IN (%s) LIMIT ? ORDER BY date" %','.join('?'*len(user_categories)), args)
        groups_list = cursor.fetchall()


    return render_template("index.html", lectures = lectures_list, groups = groups_list)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST" and re.match("^[a-zA-Z0-9_]{3,20}$", request.form["username"]):
        conn = DBConnection()
        cursor = conn.cursor
        db = conn.db

        args = (request.form["username"],) #check if username already exists
        cursor.execute("SELECT * FROM users WHERE username=?", args)

        if not cursor.rowcount:
            hash = bcrypt.generate_password_hash(request.form["password"])

            args = (request.form["username"], request.form["email"], hash, ) #add the user tuple to the DB
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", args)
            db.commit()

            args = (request.form["username"],) #get user's new id
            cursor.execute("SELECT id FROM users WHERE username=?", args) 
            user_id = cursor.fetchone()[0]

            interests = [] #TODO: find a way to parse the interest data from the POST request
            for entry in interests:
                args = (entry, ) #get id of the subject
                cursor.execute("SELECT id FROM subjects WHERE name=?",args)
                entry_id = cursor.fetchone()[0]

                args = (user_id, entry_id,) #enter the subject association
                cursor.execute("INSERT INTO interests (user.id, subject.id) VALUES (?,?)", args)

            
            db.close()
            session["id"] = user_id
            session["username"] = request.form["username"]
            return redirect(url_for("about"))


        else:  #show that username exists
            db.close()
            return render_template("signup.html", error=True)

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = DBConnection()
        cursor = conn.cursor
        db = conn.db

        args = (request.form["username"],) #checking if the person is registered
        cursor.execute("SELECT id, password, permission_id FROM users WHERE username=?", args)
        if cursor.rowcount:
            result = cursor.fetchone()
            id = result[0]
            hash = result[1]
            permission_id = result[2]
            if bcrypt.check_password_hash(hash, request.form["password"]): #check password
                session["id"] = id
                session["username"] = request.form["username"]
                session["permission_id"] = permission_id
                db.close()
                return redirect(url_for("index"))
            else:
                db.close()
                return render_template("login.html", passError=True)
        else:
            db.close()
            return render_template("login.html", userError=True)
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


def get_unique_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(15))


def get_date():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")



@app.errorhandler(404)
def page_not_found(error):
    return render_template("page_not_found.html"), 404


@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}


app.secret_key = urandom(24)


if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0", debug=True)