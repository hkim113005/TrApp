import sqlite3
import csv
import random

def db_setup(f):
    def wrap(*args, **kwargs):
        args[0].conn = sqlite3.connect(Database.DEFAULT_DB, check_same_thread=False)
        args[0].conn.row_factory = sqlite3.Row
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
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        tables = self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        tables = [x[0] for x in tables]
        if "students" not in tables:
            self.cursor.execute("CREATE TABLE students (id INTEGER, name TEXT, email TEXT, grade INTEGER, gender TEXT, PRIMARY KEY(id))")
            file = open(self.csv, "r")
            data = list(csv.DictReader(file, delimiter=","))
            file.close()
            students = [Student(None, s['name'], s['email'], int(s['grade']), s['gender'], "") for s in data]
            students.append(Student(0, "Test Student", "tsu@acs.sch.ae", 0, "M", "")) # Test Student
            for s in students:
                self.cursor.execute("INSERT INTO students (id, name, email, grade, gender) VALUES(?, ?, ?, ?, ?)", (int(s.get_id()), str(s.get_name()), str(s.get_email()), int(s.get_grade()), str(s.get_gender())))
        if "trips" not in tables:
            self.cursor.execute("CREATE TABLE trips (id TEXT, name TEXT, organizer TEXT, num_groups INTEGER, group_size INTEGER, details TEXT, PRIMARY KEY(id))")
        if "trip_students" not in tables:
            self.cursor.execute("CREATE TABLE trip_students (trip_id TEXT, student_id INTEGER, group_id INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")
        if "trip_preferences" not in tables:
            self.cursor.execute("CREATE TABLE trip_preferences (trip_id TEXT, student_id INTEGER, a INTEGER, b INTEGER, c INTEGER, d INTEGER, e INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")
        self.conn.commit()
    
    def dict_converter(self, row):
        return dict(zip(row.keys(), row))

    @db_setup
    def get_student_by_id(self, student_id):
        student = self.cursor.execute(f'SELECT * FROM students WHERE id = {student_id}').fetchall()
        if student != []:
            s = student[0]
            return self.dict_converter(s)
    
    @db_setup
    def get_student_by_email(self, email):
        student = self.cursor.execute(f"SELECT * FROM students WHERE email = '{email}'").fetchall()
        if student != []:
            s = student[0]
            return self.dict_converter(s)
    
    @db_setup
    def check_student_email(self, email):
        students = self.get_all_students()
        emails = [s['email'] for s in students]
        return email.lower() in emails
    
    @db_setup
    def get_trip_by_id(self, trip_id):
        trip = self.cursor.execute(f"SELECT * FROM trips WHERE id = '{trip_id}'").fetchall()
        if trip != []:
            t = trip[0]
            return self.dict_converter(t)
        
    @db_setup
    def get_all_students(self, excluded = []):
        all = self.cursor.execute('SELECT * from students').fetchall()
        all = sorted(list(set(all).difference(set(excluded))), key=lambda x: (x[3], x[1]) )
        return [self.dict_converter(student) for student in all]

    @db_setup
    def get_all_trips(self):
        return sorted([self.dict_converter(trip) for trip in self.cursor.execute('SELECT * FROM trips').fetchall()], key=lambda x: x['name'])
    
    @db_setup
    def get_trips_by_student(self, student_id):
        trip_ids = self.cursor.execute(f"SELECT trip_id FROM trip_students WHERE student_id = {student_id}").fetchall()
        trip_ids = [id[0] for id in trip_ids]
        trips = [self.get_trip_by_id(id) for id in trip_ids]
        return sorted(trips, key=lambda x: x['name'])
    
    @db_setup 
    def get_students_in_trip(self, trip_id):
        ids = self.cursor.execute(f"SELECT student_id FROM trip_students WHERE trip_id = '{trip_id}'").fetchall()
        ids = [x[0] for x in ids]
        students = sorted([self.get_student_by_id(id) for id in ids], key=lambda x: (x['grade'], x['name']))
        return students
    
    @db_setup 
    def remove_students_in_trip(self, trip_id):
        self.cursor.execute(f"DELETE FROM trip_students WHERE trip_id = '{trip_id}'")
        self.conn.commit()
    
    @db_setup 
    def get_students_by_attribute(self, grade, gender):
        students = self.cursor.execute(f"SELECT * FROM students WHERE grade = {grade} AND gender = '{gender.upper()}'").fetchall()
        if students != []:
            return [self.dict_converter(student) for student in students]
    
    @db_setup 
    def update_student(self, student_id, data):
        if self.get_student_by_id(student_id) != None:
            if 'name' in data:
                self.update_student_name(student_id, data['name'])
            if 'grade' in data:
                self.update_student_grade(student_id, data['grade'])
            if 'gender' in data:
                self.update_student_gender(student_id, data['gender'])

    @db_setup 
    def update_student_name(self, student_id, name):
        if self.get_student_by_id(student_id) != None:
            self.cursor.execute(f"UPDATE students SET name = '{name}' WHERE id = {student_id}")
    
    @db_setup 
    def update_student_grade(self, student_id, grade):
        if self.get_student_by_id(student_id) != None:
            self.cursor.execute(f"UPDATE students SET (grade) = {grade} WHERE id = {student_id}")
    
    @db_setup 
    def update_student_gender(self, student_id, gender):
        if self.get_student_by_id(student_id) != None:
            self.cursor.execute(f"UPDATE students SET (gender) = '{gender}' WHERE id = {student_id}")
        
    @db_setup
    def add_student_to_trip(self, student_id, trip_id):
        self.cursor.execute('INSERT INTO trip_students(trip_id, student_id, group_id) VALUES(?, ?, ?)', (trip_id, student_id, 0))
        self.conn.commit()

    @db_setup
    def get_all_trip_students(self):
        return [self.dict_converter(trip_student) for trip_student in self.cursor.execute('select * from trip_students').fetchall()]

    @db_setup
    def add_trip(self, trip):
        self.cursor.execute('INSERT INTO trips(id, name, organizer, num_groups, group_size, details) VALUES(?, ?, ?, ?, ?, ?)', (trip.get_id(), trip.get_name(), trip.get_organizer(), trip.get_num_groups(), trip.get_group_size(), trip.get_details()))
        self.conn.commit()
        for s in trip.get_students():
            self.add_student_to_trip(s, trip.get_id())

    @db_setup
    def remove_trip(self, trip_id):
        self.cursor.execute(f"DELETE FROM trips WHERE id = '{trip_id}'")
        self.conn.commit()
        self.remove_students_in_trip(trip_id)
        self.remove_trip_preferences(trip_id)

    @db_setup
    def update_trip(self, trip):
        if self.get_trip_by_id(trip.get_id()) != None:
            self.cursor.execute(f"UPDATE trips SET (id, name, organizer, num_groups, group_size, details) = (?, ?, ?, ?, ?, ?) WHERE id = '{trip.get_id()}'", (trip.get_id(), trip.get_name(), trip.get_organizer(), trip.get_num_groups(), trip.get_group_size(), trip.get_details()))
            self.remove_students_in_trip(trip.get_id())
            for s in trip.get_students():
                self.add_student_to_trip(s, trip.get_id())
        else:
            self.add_trip(trip)

    @db_setup
    def get_all_trip_preferences(self):
        return [self.dict_converter(pref) for pref in self.cursor.execute('SELECT * FROM trip_preferences').fetchall()]

    @db_setup
    def get_student_preferences(self, trip_id, student_id, return_prefs_only=False):
        prefs = self.cursor.execute(f"SELECT * FROM trip_preferences WHERE trip_id ='{trip_id}' AND student_id = {student_id}").fetchall()
        prefs = [self.dict_converter(pref) for pref in prefs]
        if return_prefs_only:
            p = prefs[0]
            return [p['a'], p['b'], p['c'], p['d'], p['e']]
        else:
            return prefs

    @db_setup
    def check_student_preferences(self, trip_id, student_id):
        return self.get_student_preferences(trip_id, student_id) != []

    @db_setup 
    def update_trip_preferences(self, trip_id, student_id, preferences):
        self.cursor.execute(f"UPDATE trip_preferences SET (a, b, c, d, e) = (?, ?, ?, ?, ?) WHERE trip_id ='{trip_id}' AND student_id = {student_id}", preferences)

    @db_setup
    def remove_trip_preferences(self, trip_id):
        self.cursor.execute(f"DELETE FROM trip_preferences WHERE trip_id ='{trip_id}'")
    
    @db_setup
    def add_preferences(self, trip_id, student_id, preferences):
        for _ in range(5 - len(preferences)):
            preferences.append(None)
        if self.check_student_preferences(trip_id, student_id):
            self.update_trip_preferences(trip_id, student_id, preferences)
        else:
            self.cursor.execute("INSERT INTO trip_preferences(trip_id, student_id, a, b, c, d, e) VALUES(?, ?, ?, ?, ?, ?, ?)", (trip_id, student_id, preferences[0], preferences[1], preferences[2], preferences[3], preferences[4]))
    
    @db_setup
    def update_students_in_trip(self, trip_id, students):
        self.remove_students_in_trip(trip_id)
        for new in students:
            self.add_student_to_trip(new, trip_id)
    
    @db_setup
    def add_students_to_group(self, trip_id, group_id, students):
        for student in students:
            id = student['id']
            self.cursor.execute(f"UPDATE trip_students SET group_id = {group_id} WHERE trip_id = '{trip_id}' AND student_id = {id}")
    
    @db_setup
    def get_students_in_group(self, trip_id, group_id):
        ids = self.cursor.execute(f"SELECT student_id FROM trip_students WHERE trip_id = '{trip_id}' AND group_id = {group_id}").fetchall()
        ids = [x[0] for x in ids]
        students = sorted([self.get_student_by_id(id) for id in ids], key=lambda x: (x['grade'], x['name']))
        if students != []:
            return students
    
    @db_setup
    def get_groups_in_trip(self, trip_id):
        no_group = self.get_students_in_group(trip_id, 0)
        trip = self.get_trip_by_id(trip_id)

        groups = [[] for _ in range(trip['num_groups'])]
        for group in range(1, trip['num_groups'] + 1):
            groups[group - 1] = self.get_students_in_group(trip_id, group)

        return { "groupless": no_group, "groups": groups }
    
    # THIS IS TEMPORARY - THE ACTUAL GROUP GENERATING ALGORITHM WILL NEED TO BE IMPLEMENTED HERE
    @db_setup
    def generate_groups(self, trip_id):
        trip = self.get_trip_by_id(trip_id)
        students = self.get_students_in_trip(trip_id)
        for s in students:
            s['preferences'] = self.get_student_preferences(trip_id, s['id'], return_prefs_only=True)
        print(students)
        
        for group_number in range(1, trip['num_groups'] + 1):
            if not students:
                break
            gender = students[0]['gender']
            group = []
            for _ in range(trip['group_size']):
                for i, student in enumerate(students):
                    if student['gender'] == gender:
                        group.append(students.pop(i))
                        break
            self.add_students_to_group(trip_id, group_number, group)

class Student:
    student_count = 0
    def __init__(self, id, name, email, grade, gender, details=""):
        # Have either num_groups or max_per_group and calculate the other variable based on the one that wasn't entered
        self.name = str(name)
        self.id = id if id != None else (Student.student_count + 1)
        self.email = str(email)
        self.gender = str(gender)
        self.grade = int(grade)
        self.details = str(details)
        Student.student_count += 1

    def set_name(self, name):
        self.name = name

    def set_email(self, email):
        self.email = email
    
    def set_gender(self, gender):
        self.gender = gender

    def set_grade(self, grade):
        self.grade = grade

    def set_details(self, details):
        self.details = details

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
    
    def get_details(self):
        return self.details

    def __str__(self):
        s = "[STUDENT INFO - " + str(self.id) + "]"
        s += "\nName: " + self.name
        s += "\nEmail: " + self.email
        s += "\nGender: " + self.gender
        s += "\nGrade: " + str(self.grade)
        s += "\nDetails: " + self.details
        return s

class Trip:
    trip_ids = []
    trips = []
    def __init__(self, id, name, organizer, num_groups, group_size, details, students):
        # Have either num_groups or max_per_group and calculate the other variable based on the one that wasn't entered
        self.name = name
        self.id = id if id != None else Trip.generate_id()
        self.organizer = organizer
        self.students = students
        self.num_groups = num_groups
        self.group_size = group_size
        self.details = details
        Trip.trips.append(self)
        Trip.trip_ids.append(self.id)

    def set_name(self, name):
        self.name = name

    def set_organizer(self, organizer):
        self.organizer = organizer
    
    def add_student(self, student):
        self.students.append(student)

    def set_num_groups(self, groups):
        self.num_groups = groups

    def set_group_size(self, max):
        self.group_size = max

    def set_details(self, details):
        self.details = details

    def get_name(self):
        return self.name
    
    def get_id(self):
        return self.id
    
    def get_organizer(self):
        return self.organizer
    
    def get_students(self):
        return self.students
    
    def get_num_groups(self):
        return self.num_groups
    
    def get_group_size(self):
        return self.group_size
    
    def get_details(self):
        return self.details
    
    @staticmethod
    def get_trips():
        return Trip.trips
    
    @staticmethod
    def get_trip_with_id(id):
        for trip in Trip.get_trips():
            if trip.get_id() == id:
                return trip

    @staticmethod
    def generate_id():
        id_length = 6
        letters = "ABCDEFGHJKLMNPQRSTUVWXYZ" # No "I" or "O" (too confusing with 1 and 0 numbers)
        nums = "0123456789"
        id = ""
        while True:
            id = ''.join(random.sample((letters + nums), id_length))
            if(id not in Trip.trip_ids):
                break
        return id

    def __str__(self):
        s = "[TRIP INFO - " + self.name + "]"
        s += "\nTrip ID = " + str(self.id)
        s += "\nOrganizer: " + self.organizer
        s += "\nTotal Students: " + str(len(self.students))
        s += "\nStudent Ids: " + str(self.students)
        s += "\nNumber of groups: " + str(self.num_groups)
        s += "\nStudents Per group: " + str(self.group_size)
        s += "\nDetails: " + self.details
        return s

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