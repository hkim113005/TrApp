# |-------------------------------------------------------------------------{ Imports & Variables }-------------------------------------------------------------------------|
from flask import Flask, render_template, redirect, request, session, abort
from functools import wraps

# Stores current user and student
current_user = { "db_user": None, "student": None }

# Create Flask App
app = Flask(__name__)

# Set configs from config.py
app.config.from_pyfile('config.py')

# Imports Very Important Classes
from classes import DB, User, Trip, Student, TripStudent, StudentPreference

# Initializes Databse Tables, Users, and Test Trips
# (Find a better way to do this when hosting)
if not DB.initialized:
    DB.init_database()


# |------------------------------------------------------------------------{ Permission Decorators }------------------------------------------------------------------------|
# Decorator for login-only routes, also forces verification
def login_required(disable_verify=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or current_user['db_user'] is None:
                return redirect("/login")
            elif not disable_verify and current_user['db_user'] is not None and not current_user['db_user'].is_verified:
                return redirect("/verify")
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Decorator for admin-only routes
def admin_only(f):
    @wraps(f)
    @login_required()
    def decorated_function(*args, **kwargs):
        if not current_user['db_user'].is_admin:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

# Decorator for teacher-only routes
def teacher_only(f):
    @wraps(f)
    @login_required()
    def decorated_function(*args, **kwargs):
        if not current_user['db_user'].is_teacher:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function


# |------------------------------------------------------------------------{ Main Flask App Routes }------------------------------------------------------------------------|
# Triggered before every request, updates 'current_user' using session id
@app.before_request
def before_request():
    if 'user_id' in session:
        if User.check_exist_with_id(session['user_id']):
            current_user['db_user'] = User.get_user_by_id(session['user_id'])
            if current_user['db_user'].is_student:
                current_user['student'] = Student.get_student_by_id(current_user['db_user'].student_id)

# Home Page
@app.route("/", methods=["GET"])
def home():
    global current_user
    logged_in = current_user['db_user'] is not None
    is_teacher = is_student = is_admin = False
    if logged_in:
        is_admin = current_user['db_user'].is_admin
        is_teacher = current_user['db_user'].is_teacher
        is_student = current_user['db_user'].is_student
    print(current_user)
    return render_template("home.html", logged_in=logged_in, is_admin=is_admin, is_teacher=is_teacher, is_student=is_student)

# Handles Error 404: Page Not Found
@app.errorhandler(404)
def page_not_found(e):
  return render_template("error/404.html")

# Handles Error 401: Unauthorized
@app.errorhandler(401)
def unauthorized(e):
  return render_template("error/401.html")

# Handles Error 500: Server Error
@app.errorhandler(500)
def server_error(e):
  return render_template("error/500.html")

# Sign Up (New User)
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("auth/signup.html")
    else:
        e = p1 = None
        global current_user
        
        # Get Sign Up info from form
        email = request.form['email'].lower().strip()
        password = request.form['password'].strip()
        password_verify = request.form['password_confirm'].strip()
        email_split = email.split("@")

        # Check if email has proper structure and acs.sch.ae domain
        if len(email_split) != 2 or email_split[1] != "acs.sch.ae":
            error = "Invalid email! Please use an actual ACS (@acs.sch.ae) student email."

        # Check if password length is at least 8
        elif len(password) < 8:
            e = email
            error = "Your password must be at least 8 characters!"

        # Check if password matches repeat password
        elif password != password_verify:
            e = email
            p1 = password
            error = "Your passwords must match! Please repeat your password."

        # Check if user account already exists
        elif User.check_exist_with_email(email):
            error = 'A user already exists with this email! Please <a href="/login">login</a> instead.' # TODO: Reset password option

        # If email exists in ACS student database
        elif Student.check_student_email(email):
            # Get existing user info
            user = Student.get_student_by_email(email)
            student_id = user['id']
            student_name = Student.get_student_by_email(email)['name']
            # Create User, login, and send signup/verification email
            new_user = User(is_student=True, student_id=student_id, name=student_name, email=email, password=password)
            new_user.create()
            new_user.login()
            new_user.send_signup_email()
            # Redirect to "/trips" or "/student"
            if current_user['db_user'].is_teacher:
                return redirect("/trips")
            else:
                return redirect("/student")
        # Email doesn't exist in student databse
        else:
            error = "This email doesn't exist! Please use an actual ACS student email. Email tsu@acs.sch.ae if you think this is a mistake."
        return render_template("auth/signup.html", error=error, e=e, p1=p1)

# Email Verification OTP
@app.route("/verify", methods=["GET", "POST"])
@login_required(disable_verify=True)
def verify():
    error = code = None
    user = current_user['db_user']
    email = user.email
    user_id = user.id

    # Verification time expired
    if user.verify_time_expired():
        error = "Your verification code has expired. Please click \"Redo Verification\" to generate a new one."
        time = 0
    else:
        time = user.get_remaining_time()
    
    if request.method == "GET":
        # Redirect to homepage if already verified
        if current_user["db_user"].is_verified:
            return redirect("/")
        # Get verification code url parameter for autofill
        code = request.args.get("code")
    else:
        # Get verification code from form
        verify_code = ""
        for i in range(1, 7):
            verify_code += request.form[f"ch_{i}"]
        
        # Check verification form, verify if correct
        if user.check_verify_code(verify_code):
            if not error:
                user.verify()
                return redirect("/")
        else:
            error = "Incorrect verification code. Please check if the code you entered matches the one in your email inbox."
    return render_template("auth/verify.html", error=error, time=time, email=email, user_id=user_id, code=code)

# Existing User Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")
    else:
        global current_user

        # Get Login Info from form
        email = request.form['email'].lower().strip()
        password = request.form['password'].strip()
        email_split = email.split("@")

        # Check if email has proper structure, acs.sch.ae domain, and exists in ACS student database
        if len(email_split) != 2 or email_split[1] != "acs.sch.ae":
            error = "Invalid email! Please use an actual ACS (@acs.sch.ae) student email."
        
        # Check if user exists, continue login process
        elif User.check_exist_with_email(email):
            login_user = User.get_user_by_email(email)

            # Check password with stores password hash
            if login_user.check_password(password):

                # Login and redirect user based on permissions
                login_user.login()
                if current_user['db_user'].is_admin:
                    return redirect("/admin")
                if current_user['db_user'].is_teacher:
                    return redirect("/trips")
                if current_user['db_user'].is_student:
                    return redirect("/student")
            # Wrong password
            # TODO: Reset password option
            else:
                error = "Wrong password! Please try again."
        # Unregistered Email
        else:
            error = 'This email isn\'t linked to an account! Please <a href="/signup">sign up</a>.'
        return render_template("auth/login.html", error=error)

# Logout
@app.route("/logout", methods=["GET", "POST"])
@login_required(disable_verify=True)
def logout():
    # Log Out User - Clear session and reset `current_user`
    global session
    if request.method == "POST":
        if 'user_id' in session:
            session.clear()
        if current_user['db_user'] is not None:
            current_user['db_user'] = None
        if current_user['student'] is not None:
            current_user['student'] = None
    return redirect("/")
    #return render_template("auth/logout.html")

# Student Dashboard
# TODO: Reset Password Feature
@app.route("/student", methods=["GET", "POST"])
@login_required()
def student():
    student = current_user['student']
    if request.method == "GET":
        # Gets Student Info, Trips
        student_trips = TripStudent.get_trips_by_student(student['id'], return_dict=True)
        trip_studs = [TripStudent.get_students_in_trip(trip['id']) for trip in student_trips]

        # Gets User Info
        user = current_user['db_user']
        info = {"user_name": user.name, "date_created": user.date_created, "date_verified": user.date_last_verify}
        return render_template("student/student.html", student=student, student_trips=student_trips, trip_studs=trip_studs, info=info)
    else:
        data = request.get_json()
        if data['cmd'] == "updateStudent":
            student = Student.get_student_by_id(student['id'], return_dict=False).update(data)
        return redirect("/student")

# Student Preferences Form
@app.route("/student/<trip_code>", methods=["GET", "POST"])
@login_required()
def student_preferences(trip_code):
    global current_user
    student = current_user['student']
    trip = Trip.get_trip_by_code(trip_code)
    if request.method == "GET":
        if trip != None:
            sel_trip = trip
            # Create student options
            sel_students = TripStudent.get_students_in_trip(trip.id)
            student_ids = [s['id'] for s in sel_students]
            sel_students.pop(student_ids.index(student['id'])) # Removes current (logged-in) student
            gender_filter = lambda x: student['gender'] == "-" or x['gender'] == "-" or x['gender'] == student['gender']
            sel_students = list(filter(gender_filter, sel_students)) # Takes out other gender
            num_prefs = len(sel_students) if len(sel_students) < 5 else 5 # Adjust preference count
            
            # Autofill Preferences
            prefs = []
            prev_submitted = StudentPreference.check_student_preferences(trip.id, student['id']) 
            if prev_submitted:
                prefs = StudentPreference.get_preferences(trip.id, student['id'], return_prefs_only=True)
            return render_template("student/preference-form.html", student=student, trip_code=trip_code, sel_trip=sel_trip,num_prefs=num_prefs, sel_students=sel_students, autofill=prev_submitted, prefs=prefs)
        else:
            return render_template("error/invalid-trip.html")
    else:
        # Get Preferences from form
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
        preferences = [pref_1, pref_2, pref_3, pref_4, pref_5]
        # Update preferences if student is editing preferences
        if StudentPreference.check_student_preferences(trip.id, self_id):
            if StudentPreference.check_different_preferences(trip.id, self_id, preferences):
                p = StudentPreference.get_preferences(trip.id, self_id)
                p.update(preferences)
                current_user['db_user'].send_preferences_email(trip.id, updated=True)
        # Create new StudentPreference object if student is submitting for the first time
        else:
            StudentPreference(trip_id=trip.id, student_id=self_id, preferences=preferences)
            current_user['db_user'].send_preferences_email(trip.id)
        return render_template("student/prefs-submitted.html", trip_code=trip_code)
    
# All Trips Page
@app.route("/trips", methods=["GET", "POST"])
@teacher_only
def trips():
    if request.method == "GET":
        # Gets all trips and students
        all_trips = Trip.get_all_trips()
        trip_studs = [TripStudent.get_students_in_trip(t.id) for t in all_trips]
        all_students = Student.get_all_students()
        return render_template("teacher/trips.html", all_trips=all_trips, trip_studs=trip_studs, all_students=all_students)

# Speciic Trip Page
@app.route("/trips/<trip_code>", methods=["GET", "POST"])
@teacher_only
def trip(trip_code):
    if request.method == "GET":
        sel_trip = Trip.get_trip_by_code(trip_code, return_dict=True)

        # Check if trip code matches valid trip
        if sel_trip != None:
            student_prefs = {}
            sel_students = TripStudent.get_students_in_trip(sel_trip['id'])
            all_students = Student.get_all_students()

            # Fill up student_prefs with whether the student has submitted their preferences
            for s in sel_students:
                student_prefs[s['id']] = StudentPreference.check_student_preferences(sel_trip['id'], s['id'])
            return render_template("teacher/trip.html", trip_code=trip_code, sel_trip=sel_trip, sel_students=sel_students, student_prefs=student_prefs, all_students=all_students)
        else:
            return render_template("error/invalid-trip.html")

# Groups Page for Trip
@app.route("/trips/<trip_code>/groups", methods=["GET", "POST"])
@teacher_only
def groups(trip_code):
    sel_trip = Trip.get_trip_by_code(trip_code)
    if request.method == "GET":
        if Trip.get_trip_by_code(trip_code) != None:
            student_prefs = {}
            for s in TripStudent.get_students_in_trip(sel_trip.id):
                student_prefs[s['id']] = StudentPreference.check_student_preferences(sel_trip.id, s['id'])
            groups = sel_trip.get_groups()
            generated = len(groups['groups'][0]) > 0
            return render_template("teacher/groups.html", trip_code=trip_code, sel_trip=sel_trip, student_prefs=student_prefs, groups=groups, generated=generated)
        else:
            return render_template("error/invalid-trip.html")
    else:
        data = request.get_json()
        if data['cmd'] == "generateGroups":
            sel_trip.generate_groups()
        return redirect(f"/trips/{trip_code}/groups")

# Admin Dashboard
# TODO: User/Student Management:
#   - Edit User Details
#   - Add New User
#   - Edit Student Details
#   - Add New Student
#   - Delete Student
@app.route("/admin", methods=["GET", "POST"])
@admin_only
def admin():
    if request.method == "GET":
        # Get all users
        users = User.get_all_users(return_dict=True)
        # Set student for each user
        for u in users:
            if u['student_id'] is not None:
                u['student'] = Student.get_student_by_id(u['student_id'])
            else:
                u['student'] = None
        # Get all students
        students = Student.get_all_students()
        return render_template("admin/admin.html", users=users, students=students)
    else:
        data = request.get_json()
        if data['cmd'] == "deleteUser":
            user_id = data['id']
            if User.check_exist_with_id(user_id):
                User.get_user_by_id(user_id).delete()
        return redirect("/admin")


# |--------------------------------------------------------------------------{ POST-Only Routes }---------------------------------------------------------------------------|
@app.route("/create_trip", methods=["POST"])
@teacher_only
def create_trip():
    data = request.get_json()
    name = data['name']
    organizer = data['organizer']
    students = data['students']
    num_groups = data['num_groups']
    group_size = data['group_size']
    print(data)
    Trip(name=name,organizer=organizer, num_groups=num_groups, group_size=group_size, students=students)
    return redirect("/trips")

@app.route("/delete_trip", methods=["POST"])
@teacher_only
def delete_trip():
    data = request.get_json()
    code = data['code']
    Trip.get_trip_by_code(code).delete()
    return redirect("/trips")

@app.route("/update_trip", methods=["POST"])
@teacher_only
def update_trip():
    data = request.get_json()
    code = data['code']
    trip = Trip.get_trip_by_code(code)
    trip.update(data)
    return redirect(f"/trips/{code}")

@app.route("/redo_verify", methods=["POST"])
@login_required(disable_verify=True)
def redo_verify():
    if request.method == "POST":
        data = request.get_json()
        id = data['id']
        if User.check_exist_with_id(id):
            u = User.get_user_by_id(id)
            if u.verify_time_expired():
                u.regenerate_verify_code()
                if not u.is_verified:
                    u.send_verify_email()
        return redirect("/verify")

# |--------------------------------------------------------------------------{ Main Function :D }---------------------------------------------------------------------------|
if __name__ == "__main__":
    app.run(debug=True)