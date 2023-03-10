from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, jsonify
from flask_session import Session
from flask_login import LoginManager, UserMixin

import pandas as pd
import numpy as np
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

import math
import time

import os

from classes import Database, Trip

db = Database()

# REMOVE LATER: Adds trip to database
db.addTrip(Trip(None, "WWW 2023", "MS", 4, 2, "blah blah blah", [1, 2, 3, 4]))
db.addTrip(Trip(None, "Viper Venture 2023: Thailand", "HS", 5, 3, "idk lol", [260, 261, 262]))
db.addTrip(Trip(None, "JV Boys Volleyball", "MESAC", 7, 2, "eeeeeee", [148, 100, 123, 90, 7]))
db.addTrip(Trip(None, "Varsity Boys Soccer", "MESAC", 9, 3, "aaaaa", [21, 150, 230, 190, 72, 110]))
db.addTrip(Trip(None, "HS Cross Country", "MESAC", 3, 3, "yyyyyy", [273, 220]))
db.addTrip(Trip(None, "HS Tennis", "MESAC", 5, 2, "xxxxxxx", [288, 270, 242, 276]))
db.addTrip(Trip(None, "HS Wrestling", "MESAC", 6, 2, "wwwwww", [204]))
db.updateTrip(Trip("t4", "Varsity Boys Soccer", "MESAC", 9, 3, "updated soccer", [21, 150, 230, 190, 72, 110, 289, 280]))
#print(db.getTripById("t3"))

app = Flask(__name__)

app.config["SESSION_TYPE"] = "filesystem"

Session(app)


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def login_not_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is not None:
            return redirect("/")
        else:
            return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["GET"])
def start():
    return render_template("start.html")

@app.route("/trip", methods=["GET", "POST"])
def trip_code_form():
    if request.method == "GET":
        return render_template("trip_code_form.html")
    else:
        first = request.form["first"]
        second = request.form["second"]
        third = request.form["third"]
        fourth = request.form["fourth"]
        fifth = request.form["fifth"]
        sixth = request.form["sixth"]

        return redirect("/" + first + second + third + fourth + fifth + sixth)
    
@app.route("/<trip_id>", methods=["GET", "POST"])
def student_preference_form(trip_id):
    if request.method == "GET":
        return render_template("student_preference_form.html", trip_id=trip_id)
    else:
        return render_template("success.html", trip_id=trip_id)

@app.route("/teacher-login", methods=["GET", "POST"])
def teacher_login_form():
    if request.method == "GET":
        return render_template("teacher_login_form.html")
    else:
        return redirect("/trips")
    
@app.route("/trips", methods=["GET", "POST"])
def trips():
    if request.method == "GET":
        return render_template("trips.html", all_trips = db.getAllTrips(), trip_studs = [db.getStudentsInTrip(t[0]) for t in db.getAllTrips()])

@app.route("/trips/<trip_id>", methods=["GET", "POST"])
def trip(trip_id):
    if request.method == "GET":
        return render_template("trip.html", sel_trip = db.getTripById(trip_id), sel_students = db.getStudentsInTrip(trip_id), all_students=db.getAllStudents(db.getStudentsInTrip(trip_id)))
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="3000")