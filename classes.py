import uuid
import sqlite3
import csv

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
            students = [Student(0, s['name'], s['email'], int(s['grade']), s['sex'], "") for s in data]
            for s in students:
                self.cursor.execute("INSERT INTO students (id, name, email, grade, gender) VALUES(?, ?, ?, ?, ?)", (int(s.get_id()), str(s.get_name()), str(s.get_email()), int(s.get_grade()), str(s.get_gender())))
        if "trips" not in tables:
            self.cursor.execute("CREATE TABLE trips (id TEXT, name TEXT, type TEXT, num_rooms INTEGER, students_per_room INTEGER, preferences TEXT, PRIMARY KEY(id))")
        if "trip_students" not in tables:
            self.cursor.execute("CREATE TABLE trip_students (trip_id TEXT, student_id INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")
        self.conn.commit()
    
    @setup
    def getStudentById(self, student_id):
        student = self.cursor.execute(f'select * from students WHERE id = {student_id}').fetchall()
        if student != []:
            s = student[0]
            return s
    
    @setup
    def getTripById(self, trip_id):
        trip = self.cursor.execute(f'select * from trips WHERE id = {trip_id}').fetchall()
        if trip != []:
            t = trip[0]
            return t
        
    @setup
    def getAllStudents(self):
        return self.cursor.execute('select * from students').fetchall()

    @setup
    def getAllTrips(self):
        return self.cursor.execute('select * from trips').fetchall()
    
    @setup 
    def getAllStudentsInTrip(self, trip_id):
        students = self.cursor.execute(f'select * from trip_students WHERE trip_id = {trip_id}').fetchall()
        if students != []:
            return students
    
    @setup 
    def getStudentsByAttribute(self, grade, gender):
        students = self.cursor.execute(f"select * from students WHERE grade = {grade} AND gender = '{gender.upper()}'").fetchall()
        if students != []:
            return students
        
    @setup
    def addStudentToTrip(self, student_id, trip_id):
        self.cursor.execute('INSERT into trip_students(trip_id. student_id) VALUES(?, ?)', (trip_id, student_id))

    #TODO
    @setup
    def addTrip(self, trip):
        self.cursor.execute('INSERT into trips(id, name, type, num_rooms, students_per_room, preferences) VALUES(?, ?, ?, ?, ?, ?)', (trip.get_id(), trip.get_name(), trip.get_type(), trip.get_num_rooms(), trip.get_students_per_room(), trip.get_preferences()))
        return trip

class Student:
    student_count = 0
    def __init__(self, id, name, email, grade, gender, preferences=""):
        # Have either num_rooms or max_per_room and calculate the other variable based on the one that wasn't entered
        self.name = str(name)
        self.id = id if id != 0 else (Student.student_count + 1)
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
    trips = []
    def __init__(self, name, trip_type, num_rooms, students_per_room, preferences, students):
        # Have either num_rooms or max_per_room and calculate the other variable based on the one that wasn't entered
        self.name = name
        self.id = uuid.uuid4()
        self.trip_type = trip_type
        self.students = students
        self.num_rooms = num_rooms
        self.students_per_room = students_per_room
        self.preferences = preferences
        Trip.trips.append(self)

    def set_name(self, name):
        self.name = name

    def set_type(self, type):
        self.trip_type = type
    
    def add_student(self, student):
        self.students.append(student)

    def set_num_rooms(self, rooms):
        self.num_rooms = rooms

    def set_students_per_room(self, max):
        self.students_per_room = max

    def set_preferences(self, preferences):
        self.preferences = preferences

    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id
    
    def get_type(self):
        return self.trip_type
    
    def get_students(self):
        return self.students
    
    def get_num_rooms(self):
        return self.num_rooms
    
    def get_students_per_room(self):
        return self.students_per_room
    
    def get_preferences(self):
        return self.preferences
    
    @staticmethod
    def get_trips():
        return Trip.trips

    def __str__(self):
        s = "[TRIP INFO - " + self.name + "]"
        s += "\nTrip ID = " + str(self.id)
        s += "\nTrip Type: " + self.trip_type
        s += "\nTotal Students: " + str(len(self.students))
        s += "\nStudent Ids: " + str(self.students)
        s += "\nNumber of Rooms: " + str(self.num_rooms)
        s += "\nStudents Per Room: " + str(self.students_per_room)
        s += "\nPreferences: " + self.preferences
        return s