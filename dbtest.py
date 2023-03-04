import sqlite3
from classes import Student, Trip
import csv


conn = sqlite3.connect("data/TrApp.db")
c = conn.cursor()

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
tables = [x[0] for x in tables]

if "students" not in tables:
    c.execute("CREATE TABLE students (id INTEGER, name TEXT, email TEXT, grade INTEGER, gender TEXT, PRIMARY KEY(id))")
    file = open("data/students.csv", "r")
    data = list(csv.DictReader(file, delimiter=","))
    file.close()
    students = [Student(s['name'], s['email'], int(s['grade']), s['sex'], "") for s in data]
    for s in students:
        c.execute("INSERT INTO students (id, name, email, grade, gender) VALUES(?, ?, ?, ?, ?)", (int(s.get_id()), str(s.get_name()), str(s.get_email()), int(s.get_grade()), str(s.get_gender())))

if "trips" not in tables:
    c.execute("CREATE TABLE trips (id TEXT, name TEXT, type TEXT, num_rooms INTEGER, students_per_room INTEGER, preferences TEXT, PRIMARY KEY(id))")

if "trip_students" not in tables:
    c.execute("CREATE TABLE trip_students (trip_id TEXT, student_id INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")

"""
TEST STUDENTS ARRAY
students_raw = [
    {
        "name": "Jeremiah Mathew",
        "email": "jeremiahmathew@acs.sch.ae",
        "grade": 10,
        "gender": "M"
    },
    {
        "name": "Hyungjae Kim",
        "email": "hyungjaekim@acs.sch.ae",
        "grade": 11,
        "gender": "M"
    },
    {
        "name": "Ryan Ayoub",
        "email": "ryan-ramiayoub@acs.sch.ae",
        "grade": 10,
        "gender": "M"
    },
    {
        "name": "Lionel DeVisscher",
        "email": "lioneldevisscher@acs.sch.ae",
        "grade": 10,
        "gender": "M"
    },
    {
        "name" : "Rohit Sundararaman",
        "email": "rohitsundararaman@acs.sch.ae",
        "grade": 10,
        "gender": "M"
    },
    {
        "name": "Jiyun Kim",
        "email": "jiyunkim@acs.sch.ae",
        "grade": 11,
        "gender": "F"
    },
    {
        "name": "Malek Zuhdi",
        "email": "malekzuhdi@acs.sch.ae",
        "grade": 9,
        "gender": "M"
    },
    {
        "name": "Jasir Zakaria",
        "email": "jasirzakaria@acs.sch.ae",
        "grade": 11,
        "gender": "M"
    },
    {
        "name": "GT Heming",
        "email": "gordonheming@acs.sch.ae",
        "grade": 11,
        "gender": "M"
    },
    {
        "name": "Batu Sinanoglu",
        "email": "batusinanoglu@acs.sch.ae",
        "grade": 11,
        "gender": "M"
    },
    {
        "name": "Kyna Rochlani",
        "email": "kynarochlani@acs.sch.ae",
        "grade": 11,
        "gender": "F"
    },
    {
        "name": "Jehyeok Lee",
        "email": "jehyeoklee@acs.sch.ae",
        "grade": 10,
        "gender": "M"
    },
]
    
students = [Student(s['name'], s['gender'], s['grade'],"") for s in students_raw]
"""

trips = [
    {
        "id" : "blahblahtrip-1",
        "name" : "Test Trip",
        "type" : "MESAC",
        "students" : [1, 2, 3, 4],
        "num_rooms": 2,
        "students_per_room": 2,
        "preferences" : "idk"
    }
]

# This part doesn't work
for t in trips:
    c.execute("INSERT INTO trips (id, name, type, num_rooms, students_per_room, preferences) VALUES(?, ?, ?, ?, ?, ?)", (t['id'], t['name'], t['type'], t['num_rooms'], t['students_per_room'], t['preferences']))
    for id in t['students']:
        c.execute("INSERT INTO trip_students (trip_id, student_id) VALUES(?, ?)", (t['id'], id))

conn.commit()

c.execute('select * from students')
result = c.fetchall()
print(result)
print("")

c.execute('select * from trips')
result2 = c.fetchall()
print(result2)
print("")

c.execute('select * from trip_students')
result3 = c.fetchall()
print(result3)

conn.close()