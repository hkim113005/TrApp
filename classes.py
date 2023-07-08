import random
import csv
from datetime import datetime, timedelta
from flask import render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Mail, Message
from app import app, current_user

# Admin Login Credentials
ADMIN = {
    "email": "tsu@acs.sch.ae",
    "password": "admin"
}

# Teacher Login Credentials
TEACHER = {
    "email": "//--@acs.sch.ae",
    "password": "ACSTeachers2023"
}

# SQLAlchemy and Mail
db = SQLAlchemy(app)
mail = Mail(app)

# Converts SQL databse row into a standard python dictionary
def dict_converter(row):
    return {column.name: getattr(row, row.__mapper__.get_property_by_column(column).key) for column in row.__table__.columns}

# Initializes databases and adds test trips
class DB:
    STUDENT_CSV = "data/students.csv"
    initialized = False

    @staticmethod
    def init_database():
        if DB.initialized:
            return
        print("Initialization Started")
        with app.app_context():
            table_names = [User.__tablename__, Student.__tablename__, Trip.__tablename__, StudentPreference.__tablename__, TripStudent.__tablename__]
            tables = db.inspect(db.engine).get_table_names()
            if (set(table_names) - set(tables)):
                print("Creating All Databse Tables")
                db.create_all()
            if "students" not in tables:
                file = open(DB.STUDENT_CSV, "r")
                data = list(csv.DictReader(file, delimiter=","))
                file.close()
                Student(id=0, name="Test Student", email="tsu@acs.sch.ae", grade=12, gender="M")
                for s in data:
                    Student(name=s['name'], email=s['email'], grade=s['grade'], gender=s['gender'])
                print("Added Students to Database")
            if not User.check_exist_with_id(0):
                admin = User(id=0, is_admin=True, is_teacher=True, is_student=True, name="TSU Admin", verified=True, student_id=0, email=ADMIN['email'], password=ADMIN['password'])
                admin.create()
                print("Added Admin to Database")
            if not User.check_exist_with_id(1):
                teacher = User(id=1, is_teacher=True, verified=True, name="ACS Teacher", email=TEACHER['email'], password=TEACHER['password'])
                teacher.create()
                print("Added Teacher to Database")
            if not db.session.query(Trip).first():
                DB.create_test_trips()
        DB.initialized = True
        print("Initialization Complete")
    
    def create_test_trips():
        with app.app_context():
            Trip(name="WWW 2023: Grade 6 (Greece)", organizer="MS", num_groups=4, group_size=2, details="blah blah blah", students=[1, 2, 3, 4])
            Trip(name="Viper Venture 2023: Thailand", organizer="HS", num_groups=5, group_size=3, details="idk lol", students=[260, 261, 262])
            Trip(code="TEST11", name="JV Boys Volleyball", organizer="MESAC", num_groups=7, group_size=2, details="eeeeeee", students=[0, 148, 100, 123, 90, 7,21, 150, 230, 190, 72, 110])
            t = Trip(name="Varsity Boys Soccer", organizer="MESAC", num_groups=9, group_size=3, details="aaaaa", students=[21, 150, 230])
            Trip(name="HS Track & Field", organizer="MESAC", num_groups=3, group_size=3, details="yyyyyy", students=[273, 220])
            Trip(name="HS Tennis", organizer="MESAC", num_groups=5, group_size=2, details="xxxxxxx", students=[288, 270, 242, 276])
            Trip(name="HS Wrestling", organizer="MESAC", num_groups=6, group_size=2, details="wwwwww", students=[204])
            Trip(code="TEST22", name="Test Trip", organizer="Tester", num_groups=3, group_size=2, details="aaaaa", students=[0, 642, 631, 604, 573, 641])
            t.update({
                "name": "Varsity Boys Soccer", 
                "organizer": "MESAC", 
                "num_groups": 9, 
                "group_size": 3, 
                "details": "updated soccer", 
                "students": [21, 150, 230, 190, 72, 110, 289, 280]
            })
            print("Created Test Trips")
            print([dict_converter(t) for t in Trip.get_all_trips()])

#  User Database Model - Handles user signup, verification, and login
class User (db.Model):
    __tablename__ = 'users'
    verify_minutes = 3

    # Database User Columns
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_teacher = db.Column(db.Boolean, nullable=False, default=False)
    is_student = db.Column(db.Boolean, nullable=False, default=False)
    name = db.Column(db.String, nullable=False)
    student_id = db.Column(db.Integer, nullable=True)
    date_created = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String, nullable=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    verify_attempts = db.Column(db.Integer, nullable=True, default=0)
    verify_code = db.Column(db.String(6), nullable=True)
    date_last_verify = db.Column(db.DateTime, nullable=True)
    hashed_password = db.Column(db.String, nullable=False)
    
    def __init__(self, password, verified=False,**kwargs):
        super(User, self).__init__(**kwargs)
        self.date_created = datetime.now().replace(microsecond=0)
        self.hashed_password = generate_password_hash(password, method="scrypt")
        self.verify_code = User.get_new_code()
        self.date_last_verify = self.date_created
        if verified:
            self.is_verified = verified;
        if not self.is_verified:
            self.verify_code = User.get_new_code()
    
    def sync(self):
        db.session.merge(self)
        db.session.commit()
        
    def create(self):
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get_remaining_time(self):
        return (timedelta(minutes=User.verify_minutes) - (datetime.now() - self.date_last_verify)).total_seconds() * 1000
    
    def verify_time_expired(self):
        time_elapsed = datetime.now() - self.date_last_verify
        return time_elapsed > timedelta(minutes=User.verify_minutes)

    def check_verify_code(self, code):
        self.verify_attempts += 1
        self.sync()
        if code == self.verify_code:
            return True
        return False
    
    def verify(self):
        self.is_verified = True
        self.sync()
    
    def regenerate_verify_code(self):
        self.date_last_verify = datetime.now().replace(microsecond=0)
        self.verify_code = User.get_new_code()
        self.sync()
    
    def send_email(self, subject, template):
        msg = Message(
            subject,
            recipients=[self.email],
            html=template,
            sender=app.config["MAIL_DEFAULT_SENDER"],
        )
        mail.send(msg)
    
    def send_verify_email(self):
        html = render_template("email/verification.html", name=self.name, code=self.verify_code)
        self.send_email("TrApp | Email Verification", html)
    
    def send_signup_email(self):
        html = render_template("email/signup.html", name=self.name, code=self.verify_code)
        self.send_email("TrApp | Signup & Email Verification", html)

    def login(self):
        session.permanent = True
        session['user_id'] = self.id
        current_user['db_user'] = self
        if current_user['db_user'].is_student:
            current_user['student'] = Student.get_student_by_id(self.student_id)
        self.sync()
        print(f"Succesfully Logged in as {self.name}")
    
    def check_password(self, plain_password):
        return check_password_hash(self.hashed_password, plain_password)

    def reset_password(self, new_password):
        self.hashed_password = generate_password_hash(new_password)
        self.sync()

    @staticmethod
    def get_new_code():
        length = 6
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
        return ''.join(random.sample((chars), length))

    @staticmethod
    def get_all_users(return_dict=False):
        users = db.session.query(User).all()
        if return_dict:
            users = [dict_converter(u) for u in users]
            for u in users:
                if u['date_created'] is not None:
                    u['date_created'] = str(u['date_created'])
                if u['date_last_verify'] is not None:
                    u['date_last_verify'] = str(u['date_last_verify'])
        return users
    
    @staticmethod
    def get_user_by_email(email):
        return db.session.query(User).filter_by(email=email).first()

    @staticmethod
    def get_user_by_id(id):
        return db.session.query(User).filter_by(id=id).first()

    @staticmethod
    def check_exist_with_email(email):
        return User.get_user_by_email(email) is not None

    @staticmethod
    def check_exist_with_id(id):
        return User.get_user_by_id(id) is not None

# Student Databse Model - Stores and handles student info 
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(1), nullable=False, default="-")

    def __init__(self, **kwargs):
        super(Student, self).__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def sync(self):
        db.session.merge(self)
        db.session.commit()
    
    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update_name(self, name):
        self.name = name
        self.sync()
    
    def update_email(self, email):
        self.email = email
        self.sync()
    
    def update_grade(self, grade):
        self.grade = grade
        self.sync()
    
    def update_gender(self, gender):
        self.gender = gender
        self.sync()
    
    def update(self, data):
        if 'name' in data:
            self.update_name(data['name'])
        if 'email' in data:
            self.update_email(data['email'])
        if 'grade' in data:
            self.update_grade(data['grade'])
        if 'gender' in data:
            self.update_gender(data['gender'])

    @staticmethod
    def get_student_by_id(id, return_dict=True):
        student = db.session.query(Student).filter_by(id=id).first()
        if return_dict:
            return dict_converter(student)
        else:
            return student

    @staticmethod
    def get_student_by_email(email):
        student = db.session.query(Student).filter_by(email=email).first()
        return dict_converter(student)

    @staticmethod
    def check_student_email(email):
        student = Student.get_student_by_email(email)
        return student is not None
    
    @staticmethod
    def get_all_students(return_dict=False):
        students = db.session.query(Student).all()
        if return_dict:
            return [dict_converter(s) for s in students] 
        else:
            return students

# Trip Databse Model - Stores and handles trip info 
class Trip(db.Model):
    __tablename__ = 'trips'
    trip_ids = []

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), nullable=False)
    name = db.Column(db.String, nullable=False)
    organizer = db.Column(db.String, nullable=False)
    num_groups = db.Column(db.Integer, nullable=False)
    group_size = db.Column(db.Integer, nullable=False)
    details = db.Column(db.String, nullable=True)

    def __init__(self, students=[], code=None,**kwargs):
        super(Trip, self).__init__(**kwargs)
        if code:
            self.code = code
        else:
            self.code = Trip.generate_trip_code()
        db.session.add(self)
        db.session.commit()

        for s_id in students:
            TripStudent(trip_id=self.id, student_id=s_id)

    def sync(self):
        db.session.merge(self)
        db.session.commit()
    
    def delete(self):
        for student in TripStudent.get_students_in_trip(self.id):
            TripStudent.remove_student_from_trip(self.id, student['id'])
        db.session.delete(self)
        db.session.commit()
    
    def update_code(self, code):
        self.code = code
        self.sync()
    
    def update_name(self, name):
        self.name = name
        self.sync()
    
    def update_organizer(self, organizer):
        self.organizer = organizer
        self.sync()
    
    def update_num_groups(self, num_groups):
        self.num_groups = num_groups
        self.sync()
    
    def update_group_size(self, group_size):
        self.group_size = group_size
        self.sync()

    def update_details(self, details):
        self.details = details
        self.sync()
        
    def update(self, data):
        if "code" in data:
            self.update_code(data['code'])
        if "name" in data:
            self.update_name(data['name'])
        if "organizer" in data:
            self.update_organizer(data['organizer'])
        if "num_groups" in data:
            self.update_num_groups(data['num_groups'])
        if "group_size" in data:
            self.update_group_size(data['group_size'])
        if "details" in data:
            self.update_details(data['details'])
        if "students" in data:
            self.update_students(data['students'])
    
    def update_students(self, students):
        current_students = TripStudent.get_students_in_trip(self.id)
        current_students = [c['id'] for c in current_students]
        for student_id in students:
            if student_id not in current_students:
                TripStudent.add_student_to_trip(self.id, student_id)
        for s_id in current_students:
            if s_id not in students:
                TripStudent.remove_student_from_trip(self.id, s_id)

    def get_groups(self):
        no_group = TripStudent.get_students_in_group(self.id, 0)
        groups = [[] for _ in range(self.num_groups)]
        for group in range(1, self.num_groups + 1):
            groups[group - 1] = TripStudent.get_students_in_group(self.id, group)
        return { "groupless": no_group, "groups": groups }

    # THIS IS TEMPORARY - THE ACTUAL GROUP GENERATING ALGORITHM WILL NEED TO BE IMPLEMENTED HERE
    def generate_groups(self):
        trip = dict_converter(self)
        students = TripStudent.get_students_in_trip(self.id)
        for s in students:
            s['preferences'] = StudentPreference.get_preferences(self.id, s['id'], return_prefs_only=True)
        for group_id in range(1, trip['num_groups'] + 1):
            if not students:
                break
            gender = students[0]['gender']
            group = []
            for _ in range(trip['group_size']):
                for i, student in enumerate(students):
                    if student['gender'] == gender:
                        group.append(students.pop(i)['id'])
                        break
            TripStudent.add_students_to_group(self.id, group_id, group)
    
    @staticmethod
    def get_trip_by_id(id, return_dict=False):
        trip = db.session.query(Trip).filter_by(id=id).first()
        if return_dict:
            return dict_converter(trip)
        else:
            return trip
    
    @staticmethod
    def get_trip_by_code(code, return_dict=False):
        trip = db.session.query(Trip).filter_by(code=code).first()
        if trip is None:
            return None
        elif return_dict:
            return dict_converter(trip) 
        else:
            return trip

    @staticmethod
    def generate_trip_code():
        id_length = 6
        letters = "ABCDEFGHJKLMNPQRSTUVWXYZ" # "I" and "O" Removed (gets confusing with 0 and 1 numbers)
        nums = "0123456789"
        id = ""
        while True:
            id = ''.join(random.sample((letters + nums), id_length))
            if(id not in Trip.trip_ids):
                break
        return id
    
    @staticmethod
    def get_all_trips(return_dict=False):
        trips = db.session.query(Trip).all()
        if return_dict:
            return [dict_converter(t) for t in trips] 
        else:
            return trips

# Student Preference Databse Model - Stores and handles student trip preferences
class StudentPreference(db.Model):
    __tablename__ = "student_preferences"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    trip_id = db.Column(db.Integer, nullable=False)
    a = db.Column(db.Integer, nullable=True)
    b = db.Column(db.Integer, nullable=True)
    c = db.Column(db.Integer, nullable=True)
    d = db.Column(db.Integer, nullable=True)
    e = db.Column(db.Integer, nullable=True)

    def __init__(self, preferences=None,**kwargs):
        super(StudentPreference, self).__init__(**kwargs)
        db.session.add(self)
        db.session.commit()
        if preferences:
            self.update(preferences)

    def sync(self):
        db.session.merge(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def update(self, preferences):
        self.a, self.b, self.c, self.d, self.e = preferences[:5]
        self.sync()

    @staticmethod
    def check_student_preferences(trip_id, student_id):
        return StudentPreference.get_preferences(trip_id, student_id) is not None

    @staticmethod
    def get_preferences(trip_id, student_id, return_prefs_only=False, return_dict=False):
        sp = db.session.query(StudentPreference).filter_by(student_id=student_id, trip_id=trip_id).first()
        if sp is not None:
            if return_prefs_only:
                return [sp.a, sp.b, sp.c, sp.d, sp.e]
            elif return_dict:
                return dict_converter(sp)
            else:
                return sp
        return None

    @staticmethod
    def get_all_preferences():
        preferences = db.session.query(StudentPreference).all()
        return [dict_converter(p) for p in preferences]

# Student Preference Databse Model - Stores and handles student trip info and groups
class TripStudent(db.Model):
    __tablename__ = "trip_students"

    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, nullable=False)
    student_id = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.Integer, nullable=False, default=0)

    def __init__(self, **kwargs):
        super(TripStudent, self).__init__(**kwargs)
        db.session.add(self)
        db.session.commit()

    def sync(self):
        db.session.merge(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    @staticmethod
    def get_trips_by_student(student_id, return_dict=False):
        trip_ids = db.session.query(TripStudent.trip_id).filter_by(student_id=student_id).all()
        trip_ids = [id[0] for id in trip_ids]
        return [Trip.get_trip_by_id(id, return_dict) for id in trip_ids]
    
    @staticmethod
    def get_students_in_trip(trip_id):
        ids = db.session.query(TripStudent.student_id).filter_by(trip_id=trip_id).all()
        ids = [id[0] for id in ids]
        students = sorted([Student.get_student_by_id(id) for id in ids], key=lambda x: (x['grade'], x['name']))
        return students
    
    @staticmethod
    def remove_all_students_from_trip(trip_id):
        trip_students = db.session.query(TripStudent).filter_by(trip_id=trip_id).all()
        for t in trip_students:
            t.delete()
    
    @staticmethod
    def remove_student_from_trip(trip_id, student_id):
        trip_student = db.session.query(TripStudent).filter_by(trip_id=trip_id, student_id=student_id).first()
        trip_student.delete()
    
    @staticmethod
    def add_students_to_trip(trip_id, students):
        for s in students:
            TripStudent.add_student_to_trip(trip_id, s)

    @staticmethod
    def add_student_to_trip(trip_id, student_id):
        TripStudent(trip_id=trip_id, student_id=student_id)
    
    @staticmethod
    def add_students_to_group(trip_id, group_id, students):
        for s_id in students:
            t_student = db.session.query(TripStudent).filter_by(trip_id=trip_id, student_id=s_id).first()
            t_student.group_id = group_id
            t_student.sync()
    
    @staticmethod
    def get_students_in_group(trip_id, group_id):
        ids = db.session.query(TripStudent.student_id).filter_by(trip_id=trip_id, group_id=group_id).all()
        ids = [id[0] for id in ids]
        return sorted([Student.get_student_by_id(id) for id in ids], key=lambda x: (x['grade'], x['name']))
    
# Group Class - Unused (idk why this is here), to be used in the future I guess
class Group:
    members = []
    preferences = []

    def __init__(self):
        self.members = []

    def __str__(self):
        return str(self.members)

    def get_size(self):
        return len(self.members)

    def add(self, member):
        self.members.append(member)

    def remove(self, member):
        self.members.remove(member)

    def add_best(self, students, preferences):
        student = self.get_best(students, preferences)
        self.members.append(student)
        return student

    def get_value(self, preferences):
        total = 0
        for member1 in self.members:
            for member2 in self.members:
                if member1 == member2: continue
                if member2 in preferences[member1]:
                    total += 1
                    break
        return total

    def get_best(self, students, preferences):
        highest = -1
        highest_student = -1
        for student in students:
            self.members.append(student)
            value = self.get_value(preferences)
            self.members.remove(student)
            if value > highest:
                highest = value
                highest_student = student
        
        return highest_student