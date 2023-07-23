# |-------------------------------------------------------------------------{ Imports & Variables }-------------------------------------------------------------------------|
from flask import Flask, render_template, redirect, request, session, abort, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from functools import wraps

# Stores current user and student
current_user = { "db_user": None, "teacher": None, "student": None }

# Create Flask App
app = Flask(__name__)

# Set configs from config.py
app.config.from_pyfile('config.py')

# SQLAlchemy and Mail
db = SQLAlchemy(app)
mail = Mail(app)

# Imports Very Important Classes
from classes import Setup, User, Trip, Student, Teacher, TripStudent, StudentPreference

# Initializes Databse Tables, Users, and Test Trips
# (Find a better way to do this when hosting)
Setup.init_database()


# |------------------------------------------------------------------------{ Permission Decorators }------------------------------------------------------------------------|
# Decorator for login-only routes, also forces verification
def login_required(disable_verify=False):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or current_user['db_user'] is None:
                return redirect("/login")
            elif not disable_verify and current_user['db_user'] is not None and not current_user['db_user'].is_verified:
                if not current_user['db_user'].is_resetting:
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
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Decorator for teacher-only routes
def teacher_only(f):
    @wraps(f)
    @login_required()
    def decorated_function(*args, **kwargs):
        if not current_user['db_user'].is_teacher:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Decorator for teacher-only routes
def student_only(f):
    @wraps(f)
    @login_required()
    def decorated_function(*args, **kwargs):
        if not current_user['db_user'].is_student:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# |------------------------------------------------------------------------{ Main Flask App Routes }------------------------------------------------------------------------|
# Triggered before every request, updates 'current_user' using session id
@app.before_request
def before_request():
    if 'user_id' in session:
        if User.check_exist_with_id(session['user_id']):
            current_user['db_user'] = User.get_user_by_id(session['user_id'])
            if current_user['db_user'].is_teacher:
                current_user['teacher'] = Teacher.get_teacher_by_id(current_user['db_user'].teacher_id)
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

# Handles Error 403: Forbidden
@app.errorhandler(403)
def forbidden(e):
  return render_template("error/403.html")

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
        # Check if user account already exists
        if User.check_exist_with_email(email):
            flash('A user already exists with this email! Please <a href="/login">login</a> instead.', 'danger')
        
        elif len(email_split) != 2 or email_split[1] != "acs.sch.ae":
            flash("Invalid email! Please use an actual ACS (@acs.sch.ae) student email.", 'danger')

        # Check if password length is at least 8
        elif len(password) < 8:
            e = email
            flash("Your password must be at least 8 characters!", 'danger')

        # Check if password matches repeat password
        elif password != password_verify:
            e = email
            p1 = password
            flash("Your passwords must match! Please repeat your password.", 'danger')

        # If email exists in ACS student database
        elif Student.check_student_email(email) or Teacher.check_teacher_email(email):
            is_student = Student.check_student_email(email)
            is_teacher = Teacher.check_teacher_email(email)
            teacher_id = student_id = None
            # Get existing user info
            if is_student:
                user = Student.get_student_by_email(email)
                student_id = user['id']
            if is_teacher:
                user = Teacher.get_teacher_by_email(email)
                teacher_id = user['id']
            student_name = Student.get_student_by_email(email)['name']
            # Create User, login, and send signup/verification email
            new_user = User(is_student=is_student, student_id=student_id, is_teacher=is_teacher, teacher_id=teacher_id, name=student_name, email=email, password=password)
            new_user.login()
            new_user.send_signup_email()
            # Redirect to "/trips" or "/student"
            if current_user['db_user'].is_teacher:
                return redirect("/teacher")
            else:
                return redirect("/student")
        # Email doesn't exist in student databse
        else:
            flash("This email doesn't exist! Please use an actual ACS student email. Email tsu@acs.sch.ae if you think this is a mistake.", 'danger')
            
        return render_template("auth/signup.html", e=e, p1=p1)

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
                initial = not user.is_resetting
                user.verify(initial=initial)
                flash("Email Verified Successfully!", 'success')
                return redirect("/")
        else:
            error = "Incorrect verification code. Please check if the code you entered matches the one in your email inbox."
    if error:
        flash(error, 'danger')
    return render_template("auth/verify.html",time=time, email=email, user_id=user_id, code=code)

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
        
        # Check if user exists, continue login process
        if User.check_exist_with_email(email):
            login_user = User.get_user_by_email(email)

            # Check password with stores password hash
            if login_user.check_password(password):

                # Login and redirect user based on permissions
                login_user.login()
                flash(f"Logged in as {current_user['db_user'].name}!", 'success')
                if current_user['db_user'].is_admin:
                    return redirect("/admin")
                if current_user['db_user'].is_teacher:
                    return redirect("/teacher")
                if current_user['db_user'].is_student:
                    return redirect("/student")
            # Wrong password
            # TODO: Reset password option
            else:
                flash("Wrong password! Please try again.", 'danger')

        # Check if email has proper structure, acs.sch.ae domain, and exists in ACS student database
        elif len(email_split) != 2 or email_split[1] != "acs.sch.ae":
            flash("Invalid email! Please use an actual ACS (@acs.sch.ae) student email.", 'danger')
        # Unregistered Email
        else:
            flash('This email isn\'t linked to an account! Please <a href="/signup">sign up</a>.', 'danger')
        return render_template("auth/login.html")

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
        if current_user['teacher'] is not None:
            current_user['teacher'] = None
        flash("Logged out successfully", 'success')
    return redirect("/")
    #return render_template("auth/logout.html")

# Student Dashboard
# TODO: Reset Password Feature
@app.route("/student", methods=["GET", "POST"])
@student_only
def student():
    student = current_user['student']
    if request.method == "GET":
        # Gets Student Info, Trips
        student_trips = TripStudent.get_trips_by_student(student['id'], return_dict=True)
        trip_studs = [TripStudent.get_students_in_trip(trip['id']) for trip in student_trips]

        # Gets User Info
        user = current_user['db_user']
        info = {
            "user_name": user.name, 
            "login_email": user.email, 
            "is_student": user.is_student,
            "is_teacher": user.is_teacher,
            "is_admin": user.is_admin, 
            "date_created": user.date_created, 
            "date_verified": user.date_verified
        }
        return render_template("student/student.html", student=student, student_trips=student_trips, trip_studs=trip_studs, info=info)
    else:
        data = request.get_json()
        if data['cmd'] == "updateStudent":
            Student.get_student_by_id(student['id'], return_dict=False).update(data)
            flash("Student Information Updated!", 'success')
        return redirect("/student")

# Student Preferences Form
@app.route("/student/<trip_code>", methods=["GET", "POST"])
@student_only
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
@app.route("/teacher", methods=["GET", "POST"])
@teacher_only
def trips():
    # Gets teacher and user info
    teacher = current_user['teacher']
    main_teacher = False
    user = current_user['db_user']
    info = {
        "user_name": user.name, 
        "login_email": user.email, 
        "is_student": user.is_student,
        "is_teacher": user.is_teacher,
        "is_admin": user.is_admin, 
        "date_created": user.date_created, 
        "date_verified": user.date_verified
    }

    # Gets all trips and students
    all_trips = Trip.get_trips_by_teacher_id(teacher['id'])
    if Teacher.check_main(teacher['email']):
        main_teacher = True
        all_trips = Trip.get_all_trips()
    trip_studs = [TripStudent.get_students_in_trip(t.id) for t in all_trips]
    all_students = Student.get_all_students()
    if request.method == "POST":
        data = request.get_json()
        if data['cmd'] == "createTrip":
            name = data['name']
            organizer = data['organizer']
            students = data['students']
            num_groups = data['num_groups']
            group_size = data['group_size']
            teacher_id = teacher['id']
            print(data)
            Trip(name=name, organizer=organizer, teacher_id=teacher_id, num_groups=num_groups, group_size=group_size, students=students)
            flash("New Trip Created!", 'success')
        elif data['cmd'] == "updateTeacher":
            if 'email' in data and not Teacher.check_teacher_email(data['email']):
                flash("Teacher NOT Updated: Invalid Email!", 'danger')
            else:
                Teacher.get_teacher_by_id(teacher['id'], return_dict=False).update(data)
                flash("Teacher Information Updated!", 'success')
    return render_template("teacher/teacher.html", main_teacher=main_teacher, teacher=teacher, all_trips=all_trips, trip_studs=trip_studs, all_students=all_students, info=info)

# Speciic Trip Page
@app.route("/teacher/<trip_code>", methods=["GET", "POST"])
@teacher_only
def trip(trip_code):
    main_teacher = Teacher.check_main(current_user['teacher']['email'])
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
            return render_template("teacher/trip.html", main_teacher=main_teacher, trip_code=trip_code, sel_trip=sel_trip, sel_students=sel_students, student_prefs=student_prefs, all_students=all_students)
        else:
            return render_template("error/invalid-trip.html")
    else:
        data = request.get_json()
        if data['cmd'] in ["updateTripInfo", "updateTripStudents"]:
            flash("Trip Updated!.", 'success')
            Trip.get_trip_by_code(trip_code).update(data)
            
        elif data['cmd'] == "deleteTrip":
            Trip.get_trip_by_code(trip_code).delete()
            flash("Trip Deleted!.", 'success')
            return redirect("/teacher")
        return redirect(f"/teacher/{trip_code}")

# Groups Page for Trip
@app.route("/teacher/<trip_code>/groups", methods=["GET", "POST"])
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
            flash("Groups Generated!.", 'success')
        return redirect(f"/teacher/{trip_code}/groups")


@app.route("/admin", methods=["GET", "POST"])
@admin_only
def admin():
    return render_template("/admin/admin.html")
    
@app.route("/admin/users", methods=["GET", "POST"])
@admin_only
def admin_users():
    get_flashed_messages()
    # Get all users
    users = User.get_all_users(return_dict=True)
    # Set student for each user
    for u in users:
        u['student'] = u['teacher'] = None
        if u['student_id'] is not None:
            u['student'] = Student.get_student_by_id(u['student_id'])
        if u['teacher_id'] is not None:
            u['teacher'] = Teacher.get_teacher_by_id(u['teacher_id'])

    # Get all teachers
    teachers = Teacher.get_all_teachers(return_dict=True)
    
    # Get all students
    students = Student.get_all_students(return_dict=True)
    if request.method == "POST":
        data = request.get_json()

        if data['cmd'] == "updateUser":
            id = data['id']
            user = User.get_user_by_id(id)
            if 'email' in data and User.check_exist_with_email(data['email']):
                flash("User NOT Updated: Login Email Already Exists!", 'danger')
            elif id == current_user['db_user'].id:
                flash("User NOT Updated: You cannot update yourself!", 'danger')
            elif user is not None:
                user.update(data)
                flash("User Updated!", 'success')
       
        elif data['cmd'] == "createUser":
            email = data['email']
            student_id = data['student_id'] if 'student_id' in data else None
            teacher_id = data['teacher_id'] if 'teacher_id' in data else None
            if User.check_exist_with_email(email):
                flash("User NOT Created: Login Email Already Exists!", 'danger')
            elif student_id is not None and Student.get_student_by_id(student_id) is None:
                flash("User NOT Created: Invalid Student ID!", 'danger')
            elif teacher_id is not None and Teacher.get_teacher_by_id(teacher_id) is None:
                flash("User NOT Created: Invalid Teacher ID!", 'danger')
            else:
                name = data['name']
                verified = data['verified']
                is_admin = data['admin']
                is_teacher = data['teacher']
                is_student = data['student']
                password = data['password']
                User(name=name, is_admin=is_admin, is_teacher=is_teacher, is_student=is_student, student_id=student_id, teacher_id=teacher_id, email=email, is_verified=verified, password=password)
                flash("User Created!", 'success')
        
        elif data['cmd'] == "deleteUser":
            user_id = data['id']
            if user_id == current_user['db_user'].id:
                flash("You cannot delete yourself!", 'danger')
            elif User.check_exist_with_id(user_id):
                User.get_user_by_id(user_id).delete()
                flash("User Deleted!", 'success')

    return render_template("admin/users.html", users=users, teachers=teachers, students=students)

@app.route("/admin/students", methods=["GET", "POST"])
@admin_only
def admin_students():
    # Get all students
    students = Student.get_all_students(return_dict=True)
    if request.method == "POST":
        data = request.get_json()
        if data['cmd'] == "updateStudent":
            student = Student.get_student_by_id(data['id'], return_dict=False)
            email_check = Student.check_student_email(data['email']) if "email" in data else True
            if student is not None and email_check:
                student.update(data)
                flash("Student Updated!", 'success')
            else:
                flash("Student NOT Updated: Invalid Email!", 'danger')
        
        elif data['cmd'] == "addStudent":
            email = data['email']
            if not Student.check_student_email(email):
                name = data['name']
                grade = data['grade']
                gender = data['gender']
                Student(name=name, email=email, grade=grade, gender=gender)
                flash("Student Added!", 'success')
            else:
                flash("Student NOT Added: Email Already Exists!", 'danger') 

        elif data['cmd'] == "deleteStudent":
            student_id = data['id']
            if Student.get_student_by_id(student_id) is not None:
                Student.get_student_by_id(student_id, return_dict=False).delete()
                flash("Student Deleted!", 'success')
    return render_template("admin/students.html", students=students)

@app.route("/admin/teachers", methods=["GET", "POST"])
@admin_only
def admin_teachers():
    # Get all students
    teachers = Teacher.get_all_teachers(return_dict=True)
    if request.method == "POST":
        data = request.get_json()
        if data['cmd'] == "updateTeacher":
            teacher = Teacher.get_teacher_by_id(data['id'], return_dict=False)
            email_check = Teacher.check_teacher_email(data['email']) if "email" in data else True
            if teacher is not None and email_check:
                teacher.update(data)
                flash("Teacher Updated!", 'success')
            else:
                flash("Teacher NOT Updated: Invalid Email!", 'danger')
        
        elif data['cmd'] == "addTeacher":
            email = data['email']
            if not Teacher.check_teacher_email(email):
                name = data['name']
                email = data['email']
                title = data['title']
                photoUrl = data['photoUrl'] if 'photoUrl' in data else None
                Teacher(name=name, email=email, title=title, photoUrl=photoUrl)
                flash("Teacher Added!", 'success')
            else:
                flash("Teacher NOT Added: Email Already Exists!", 'danger') 

        elif data['cmd'] == "deleteTeacher":
            teacher_id = data['id']
            if Teacher.get_teacher_by_id(teacher_id) is not None:
                Teacher.get_teacher_by_id(teacher_id, return_dict=False).delete()
                flash("Teacher Deleted!", 'success')
    return render_template("admin/teachers.html", teachers=teachers)

# |--------------------------------------------------------------------------{ POST-Only Routes }---------------------------------------------------------------------------|
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