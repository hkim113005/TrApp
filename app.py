from flask import Flask, render_template, redirect, request, session, abort
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

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
app.config.from_pyfile('config.py')
auth_db = SQLAlchemy(app)

# Teacher Login Credentials
ADMIN = {
    "email": "tsu@acs.sch.ae",
    "password": "admin"
}

# Teacher Login Credentials
TEACHER = {
    "email": "//--@acs.sch.ae",
    "password": "ACSTeachers2023"
}

# TODO: User Class
class User (auth_db.Model, UserMixin):
    is_initialized = False

    id = auth_db.Column(auth_db.Integer, primary_key=True)
    is_admin = auth_db.Column(auth_db.Boolean, nullable=False, default=False)
    is_teacher = auth_db.Column(auth_db.Boolean, nullable=False, default=False)
    is_student = auth_db.Column(auth_db.Boolean, nullable=False, default=False)
    name = auth_db.Column(auth_db.String(255), nullable=False)
    student_id = auth_db.Column(auth_db.Integer, nullable=True)
    email = auth_db.Column(auth_db.String(255), nullable=False)
    email_verified = auth_db.Column(auth_db.Boolean, nullable=False, default=False)
    verifiy_token = auth_db.Column(auth_db.String, nullable=True)
    hashed_password = auth_db.Column(auth_db.String, nullable=False)
    
    def __init__(self, name, email, password, is_admin=False, is_teacher=False, is_student=False, student_id=None, **kwargs):
        super(User, self).__init__(**kwargs)
        self.name = name
        self.email = email
        self.hashed_password = generate_password_hash(password, method="scrypt")
        self.is_admin = is_admin
        self.is_teacher = is_teacher
        self.is_student = is_student
        self.student_id = student_id
        self.verify_token = "XXX" #TODO
    
    def create(self):
        auth_db.session.add(self)
        auth_db.session.commit()
    
    def login(self):
        session.permanent = True
        session['user_id'] = self.id
        current_user['db_user'] = self
        if current_user['db_user'].is_student:
            current_user['student'] = db.get_student_by_id(self.student_id)
        print(f"Succesfully Logged in as {self.name}")
    
    def check_password(self, plain_pass):
        return check_password_hash(self.hashed_password, plain_pass)
    
    @staticmethod
    def init_database():
        with app.app_context():
            inspector = auth_db.inspect(auth_db.engine)
            if not "user" in inspector.get_table_names():
                print("Creating user Databse Table")
                auth_db.create_all()
            if not User.check_exist_with_id(0):
                print("Adding Admin to Database")
                admin = User(id=0, is_admin=True, is_teacher=True,is_student=True, name="TSU Admin", student_id=0,email=ADMIN['email'], password=ADMIN['password'])
                admin.create()
            if not User.check_exist_with_id(1):
                print("Adding Teacher to Database")
                teacher = User(id=1, is_teacher=True,name="ACS Teacher", email=TEACHER['email'], password=TEACHER['password'])
                teacher.create()
            User.is_initialized = True
            print("Initialization Complete")

    @staticmethod
    def get_all_users():
        return auth_db.session.query(User).all()
    
    @staticmethod
    def get_user_by_email(email):
        return auth_db.session.query(User).filter_by(email=email).first()

    @staticmethod
    def get_user_by_id(id):
        return auth_db.session.query(User).filter_by(id=id).first()

    @staticmethod
    def check_exist_with_email(email):
        return User.get_user_by_email(email) is not None

    @staticmethod
    def check_exist_with_id(id):
        return User.get_user_by_id(id) is not None

current_user = {
    "db_user": None,
    "student": None
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def login_not_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user['db_user'] is not None and not current_user['db_user'].is_admin:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def teacher_only(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user['db_user'] is not None and not current_user['db_user'].is_teacher:
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    if not User.is_initialized:
        print("Initializing...")
        User.init_database()
    if current_user['db_user'] is None and 'user_id' in session:
        if User.check_exist_with_id(session['user_id']):
            current_user['db_user'] = User.get_user_by_id(session['user_id'])
            if current_user['db_user'].is_student:
                current_user['student'] = db.get_student_by_id(current_user['db_user'].student_id)

@app.route("/", methods=["GET"])
def start():
    global current_user
    logged_in = current_user['db_user'] is not None
    is_teacher = is_student = is_admin = False
    if logged_in:
        is_admin = current_user['db_user'].is_admin
        is_teacher = current_user['db_user'].is_teacher
        is_student = current_user['db_user'].is_student
    print(current_user)
    return render_template("home.html", logged_in=logged_in, is_admin=is_admin, is_teacher=is_teacher, is_student=is_student)

@app.errorhandler(404)
def not_found(e):
  return render_template("error/404.html")

@app.errorhandler(401)
def unauthorized(e):
  return render_template("error/unauthorized.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("auth/register.html")
    else:
        global current_user
        # Get Register Info
        email = request.form['email'].lower().strip()
        password = request.form['password'].strip()
        # Check if email is already used as a user
        if User.check_exist_with_email(email):
            print("[REGISTER] USER ALREADY EXISTS!")
            return render_template("auth/register.html", account_exists=True)
        
        valid_email = db.check_student_email(email)
        # Check if email exists in student database
        if valid_email:
            student_id = db.get_student_by_email(email)['id']
            student_name = db.get_student_by_email(email)['name']
            new_user = User(is_student=True, student_id=student_id, name=student_name, email=email, password=password)
            new_user.create()
            new_user.login()
            # Redirect to either "/trips" or "/student"
            if current_user['db_user'].is_teacher:
                return redirect("/trips")
            else:
                return redirect("/student")
        # Invalid Email (Doesn't exist as a student email)
        print("[REGISTER] INVALID EMAIL")
        return render_template("auth/register.html", invalid_email=True)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")
    else:
        global current_user, session
        # Get Login Info
        email = request.form['email'].lower().strip()
        password = request.form['password'].strip()
        if User.check_exist_with_email(email):
            login_user = User.get_user_by_email(email)
            if login_user.check_password(password):
                login_user.login()
                if current_user['db_user'].is_admin:
                    return redirect("/admin")
                if current_user['db_user'].is_teacher:
                    return redirect("/trips")
                if current_user['db_user'].is_student:
                    return redirect("/student")
        return render_template("auth/login.html", invalid_login=True)

@app.route("/logout", methods=["GET", "POST"])
def logout():
    # Log Out User
    global session
    if request.method == "POST":
        if 'user_id' in session:
            session.clear()
        if current_user['db_user'] is not None:
            current_user['db_user'] = None
        if current_user['db_user'] is not None:
            current_user['student'] = None
        return redirect("/")
        #return render_template("auth/logout.html")

# TODO: Student Page
#   - Reset Password Option
@app.route("/student", methods=["GET", "POST"])
@login_required
def student():
    if request.method == "GET":
        global current_user
        if current_user['db_user'] is not None:
            student = current_user['student']
            student_trips = db.get_trips_by_student(student['id'])
            trip_studs = [db.get_students_in_trip(trip['id']) for trip in student_trips]
            return render_template("student/student.html", student=student, student_trips=student_trips,trip_studs=trip_studs) # Needs to be setup
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
@login_not_required
def trip_search():
    if request.method == "GET":
        if not current_user['db_user'] is not None:
            return render_template("student/trip-search.html")
        else:
            return render_template("error/unauthorized.html")
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
            if current_user['db_user'] is not None:
                return logged_in_preferences(trip_id)
            else:
                return render_template("student/pref-form-1.html", trip_id = trip_id, sel_trip=sel_trip, sel_students=sel_students)
        else:
            return render_template("error/invalid-trip.html")
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
        return render_template("student/prefs-submitted.html", sel_trip = db.get_trip_by_id(trip_id))

@app.route("/student/<trip_id>", methods=["GET", "POST"])
@login_required
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
            return render_template("student/pref-form-2.html", student=student, trip_id=trip_id, sel_trip=sel_trip,num_prefs=num_prefs, sel_students=sel_students, autofill=prev_submitted, prefs=prefs)
        else:
            return render_template("error/invalid-trip.html")
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
        return render_template("student/prefs-submitted.html", sel_trip = db.get_trip_by_id(trip_id))
    
@app.route("/trips", methods=["GET", "POST"])
@teacher_only
def trips():
    if request.method == "GET":
        return render_template("teacher/trips.html", all_trips = db.get_all_trips(), trip_studs = [db.get_students_in_trip(t['id']) for t in db.get_all_trips()], all_students=db.get_all_students())

@app.route("/trips/<trip_id>", methods=["GET", "POST"])
@teacher_only
def trip(trip_id):
    if request.method == "GET":
        if db.get_trip_by_id(trip_id) != None:
            student_prefs = {}
            for s in db.get_students_in_trip(trip_id):
                student_prefs[s['id']] = db.check_student_preferences(trip_id, s["id"])
            return render_template("teacher/trip.html", trip_id = trip_id, sel_trip = db.get_trip_by_id(trip_id), sel_students = db.get_students_in_trip(trip_id), student_prefs = student_prefs, all_students=db.get_all_students())
        else:
            return render_template("error/invalid-trip.html")

@app.route("/trips/<trip_id>/groups", methods=["GET", "POST"])
@teacher_only
def groups(trip_id):
    if request.method == "GET":
        if db.get_trip_by_id(trip_id) != None:
            student_prefs = {}
            for s in db.get_students_in_trip(trip_id):
                student_prefs[s['id']] = db.check_student_preferences(trip_id, s['id'])
            return render_template("teacher/groups.html", trip_id = trip_id, sel_trip = db.get_trip_by_id(trip_id), student_prefs = student_prefs, groups = db.get_groups_in_trip(trip_id))
        else:
            return render_template("error/invalid-trip.html")

@app.route("/admin", methods=["GET", "POST"])
@admin_only
def admin():
    users = User.get_all_users()
    users = [u.__dict__ for u in users]
    return render_template("admin/admin.html", users=users)

# POST-Only Routes
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