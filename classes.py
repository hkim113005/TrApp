import uuid

class Student:
    student_count = 0
    def __init__(self, name, email, grade, gender, preferences):
        # Have either num_rooms or max_per_room and calculate the other variable based on the one that wasn't entered
        self.name = str(name)
        self.id = (Student.student_count + 1)
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