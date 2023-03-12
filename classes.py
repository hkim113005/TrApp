import sqlite3
import csv
import random
import string

def setup(f):
    def wrap(*args, **kwargs):
        args[0].conn = sqlite3.connect(Database.DEFAULT_DB)
        r = f(*args, **kwargs)
        args[0].conn.close()
        return r
    return wrap

class Database:
    STUDENT_CSV = "data/students.csv"
    DEFAULT_DB = "data/TrApp.db"

    def __init__(self, fn=None):
        self.csv = fn if fn is not None else Database.STUDENT_CSV
        self.conn = sqlite3.connect(Database.DEFAULT_DB, check_same_thread=False)
        self.cursor = self.conn.cursor()
        tables = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        tables = [x[0] for x in tables]
        if "students" not in tables:
            self.cursor.execute("CREATE TABLE students (id INTEGER, name TEXT, email TEXT, grade INTEGER, gender TEXT, PRIMARY KEY(id))")
            file = open(self.csv, "r")
            data = list(csv.DictReader(file, delimiter=","))
            file.close()
            students = [Student(None, s['name'], s['email'], int(s['grade']), s['gender'], "") for s in data]
            for s in students:
                self.cursor.execute("INSERT INTO students (id, name, email, grade, gender) VALUES(?, ?, ?, ?, ?)", (int(s.get_id()), str(s.get_name()), str(s.get_email()), int(s.get_grade()), str(s.get_gender())))
        if "trips" not in tables:
            self.cursor.execute("CREATE TABLE trips (id TEXT, name TEXT, type TEXT, num_groups INTEGER, students_per_group INTEGER, preferences TEXT, PRIMARY KEY(id))")
        if "trip_students" not in tables:
            self.cursor.execute("CREATE TABLE trip_students (trip_id TEXT, student_id INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")
        if "trip_preferences" not in tables:
            self.cursor.execute("CREATE TABLE trip_preferences (trip_id TEXT, student_id INTEGER, a INTEGER, b INTEGER, c INTEGER, d INTEGER, e INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")
        self.conn.commit()
    
    @setup
    def get_student_by_id(self, student_id):
        student = self.cursor.execute(f'SELECT * FROM students WHERE id = {student_id}').fetchall()
        if student != []:
            s = student[0]
            return s
    
    @setup
    def get_trip_by_id(self, trip_id):
        trip = self.cursor.execute(f"SELECT * FROM trips WHERE id = '{trip_id}'").fetchall()
        if trip != []:
            t = trip[0]
            return t
        
    @setup
    def get_all_students(self, excluded = []):
        all = self.cursor.execute('select * from students').fetchall()
        all = sorted(list(set(all).difference(set(excluded))), key=lambda x: (x[3], x[1]) )
        return all

    @setup
    def get_all_trips(self):
        return sorted(self.cursor.execute('SELECT * FROM trips').fetchall(), key=lambda x: x[1])
    
    @setup
    def get_all_tripstudents(self):
        return self.cursor.execute('SELECT * FROM trip_students').fetchall()
    
    @setup 
    def get_students_in_trip(self, trip_id):
        ids = self.cursor.execute(f"SELECT student_id FROM trip_students WHERE trip_id = '{trip_id}'").fetchall()
        ids = [x[0] for x in ids]
        if ids != []:
            students = sorted([self.get_student_by_id(id) for id in ids], key=lambda x: (x[3], x[1]))
            if students != []:
                return students
    
    @setup 
    def remove_students_in_trip(self, trip_id):
        self.cursor.execute(f"DELETE FROM trip_students WHERE trip_id = '{trip_id}'")
    
    @setup 
    def get_students_by_attribute(self, grade, gender):
        students = self.cursor.execute(f"SELECT * FROM students WHERE grade = {grade} AND gender = '{gender.upper()}'").fetchall()
        if students != []:
            return students
        
    @setup
    def add_student_to_trip(self, student_id, trip_id):
        self.cursor.execute('INSERT INTO trip_students(trip_id, student_id) VALUES(?, ?)', (trip_id, student_id))

    @setup
    def add_trip(self, trip):
        self.cursor.execute('INSERT INTO trips(id, name, type, num_groups, students_per_group, preferences) VALUES(?, ?, ?, ?, ?, ?)', (trip.get_id(), trip.get_name(), trip.get_type(), trip.get_num_groups(), trip.get_students_per_group(), trip.get_preferences()))
        for s in trip.get_students():
            self.add_student_to_trip(s, trip.get_id())

    @setup
    def remove_trip(self, trip_id):
        self.cursor.execute(f"DELETE FROM trips WHERE id = '{trip_id}'")
        self.remove_students_in_trip(trip_id)

    @setup
    def update_trip(self, trip):
        if self.get_trip_by_id(trip.get_id()) != None:
            self.cursor.execute(f"UPDATE trips SET (id, name, type, num_groups, students_per_group, preferences) = (?, ?, ?, ?, ?, ?) WHERE id = '{trip.get_id()}'", (trip.get_id(), trip.get_name(), trip.get_type(), trip.get_num_groups(), trip.get_students_per_group(), trip.get_preferences()))
            self.remove_students_in_trip(trip.get_id())
            for s in trip.get_students():
                self.add_student_to_trip(s, trip.get_id())
        else:
            self.add_trip(trip)

    @setup
    def add_preferences(self, trip_id, student_id, preferences):
        for i in range(5 - len(preferences)):
            preferences.append(None)
        self.cursor.execute("INSERT INTO trip_preferences(trip_id, student_id, a, b, c, d, e) VALUES(?, ?, ?, ?, ?, ?, ?)", (trip_id, student_id, preferences[0], preferences[1], preferences[2], preferences[3], preferences[4]))

    @setup
    def update_students_in_trip(self, trip_id, students):
        self.remove_students_in_trip(trip_id)
        for new in students:
            self.add_student_to_trip(new, trip_id)


class Student:
    student_count = 0
    def __init__(self, id, name, email, grade, gender, preferences=""):
        # Have either num_groups or max_per_group and calculate the other variable based on the one that wasn't entered
        self.name = str(name)
        self.id = id if id != None else (Student.student_count + 1)
        self.email = str(email)
        self.gender = str(gender)
        self.grade = int(grade)
        self.preferences = str(preferences)
        Student.student_count += 1

    def set_name(self, name):
        self.name = name

    def set_email(self, email):
        self.email = email
    
    def set_gender(self, gender):
        self.gender = gender

    def set_grade(self, grade):
        self.grade = grade

    def set_preferences(self, preferences):
        self.preferences = preferences

    def get_name(self):
        return self.name
    
    def get_email(self):
        return self.email
    
    def get_id(self):
        return self.id
    
    def get_gender(self):
        return self.gender
    
    def get_grade(self):
        return self.grade
    
    def get_preferences(self):
        return self.preferences

    def __str__(self):
        s = "[STUDENT INFO - " + str(self.id) + "]"
        s += "\nName: " + self.name
        s += "\nEmail: " + self.email
        s += "\nGender: " + self.gender
        s += "\nGrade: " + str(self.grade)
        s += "\nPreferences: " + self.preferences
        return s


class Trip:
    trip_ids = []
    trips = []
    def __init__(self, id, name, organizer, num_groups, students_per_group, preferences, students):
        # Have either num_groups or max_per_group and calculate the other variable based on the one that wasn't entered
        self.name = name
        self.id = id if id != None else Trip.generate_id()
        self.organizer = organizer
        self.students = students
        self.num_groups = num_groups
        self.students_per_group = students_per_group
        self.preferences = preferences
        Trip.trips.append(self)
        Trip.trip_ids.append(self.id)

    def set_name(self, name):
        self.name = name

    def set_type(self, type):
        self.organizer = type
    
    def add_student(self, student):
        self.students.append(student)

    def set_num_groups(self, groups):
        self.num_groups = groups

    def set_students_per_group(self, max):
        self.students_per_group = max

    def set_preferences(self, preferences):
        self.preferences = preferences

    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id
    
    def get_type(self):
        return self.organizer
    
    def get_students(self):
        return self.students
    
    def get_num_groups(self):
        return self.num_groups
    
    def get_students_per_group(self):
        return self.students_per_group
    
    def get_preferences(self):
        return self.preferences
    
    @staticmethod
    def get_trips():
        return Trip.trips

    @staticmethod
    def generate_id():
        id = ""
        while True:
            id = ''.join(random.sample((string.ascii_uppercase+string.digits),6))
            if(id not in Trip.trip_ids):
                break
        return id

    def __str__(self):
        s = "[TRIP INFO - " + self.name + "]"
        s += "\nTrip ID = " + str(self.id)
        s += "\nTrip Type: " + self.organizer
        s += "\nTotal Students: " + str(len(self.students))
        s += "\nStudent Ids: " + str(self.students)
        s += "\nNumber of groups: " + str(self.num_groups)
        s += "\nStudents Per group: " + str(self.students_per_group)
        s += "\nPreferences: " + self.preferences
        return s