import random
import csv
import os
from datetime import datetime, timedelta
from flask import render_template, session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Message
from app import db, mail, app, current_user

# Admin Login Credentials
ADMIN = {
    "email": "tsu@acs.sch.ae",
    "password": "admin"
}

# Teacher Login Credentials
TEACHER = {
    "email": "//--@acs.sch.ae",
    "password": "ACSTeachers2023",
    "photoUrl": "https://web.archive.org/web/20201030114656if_/https://www.acs.sch.ae/uploaded/Home_Page/ACS_Star.png?1576060292569"
}

# Converts SQL databse row into a standard python dictionary
def dict_converter(row):
    return {column.name: getattr(row, row.__mapper__.get_property_by_column(column).key) for column in row.__table__.columns}

#  User Database Model - Handles user signup, verification, and login
class User (db.Model):
    __tablename__ = 'users'
    verify_minutes = 3

    # Database User Columns
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_teacher = db.Column(db.Boolean, nullable=False, default=False)
    is_student = db.Column(db.Boolean, nullable=False, default=False)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    is_resetting = db.Column(db.Boolean, nullable=False, default=False)

    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    hashed_password = db.Column(db.String, nullable=False)
    verify_code = db.Column(db.String(6), nullable=True)
    
    student_id = db.Column(db.Integer, nullable=True)
    teacher_id = db.Column(db.Integer, nullable=True)
    verify_attempts = db.Column(db.Integer, nullable=False, default=0)

    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now().replace(microsecond=0))
    date_verified = db.Column(db.DateTime, nullable=True)
    date_last_verify = db.Column(db.DateTime, nullable=True, default=datetime.now().replace(microsecond=0))
    
    def __init__(self, password, is_verified=False, **kwargs):
        super(User, self).__init__(**kwargs)
        self.hashed_password = generate_password_hash(password, method="scrypt")
        if is_verified:
            self.verify(initial=True)
        self.regenerate_verify_code()
        self.create()

    def create(self):
        db.session.add(self)
        db.session.commit()
    
    def sync(self):
        db.session.commit()
    
    def delete(self):
        for file in FileUpload.get_uploads_by_user(self.id):
            file.delete()
        db.session.delete(self)
        db.session.commit()
    
    def update_name(self, name):
        self.name = name
        self.sync()
    
    def update_email(self, email):
        self.email = email
        self.sync()
    
    def update_student_id(self, student_id):
        self.student_id = student_id
        self.sync()
    
    def update_teacher_id(self, teacher_id):
        self.teacher_id = teacher_id
        self.sync()

    def update_password(self, password):
        self.hashed_password = generate_password_hash(password, method="scrypt")
        self.is_resetting = False
        self.sync()

    def update_perms(self, data):
        if 'is_verified' in data:
            self.is_verified = data['is_verified']
        if "is_admin" in data:
            self.is_admin = data['is_admin']
        if "is_teacher" in data:
            self.is_teacher = data['is_teacher']
        if "is_student" in data:
            self.is_student = data['is_student']
        self.sync()

    def update(self, data):
        if 'name' in data:
            self.update_name(data['name'])
        if 'email' in data:
            self.update_email(data['email'])
        if 'student_id' in data:
            self.update_student_id(data['student_id'])
        if 'teacher_id' in data:
            self.update_teacher_id(data['teacher_id'])
        if 'password' in data:
            self.update_password(data['password'])
        self.update_perms(data)

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
    
    def verify(self, initial=False):
        self.is_verified = True
        if initial:
            self.date_verified = datetime.now().replace(microsecond=0)
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
    
    def send_signup_email(self):
        name = self.name.split(" ")[0]
        html = render_template("email/signup.html", name=name, code=self.verify_code)
        self.send_email("TrApp | Signup & Email Verification", html)

    def send_verify_email(self):
        html = render_template("email/verification.html", code=self.verify_code)
        self.send_email("TrApp | Email Verification", html)
    
    def send_preferences_email(self, trip_id, updated=False):
        name = self.name.split(" ")[0]
        trip = Trip.get_trip_by_id(trip_id)
        preferences = StudentPreference.get_preferences(trip_id, self.student_id, return_prefs_only=True)
        preferences = list(filter(lambda x: x is not None, preferences))
        preferences = [Student.get_student_by_id(id) for id in preferences]

        file_name = "preferences-2" if updated else "preferences-1"
        email_subject = f"Preferences {'Updated ' if updated else ''}for {trip.name}" 
        html = render_template(f"email/{file_name}.html", name=name, trip=trip, preferences=preferences)
        self.send_email(f"TrApp | {email_subject}", html)

    def login(self):
        session.permanent = True
        session['user_id'] = self.id
        current_user['db_user'] = self
        if current_user['db_user'].is_student:
            current_user['student'] = Student.get_student_by_id(self.student_id)
        if current_user['db_user'].is_teacher:
            current_user['teacher'] = Teacher.get_teacher_by_id(self.teacher_id)
        self.sync()
        print(f"Succesfully Logged in as {self.name}")
    
    def check_password(self, plain_password):
        return check_password_hash(self.hashed_password, plain_password)

    def initiate_pass_reset(self):
        self.regenerate_verify_code()
        self.is_verified = False
        self.is_resetting = True
        self.sync()
        self.send_verify_email()

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
                if u['date_verified'] is not None:
                    u['date_verified'] = str(u['date_verified'])
        return users
    
    @staticmethod
    def get_user_by_email(email):
        return db.session.query(User).filter_by(email=email).first()

    @staticmethod
    def get_user_by_id(id):
        return db.session.query(User).filter_by(id=id).first()

    @staticmethod
    def get_user_by_student_id(student_id):
        return db.session.query(User).filter_by(student_id=student_id).first()

    @staticmethod
    def get_user_by_teacher_id(teacher_id):
        return db.session.query(User).filter_by(teacher_id=teacher_id).first()

    @staticmethod
    def check_exist_with_email(email):
        return User.get_user_by_email(email) is not None

    @staticmethod
    def check_exist_with_id(id):
        return User.get_user_by_id(id) is not None

    @staticmethod
    def check_exist_with_student_email(email):
        s = Student.get_student_by_email(email)
        return User.get_user_by_student_id(s['id']) is not None

# Student Databse Model - Stores and handles student info 
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    grade = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(1), nullable=True, default="-")

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
    def get_student_by_id(student_id, return_dict=True):
        student = db.session.query(Student).filter_by(id=student_id).first()
        if not return_dict or student is None:
            return student
        else:
            return dict_converter(student)

    @staticmethod
    def get_student_by_email(email, return_dict=True):
        student = db.session.query(Student).filter_by(email=email).first()
        if not return_dict or student is None:
            return student
        else:
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
    
    @staticmethod
    def check_new_student(student):
        no_name = student['name'] == '' or student['name'] is None
        no_email = student['email'] == '' or student['email'] is None
        if not no_email:
            s = Student.get_student_by_email(student['email'])
        return no_name or no_email or s is None

    @staticmethod
    def delete_students_with_ids(student_ids, delete_users=False):
        for id in student_ids:
            Student.get_student_by_id(id, return_dict=False).delete()
            if delete_users:
                User.get_user_by_student_id(id).delete()

# Teacher Databse Model - Stores and handles teacher info 
class Teacher(db.Model):
    __tablename__ = 'teachers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=True)
    title = db.Column(db.String, nullable=True, default="Unknown")
    photoUrl = db.Column(db.String, nullable=False, default="/static/img/logo.png")

    def __init__(self, **kwargs):
        super(Teacher, self).__init__(**kwargs)
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
    
    def update_title(self, title):
        self.title = title
        self.sync()
    
    def update(self, data):
        if 'name' in data:
            self.update_name(data['name'])
        if 'email' in data:
            self.update_email(data['email'])
        if 'title' in data:
            self.update_title(data['title'])

    @staticmethod
    def get_teacher_by_id(teacher_id, return_dict=True):
        teacher = db.session.query(Teacher).filter_by(id=teacher_id).first()
        if not return_dict or teacher is None:
            return teacher
        else:
            return dict_converter(teacher)

    @staticmethod
    def get_teacher_by_email(email):
        teacher = db.session.query(Teacher).filter_by(email=email).first()
        return dict_converter(teacher) if teacher else None

    @staticmethod
    def check_teacher_email(email):
        teacher = Teacher.get_teacher_by_email(email)
        return teacher is not None
    
    def check_main(email):
        return email == TEACHER['email']

    @staticmethod
    def get_all_teachers(return_dict=False):
        teachers = db.session.query(Teacher).all()
        if return_dict:
            return [dict_converter(t) for t in teachers] 
        else:
            return teachers

# Trip Databse Model - Stores and handles trip info 
class Trip(db.Model):
    __tablename__ = 'trips'
    trip_ids = []

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, nullable=False, default=0)
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
            sp = StudentPreference.get_preferences(self.id, student['id'])
            if sp:
                sp.delete()
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
    
    @staticmethod
    def get_trips_by_teacher_id(teacher_id, return_dict=False):
        trips = db.session.query(Trip).filter_by(teacher_id=teacher_id).all()
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
    def check_different_preferences(trip_id, student_id, preferences):
        return StudentPreference.get_preferences(trip_id, student_id, return_prefs_only=True) != preferences

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
        students = [Student.get_student_by_id(id) for id in ids]
        students = sorted(students, key=lambda x: (x['grade'], x['name']))
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
    
# File Upload Database model - Stores and handles file upload info
class FileUpload(db.Model):
    __tablename__ = "file_uploads"

    STUDENT_COLUMN_INFO = None
    TEACHER_COLUMN_INFO = None

    ALLOWED_FORMATS = {
        "csv": "csv",
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    full_path = db.Column(db.String, nullable=False, default=app.config['UPLOAD_FOLDER'])
    dir = db.Column(db.String, nullable=False, default="")
    filename = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False, default="unknown")
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.now().replace(microsecond=0))

    def __init__(self, filename, **kwargs):
        super(FileUpload, self).__init__(**kwargs)
        self.dir = f"user-{kwargs.get('user_id')}"
        self.full_path = f"{app.config['UPLOAD_FOLDER']}/{self.dir}"
        if not os.path.exists(self.full_path):
            os.makedirs(self.full_path)
        self.filename = FileUpload.fix_filename(self.full_path, filename)
        ext = filename.split(".")[-1]
        if ext in list(FileUpload.ALLOWED_FORMATS.keys()):
            self.type = FileUpload.ALLOWED_FORMATS[ext]

    def delete(self):
        os.remove(os.path.join(self.full_path, self.filename))
        db.session.delete(self)
        db.session.commit()

    def save_file(self, file):
        file.seek(0)
        file.save(os.path.join(self.full_path, self.filename))
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_student_csv_columns(file, adding=False):
        f = file.stream.read().decode("utf-8").splitlines()
        data = list(csv.DictReader(f))
        columns = list(dict(data[0]).keys())
        if not adding:
            return 'email' in columns
        return columns == FileUpload.STUDENT_COLUMN_INFO['columns']
    
    @staticmethod
    def check_valid_student(row):
        for key, val in row.items():
            data = FileUpload.STUDENT_COLUMN_INFO[key]
            is_null = val == '' or val is None
            if is_null and is_null != data['nullable']:
                return False         
            if key != "gender" and 'max_length' in data:
                if len(val) != data['max_length']:
                    return False
            if key == "grade":
                if int(val) < 1 or int(val) > 12:
                    return False
            if key == "gender" and val not in ['M', 'F', '-', '']:
                return False
        return True
    
    @staticmethod
    def check_teacher_csv_columns(file):
        f = file.stream.read().decode("utf-8").splitlines()
        data = list(csv.DictReader(f))
        return list(dict(data[0]).keys()) == FileUpload.TEACHER_COLUMN_INFO['columns']

    @staticmethod
    def get_uploads_by_user(user_id, return_dict=False):
        uploads = db.session.query(FileUpload).filter_by(user_id=user_id).all()
        if return_dict:
            return [dict_converter(u) for u in uploads] 
        else:
            return uploads
    
    @staticmethod
    def get_students_results(file_upload, adding=False):
        students = {
            "added": [],
            "removed": {
                "used": [],
                "unused": []
            },
            "invalid": []
        }
        f_path = os.path.join(file_upload.full_path, file_upload.filename)
        f = open(f_path, "r")
        data = list(csv.DictReader(f))
        emails = [s['email'] for s in data]
        if adding:
            for st in Student.get_all_students(return_dict=True):
                if st['email'] not in emails:
                    if User.check_exist_with_student_email(st['email']):
                        students['removed']['used'].append(st)
                    else:
                        students['removed']['unused'].append(st)
        for s in data:
            if len(s['gender']) == 0:
                s['gender'] = "-"
            if not FileUpload.check_valid_student(s):
                students['invalid'].append(s)
            elif adding and Student.check_new_student(s):
                students['added'].append(s)
            elif Student.check_student_email(s['email']):
                student = Student.get_student_by_email(s['email'])
                if User.check_exist_with_student_email(student['email']):
                    students['removed']['used'].append(student)
                else:
                    students['removed']['unused'].append(student)
        return students
    
    @staticmethod
    def get_upload_by_id(file_id, return_dict=False):
        upload = db.session.query(FileUpload).filter_by(id=file_id).first()
        if return_dict:
            dict_converter(upload)
        else:
            return upload
    
    @staticmethod
    def fix_filename(path, filename):
        fn = secure_filename(filename)
        filename_list = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        if not fn:
            fn = "file"
        if fn in filename_list:
            i = 1
            new_path = os.path.join(path, filename)
            while os.path.exists(new_path):
                name, ext = os.path.splitext(filename)
                fn = f"{name}_{i}{ext}"
                new_path = os.path.join(path, fn)
                i += 1
        return fn

    @staticmethod
    def get_full_path(path):
        return os.path.join(app.config['UPLOAD_FOLDER'], path)

# TrApp Setup - Initializes databases and adds test trips
class Setup:
    STUDENT_CSV = "data/students.csv"
    TEACHER_CSV = "data/teachers.csv"
    TABLE_NAMES = [User.__tablename__, Student.__tablename__, Teacher.__tablename__, Trip.__tablename__, StudentPreference.__tablename__, TripStudent.__tablename__]
    
    initialized = False

    @staticmethod
    def init_database():
        print("|-------------[TrApp Setup Start]-------------|")
        tables_exist = students_exist = admin_exists = teacher_exists = trips_exist = True
        with app.app_context():
            while True:
                tables = db.inspect(db.engine).get_table_names()
                tables_exist = len(set(Setup.TABLE_NAMES) - set(tables)) == 0
                
                if not tables_exist:
                    db.create_all()
                    print("|-> Created All Databse Tables")
                else:
                    students_exist = len(Student.get_all_students()) > 0
                    teachers_exist = len(Teacher.get_all_teachers()) > 0
                    admin_exists = User.check_exist_with_email(ADMIN['email'])
                    teacher_exists = User.check_exist_with_email(TEACHER['email'])
                    trips_exist = len(db.session.query(Trip).all()) == 8
                    s_column_info_exists = FileUpload.STUDENT_COLUMN_INFO is not None
                    t_column_info_exists = FileUpload.TEACHER_COLUMN_INFO is not None
                    if not students_exist:
                        Setup.add_students()
                    elif not teachers_exist:
                        Setup.add_teachers()
                    else:
                        if not trips_exist:
                            Setup.create_test_trips()
                        if not admin_exists:
                            User(is_admin=True, is_teacher=True, is_student=True, name="TSU Admin", is_verified=True, student_id=0, teacher_id=0, email=ADMIN['email'], password=ADMIN['password'])
                            print("|-> Added Admin to Database")
                        if not teacher_exists:
                            User(is_teacher=True, is_verified=True, name="ACS Teacher",teacher_id=1, email=TEACHER['email'], password=TEACHER['password'])
                            print("|-> Added Teacher to Database")
                        if not s_column_info_exists:
                            Setup.add_column_info(Student)
                        if not t_column_info_exists:
                            Setup.add_column_info(Teacher)
                        if trips_exist and admin_exists and teacher_exists and s_column_info_exists and t_column_info_exists:
                            break

        print("|----------------[Setup Check]----------------|")
        print(f"|---> {tables_exist} | Tables Exist")
        print(f"|---> {students_exist} | Students Exist")
        print(f"|---> {teachers_exist} | Teachers Exist")
        print(f"|---> {admin_exists} | Admin User Exists")
        print(f"|---> {teacher_exists} | Teacher User Exists")
        print(f"|---> {trips_exist} | Test Trips Exist")
        print(f"|---> {s_column_info_exists} | Student Column Info Exists")
        print(f"|---> {t_column_info_exists} | Teacher Column Info Exists")
        print("|--------------[TrApp Setup End]--------------|")
    
    @staticmethod
    def add_students():
        file = open(Setup.STUDENT_CSV, "r")
        data = list(csv.DictReader(file))
        file.close()
        Student(id=0, name="Test Student", email="tsu@acs.sch.ae", grade=12, gender="M")
        for s in data:
            Student(name=s['name'], email=s['email'], grade=s['grade'], gender=s['gender'])
        print("|-> Added Students to Database")
    
    @staticmethod
    def add_teachers():
        file = open(Setup.TEACHER_CSV, "r")
        data = list(csv.DictReader(file))
        file.close()
        Teacher(id=0, name="TSU Admin", email="tsu@acs.sch.ae", title="TSU Admin")
        Teacher(id=1, name="ACS Teacher", email=TEACHER['email'], title="ACS Teacher", photoUrl=TEACHER['photoUrl'])
        for t in data:
            Teacher(name=t['name'], email=t['email'], title=t['title'], photoUrl=t['photoUrl'])
        print("|-> Added Teachers to Database")
    
    # Get rid of this for production
    @staticmethod
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
            print("|-> Created Test Trips")
            #print([dict_converter(t) for t in Trip.get_all_trips()])

    @staticmethod
    def add_column_info(t):
        def get_python_type(sqlalchemy_type):
            type_mapping = {
                "INTEGER": int,
                "STRING": str,
                "VARCHAR": str,
                "BOOLEAN": bool,
                "DATETIME": str,
                # (add more later)...
            }
            type_name = str(sqlalchemy_type).split("(")[0].upper()
            return type_mapping.get(type_name)

        # Get the SQLAlchemy table object for the provided model class
        table = t.__table__

        # Get the column names and types as Python types
        columns = table.columns
        column_names = []
        column_types = []
        nullable_flags = []
        max_lengths = []

        for column in columns:
            if column.name != "id": # Ignore ID column
                column_names.append(column.name)
                column_types.append(get_python_type(column.type))
                nullable_flags.append(column.nullable)
                max_lengths.append(column.type.length if isinstance(column.type, db.String) else None)
                
        # Create the database_info dictionary
        database_info = {
            "columns": column_names
        }
        
        for column, column_type, nullable, max_length in zip(column_names, column_types, nullable_flags, max_lengths):
            column_info = {
                "type": column_type,
                "nullable": nullable
            }
            if max_length is not None:
                column_info["max_length"] = max_length
            database_info[column] = column_info
        if t.__tablename__ == Student.__tablename__:
            FileUpload.STUDENT_COLUMN_INFO = database_info
        elif t.__tablename__ == Teacher.__tablename__:
            FileUpload.TEACHER_COLUMN_INFO = database_info

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