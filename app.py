from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, jsonify
from flask_session import Session
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

import pandas as pd
import numpy as np
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

from classes import Database, Trip

db = Database()

# REMOVE LATER: Adds example trips to database
db.add_trip(Trip(None, "WWW 2023: Grade 6 (Greece)", "MS", 4, 2, "blah blah blah", [1, 2, 3, 4]))
db.add_trip(Trip(None, "Viper Venture 2023: Thailand", "HS", 5, 3, "idk lol", [260, 261, 262]))
db.add_trip(Trip("TEST11", "JV Boys Volleyball", "MESAC", 7, 2, "eeeeeee", [0, 148, 100, 123, 90, 7,21, 150, 230, 190, 72, 110]))
db.add_trip(Trip(None, "Varsity Boys Soccer", "MESAC", 9, 3, "aaaaa", [21, 150, 230]))
db.add_trip(Trip(None, "HS Track & Field", "MESAC", 3, 3, "yyyyyy", [273, 220]))
db.add_trip(Trip(None, "HS Tennis", "MESAC", 5, 2, "xxxxxxx", [288, 270, 242, 276]))
db.add_trip(Trip(None, "HS Wrestling", "MESAC", 6, 2, "wwwwww", [204]))
db.add_trip(Trip("TEST22", "Test Trip", "Tester", 3, 2, "aaaaa", [0, 642, 631, 604, 573, 641]))
db.update_trip(Trip(Trip.get_trips()[3].get_id(), "Varsity Boys Soccer", "MESAC", 9, 3, "updated soccer", [21, 150, 230, 190, 72, 110, 289, 280]))
print(db.get_all_trips())

app = Flask(__name__)

# TODO: Auth Database Stuff (WIP)
"""
app.config['SESSION_TYPE'] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data/auth.db"
app.config['SECRET_KEY'] = "ACS-TSU@2022"
Session(app)
auth_db = SQLAlchemy(app)

class User (auth_db.Model, UserMixin):
    id = auth_db.Column(auth_db.Integer, primary_key=True)
    teacher = auth_db.Column(auth_db.Boolean, nullable=False)
    student_id = auth_db.Column(auth_db.Integer, nullable=False)
    email = auth_db.Column(auth_db.String(20), nullable=False)
    password = auth_db.Column(auth_db.String(80), nullable=False)
"""

# Temporary Implementation
TEACHER_LOGIN = {
    "username": "tsu@acs.sch.ae",
    "password": "ACSTeachers2023"
}
current_user = {
    "user": None,
    "is_logged_in": False,
    "is_teacher": False,
    "student": None
}

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
    global current_user
    logged_in = current_user['is_logged_in']
    is_teacher = current_user['is_teacher']
    print(current_user)
    return render_template("home.html", logged_in=logged_in, is_teacher=is_teacher)

@app.errorhandler(404)
def not_found(e):
  return render_template("404.html")

# TODO: User Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        # Handle Sign Up Info
        # Temporary Implementation
        global current_user
        current_user['is_logged_in'] = True
        current_user['is_teacher'] = False
        current_user['student'] = None
        # Redirect to either "/trips" or "/student"
        if current_user['is_teacher']:
            print(f"Logged in as Teacher")
            return redirect("/trips")
        else:
            print(f"Logged in as {current_user['student']['name']}")
            return redirect("/student")

# TODO: User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        # Handle Login Info
        # Temporary Implementation
        global current_user
        current_user['is_logged_in'] = True
        current_user['student'] = db.get_student_by_id(560)
        # Redirect to "/trips" or "/student" depending on uer
        if current_user['is_teacher']:
            return redirect("/trips")
        else:
            print(f"Logged in as {current_user['student']['name']}")
            return redirect("/student")

# TODO: User Logout
@app.route("/logout", methods=["GET", "POST"])
def logout():
    # Log Out User
     if request.method == "POST":
    # Temporary Implementation
        global current_user
        if current_user['is_logged_in']:
            print(f"Logged out")
            current_user['is_logged_in'] = False
            current_user['is_teacher'] = False
            current_user['student'] = None
        return render_template("logout.html")

# TODO: Student Page
# - Account Information:
#   - Change Gender and Grade
#   - Reset Password Option
@app.route("/student", methods=["GET", "POST"])
def student():
    if request.method == "GET":
        global current_user
        if (current_user['is_logged_in']):
            student = current_user['student']
            student_trips = db.get_trips_by_student(student['id'])
            trip_studs = [db.get_students_in_trip(trip['id']) for trip in student_trips]
            return render_template("student.html", student=student, student_trips=student_trips,trip_studs=trip_studs) # Needs to be setup
        else:
            return redirect("/login")

@app.route("/update_student", methods=["POST"])
def update_student():
    if request.method == "POST":
        data = request.get_json()[0]
        db.update_student(data['id'], data)
        current_user['student'] = db.get_student_by_id(current_user['student']['id'])
        return student()

@app.route("/search", methods=["GET", "POST"])
def trip_search():
    if request.method == "GET":
        if not current_user['is_logged_in']:
            return render_template("trip-search.html")
        else:
            return render_template("unauthorized.html")
    else:
        first = request.form['first']
        second = request.form['second']
        third = request.form['third']
        fourth = request.form['fourth']
        fifth = request.form['fifth']
        sixth = request.form['sixth']
        return redirect("/search/" + first + second + third + fourth + fifth + sixth)

@app.route("/search/<trip_id>", methods=["GET", "POST"])
def logged_out_preferences(trip_id):
    if request.method == "GET":
        if db.get_trip_by_id(trip_id) != None:
            global current_user
            sel_trip = db.get_trip_by_id(trip_id)
            sel_students = db.get_students_in_trip(trip_id)
            
            # User clicks "Edit" after submitting (Post-login)
            if current_user['is_logged_in']: # Example Implementation
                return logged_in_preferences(trip_id)
            else:
                return render_template("student-pref-1.html", trip_id = trip_id, sel_trip=sel_trip, sel_students=sel_students)
        else:
            return render_template("trip-error.html")
    else:
        self_id = pref_1 = pref_2 = pref_3 = pref_4 = pref_5 = None
        if 'pref_0' in request.form:
            self_id = request.form['pref_0']
        if 'pref_1' in request.form:
            pref_1 = request.form['pref_1']
        if 'pref_2' in request.form:
            pref_2 = request.form['pref_2']
        if 'pref_3' in request.form:
            pref_3 = request.form['pref_3']
        if 'pref_4' in request.form:
            pref_4 = request.form['pref_4']
        if 'pref_5' in request.form:
            pref_5 = request.form['pref_5']
        db.add_preferences(trip_id, self_id, (pref_1, pref_2, pref_3, pref_4, pref_5))
        #print(db.get_all_trip_preferences())
        return render_template("success.html", sel_trip = db.get_trip_by_id(trip_id))
    
@app.route("/student/<trip_id>", methods=["GET", "POST"])
def logged_in_preferences(trip_id):
    global current_user
    student = current_user['student'] # Example Implementation
    if request.method == "GET":
        if db.get_trip_by_id(trip_id) != None:
            sel_trip = db.get_trip_by_id(trip_id)
            sel_students = db.get_students_in_trip(trip_id)
            sel_students.pop([s['id'] for s in sel_students].index(student['id'])) # Removes Logged-In Student
            gender_filter = lambda x: student['gender'] == "-" or x['gender'] == "-" or x['gender'] == student['gender']
            sel_students = list(filter(gender_filter, sel_students)) # Takes out other gender
            num_prefs = len(sel_students) if len(sel_students) < 5 else 5
            # Autofill Preferences (if logged in)
            prefs = []
            prev_submitted = db.check_student_preferences(trip_id, student['id']) 
            if prev_submitted:
                prefs = db.get_student_preferences(trip_id, student['id'], return_prefs_only=True)
            return render_template("student-pref-2.html", student=student, trip_id=trip_id, sel_trip=sel_trip,num_prefs=num_prefs, sel_students=sel_students, autofill=prev_submitted, prefs=prefs)
        else:
            return render_template("trip-error.html")
    else:
        pref_1 = pref_2 = pref_3 = pref_4 = pref_5 = None
        self_id = student['id']
        if 'pref_1' in request.form:
            pref_1 = request.form['pref_1']
        if 'pref_2' in request.form:
            pref_2 = request.form['pref_2']
        if 'pref_3' in request.form:
            pref_3 = request.form['pref_3']
        if 'pref_4' in request.form:
            pref_4 = request.form['pref_4']
        if 'pref_5' in request.form:
            pref_5 = request.form['pref_5']
        db.add_preferences(trip_id, self_id, (pref_1, pref_2, pref_3, pref_4, pref_5))
        #print(db.get_all_trip_preferences())
        return render_template("success.html", sel_trip = db.get_trip_by_id(trip_id))
    
@app.route("/trips", methods=["GET", "POST"])
def trips():
    if request.method == "GET":
        return render_template("trips.html", all_trips = db.get_all_trips(), trip_studs = [db.get_students_in_trip(t['id']) for t in db.get_all_trips()], all_students=db.get_all_students())

@app.route("/trips/<trip_id>", methods=["GET", "POST"])
def trip(trip_id):
    if request.method == "GET":
        if db.get_trip_by_id(trip_id) != None:
            student_prefs = {}
            for s in db.get_students_in_trip(trip_id):
                student_prefs[s['id']] = db.check_student_preferences(trip_id, s["id"])
            return render_template("trip.html", trip_id = trip_id, sel_trip = db.get_trip_by_id(trip_id), sel_students = db.get_students_in_trip(trip_id), student_prefs = student_prefs, all_students=db.get_all_students())
        else:
            return render_template("trip-error.html")

@app.route("/trips/<trip_id>/groups", methods=["GET", "POST"])
def groups(trip_id):
    if request.method == "GET":
        if db.get_trip_by_id(trip_id) != None:
            student_prefs = {}
            for s in db.get_students_in_trip(trip_id):
                student_prefs[s['id']] = db.check_student_preferences(trip_id, s['id'])
            return render_template("groups.html", trip_id = trip_id, sel_trip = db.get_trip_by_id(trip_id), student_prefs = student_prefs, groups = db.get_groups_in_trip(trip_id))
        else:
            return render_template("trip-error.html")

@app.route("/create_trip", methods=["POST"])
def create_trip():
    if request.method == "POST":
        data = request.get_json()[0]
        name = data['name']
        organizer = data['organizer']
        students = data['students']
        num_groups = data['num_groups']
        group_size = data['group_size']
        print(data)
        db.add_trip(Trip(None, name, organizer, num_groups, group_size, "", students))
        return redirect("/trips")

@app.route("/delete_trip", methods=["POST"])
def delete_trip():
    if request.method == "POST":
        data = request.get_json()[0]
        id = data['id']
        db.remove_trip(id)
        return redirect("/trips")

@app.route("/update_trip", methods=["POST"])
def update_trip():
    if request.method == "POST":
        data = request.get_json()[0]
        id = data['id']
        trip = Trip.get_trip_with_id(id)
        if "students" in data:
            students = data['students']
            db.update_students_in_trip(id, students)
        else:
            if "name" in data:
                name = data['name']
                trip.set_name(name)
            if "organizer" in data:
                organizer = data['organizer']
                trip.set_organizer(organizer)
            if "numGroups" in data:
                num_groups = data['numGroups']
                trip.set_num_groups(num_groups)
            if "groupSize" in data:
                group_size = data['groupSize']
                trip.set_group_size(group_size)
            db.update_trip(trip)
        return redirect(f"/trips/{id}")

@app.route("/generate_groups", methods=["POST"])
def generate_groups():
    if request.method == "POST":
        data = request.get_json()
        id = data['id']
        db.generate_groups(id)
        return redirect(f"/trips/{id}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="4000", debug=True)