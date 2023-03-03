import sqlite3
from classes import Student, Trip


conn = sqlite3.connect("trApp.db")
c = conn.cursor()

tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
tables = [x[0] for x in tables]

if "students" not in tables:
    c.execute("CREATE TABLE students (id INTEGER, name TEXT, gender TEXT, grade INTEGER, PRIMARY KEY(id))")

if "trips" not in tables:
    c.execute("CREATE TABLE trips (id TEXT, name TEXT, type TEXT, num_rooms INTEGER, students_per_room INTEGER, preferences TEXT, PRIMARY KEY(id))")

if "trip_students" not in tables:
    c.execute("CREATE TABLE trip_students (trip_id TEXT, student_id INTEGER, FOREIGN KEY(trip_id) REFERENCES trips(id))")

students_raw = [
    {
        "name": "Jeremiah Mathew",
        "gender": "male",
        "grade": 10
    },
    {
        "name": "Hyungjae Kim",
        "gender": "male",
        "grade": 11
    },
    {
        "name": "Ryan Ayoub",
        "gender": "male",
        "grade": 10
    },
    {
        "name": "Lionel DeVisscher",
        "gender": "male",
        "grade": 10
    },
    {
        "name" : "Rohit Sundararaman",
        "gender": "male",
        "grade": 10
    },
    {
        "name": "Jiyun Kim",
        "gender": "female",
        "grade": 11
    },
    {
        "name": "Malek Zuhdi",
        "gender": "male",
        "grade": 9
    },
    {
        "name": "Jasir Zakaria",
        "gender": "male",
        "grade": 11
    },
    {
        "name": "GT",
        "gender": "male",
        "grade": 11
    },
    {
        "name": "Batu Sinanoglu",
        "gender": "male",
        "grade": 11
    },
    {
        "name": "Kyna Rochlani",
        "gender": "female",
        "grade": 11
    },
    {
        "name": "Matthew Sado",
        "gender": "male",
        "grade": 10
    },
    {
        "name": "Jehyeok Lee",
        "gender": "male",
        "grade": 10
    },
]
    
students = [Student(s['name'], s['gender'], s['grade'],"") for s in students_raw]

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

for s in students:
    c.execute("INSERT INTO students (id, name, gender, grade) VALUES(?, ?, ?, ?)", (s.get_id(), s.get_name(), s.get_gender(), s.get_grade()))

for t in trips:
    #c.execute("INSERT INTO trips (id, name, type, num_rooms, students_per_room, preferences) VALUES(?, ?, ?, ?, ?, ?)", t['id'], t['name'], t['type'], t['num_rooms'], t['students_per_room'], t['preferences'])
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