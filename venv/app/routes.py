from flask import Flask, render_template, request, redirect, url_for, session, abort
from flask_bcrypt import Bcrypt
import re
import datetime
import string, random
from os import urandom
from app import app



#TODO make mydqldb return dicts and not lists, and fix all templates


@app.route("/")
def about():
    return render_template("about.html")


def get_unique_id():
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for _ in range(15))


def get_date():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.context_processor
def inject_now():
    return {'now': datetime.datetime.utcnow()}




if __name__ == "__main__":
    app.run(threaded=True, host="0.0.0.0", debug=True)