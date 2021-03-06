from flask import Flask, render_template, request, redirect, url_for, session, abort
import bcrypt
from app.db import DBConnection
import re
import datetime
import string, random
from os import urandom
from app import app

result_limit = 100


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        conn = DBConnection()
        cursor = conn.cursor
        db = conn.db
        lectures_list = []
        groups_list = []
        all_subjects = []
        fav_subjects = []


        if not session.get("username"): #not logged in, give events by order of date_time
            args = (result_limit,)
            cursor.execute("SELECT * FROM lectures JOIN subjects ON lectures.subject = subjects.id ORDER BY date_time LIMIT ?", args)
            lectures_list = cursor.fetchall()
            cursor.execute("SELECT * FROM groups JOIN subjects ON groups.subject = subjects.id ORDER BY date_time LIMIT ?", args)
            groups_list = cursor.fetchall()
            cursor.execute("SELECT * FROM subjects LIMIT ?", args)
            all_subjects = cursor.fetchall()

        else:
            args = (session["id"], ) #get his fav categories
            cursor.row_factory = lambda cursor, row: row[0]
            cursor.execute("SELECT subjects.id FROM interests JOIN subjects ON interests.subject_id = subjects.id WHERE interests.user_id=?", args)
            fav_subjects = cursor.fetchall()
            cursor.row_factory = None

            args = (result_limit,)
            cursor.execute("SELECT * FROM subjects LIMIT ?", args)
            all_subjects = cursor.fetchall()
            # display (1, 'History', True) for category info and whether the user likes it

            args = tuple(fav_subjects) + (session["id"],) #select events according to his categories
            cursor.row_factory = None
            cursor.execute("SELECT * FROM lectures JOIN subjects ON lectures.subject = subjects.id WHERE lectures.subject IN (%s)  ORDER BY date_time LIMIT ?" %','.join('?'*len(fav_subjects)), args)
            lectures_list = cursor.fetchall()
            cursor.execute("SELECT * FROM groups JOIN subjects ON groups.subject = subjects.id WHERE groups.subject IN (%s)  ORDER BY date_time LIMIT ?" %','.join('?'*len(fav_subjects)), args)
            groups_list = cursor.fetchall()

            """
            lectures_list structure: (id, name, subject id, date_time, description, link, subject id, subject name)
            groups_list structure:  (id, name, subject id, date_time, description, link, subject id, subject name)
            
            """

        return render_template("index.html", username=session.get("username"), lectures=lectures_list, groups=groups_list, subjects=all_subjects, favs=fav_subjects)

    else:
        if not session.get("id"):
            return redirect(url_for("login"))

        conn = DBConnection()
        cursor = conn.cursor
        db = conn.db


        if request.form["request_type"] == "add_lecture": #making a new lecture
            args = (request.form["title"], request.form["lecture_subject"], request.form["date"], request.form["desc"], request.form["link"],)
            cursor.execute("INSERT INTO lectures (name, subject, date_time, description, link) VALUES (?,?,?,?,?)", args)
            db.commit()
            db.close()
            return redirect(url_for("index"))

        elif request.form["request_type"] == "add_group": #making a new lecture
            args = (request.form["title"], request.form["group_subject"], request.form["date"], request.form["desc"], request.form["link"],)
            cursor.execute("INSERT INTO groups (name, subject, date_time, description, link) VALUES (?,?,?,?,?)", args)
            db.commit()
            db.close()
            return redirect(url_for("index"))
        
        else:
            args = (session["id"],)
            cursor.execute("DELETE FROM interests WHERE user_id=?",args)
            db.commit()

            liked = request.form.getlist("subjectbox")
            for entry in liked:
                args = (session["id"], entry,)
                cursor.execute("INSERT INTO interests VALUES (?,?)", args)
                db.commit()


            db.close()        
            return redirect(url_for("index"))
    


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST" and re.match("^[a-zA-Z0-9_]{3,20}$", request.form["username"]):
        conn = DBConnection()
        cursor = conn.cursor
        db = conn.db

        args = (request.form["username"],) #check if username already exists
        cursor.execute("SELECT * FROM users WHERE username=?", args)

        if not cursor.fetchall():
            salt = bcrypt.gensalt()
            hash = bcrypt.hashpw(request.form["password"].encode('utf-8'), salt)

            args = (request.form["username"], request.form["email"], hash, ) #add the user tuple to the DB
            cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", args)
            db.commit()

            args = (request.form["username"],) #get user's new id
            cursor.execute("SELECT id FROM users WHERE username=?", args) 
            user_id = cursor.fetchone()[0]

            
            db.close()
            session["id"] = user_id
            session["username"] = request.form["username"]
            return redirect(url_for("index"))


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
        cursor.execute("SELECT id, password FROM users WHERE username=?", args)
        result = cursor.fetchone()
        if result:
            id = result[0]
            hash = result[1]
            if bcrypt.checkpw(request.form["password"].encode('utf-8'), hash.encode('utf-8')): #check password
                session["id"] = id
                session["username"] = request.form["username"]
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
