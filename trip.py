import uuid

class Trip:
    trips = []
    def __init__(self, name, trip_type, num_rooms, max_per_room, preferences, students):
        # Have either num_rooms or max_per_room and calculate the other variable based on the one that wasn't entered
        self.name = name
        self.id = uuid.uuid4()
        self.trip_type = trip_type
        self.students = students
        self.num_rooms = num_rooms
        self.max_per_room = max_per_room
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

    def set_max_per_room(self, max):
        self.max_per_room = max

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
    
    def get_max_per_room(self):
        return self.num_rooms
    
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
        s += "\nStudents Per Room: " + str(self.max_per_room)
        s += "\nPreferences: " + self.preferences
        return s
    
test_trip1 = Trip("TSU 2023", "Test Trip to Ohio", 5, 2, "blah blah blah", [f"student-{i}-id" for i in range(1, 11)])
test_trip2 = Trip("Random Adventure", "Random trip idk", 100, 2, "more random details", [f"student-{i}-id" for i in range(10, 21)])
print(test_trip1)
print()
print(Trip.get_trips()[1])