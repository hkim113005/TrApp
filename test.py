def assign_rooms(students, k):
    # Initialize each student with their top preference
    for student in students:
        student.current_roommate = student.preferences[0]
    
    # Initialize each room with an empty list of occupants
    rooms = [[] for _ in range(k)]
    
    # Loop until all students are assigned to a room
    while any(student.current_room is None for student in students):
        # Select an unassigned student
        free_student = next(student for student in students if student.current_room is None)
        
        # Iterate through the free student's preferred roommates
        for potential_roommate in free_student.preferences:
            # If the potential roommate is also unassigned, assign them to a room together
            if potential_roommate.current_room is None:
                free_student.current_room = potential_roommate.current_room = len(rooms)
                rooms[-1].append(free_student)
                break
            # If the potential roommate is already assigned, check their preference
            elif potential_roommate.preferences.index(free_student) < potential_roommate.preferences.index(potential_roommate.current_roommate):
                # Unassign the potential roommate's current roommate and assign them to the room with the free student
                prev_room = potential_roommate.current_room
                potential_roommate.current_room = len(rooms)
                free_student.current_room = prev_room
                rooms[-1].append(potential_roommate)
                rooms[prev_room].remove(potential_roommate)
                break
    
    return rooms

# Define the students and their preferences
students = [
    Student('Alice', ['Bob', 'Charlie', 'David', 'Eve', 'Frank']),
    Student('Bob', ['Alice', 'Charlie', 'Eve', 'David', 'Frank']),
    Student('Charlie', ['Alice', 'Bob', 'David', 'Eve', 'Frank']),
    Student('David', ['Alice', 'Bob', 'Charlie', 'Eve', 'Frank']),
    Student('Eve', ['Alice', 'Bob', 'Charlie', 'David', 'Frank']),
    Student('Frank', ['Alice', 'Bob', 'Charlie', 'David', 'Eve']),
    Student('George', ['Hannah', 'Isaac', 'Jane', 'Kelly', 'Lucas']),
    Student('Hannah', ['George', 'Isaac', 'Jane', 'Lucas', 'Kelly']),
    Student('Isaac', ['George', 'Hannah', 'Jane', 'Kelly', 'Lucas']),
    Student('Jane', ['George', 'Hannah', 'Isaac', 'Lucas', 'Kelly']),
    Student('Kelly', ['George', 'Hannah', 'Isaac', 'Jane', 'Lucas']),
    Student('Lucas', ['George', 'Hannah', 'Isaac', 'Jane', 'Kelly']),
    Student('Maggie', ['Nate', 'Olivia', 'Peter', 'Quincy', 'Rose']),
    Student('Nate', ['Maggie', 'Olivia', 'Peter', 'Quincy', 'Rose']),
    Student('Olivia', ['Maggie', 'Nate', 'Peter', 'Quincy', 'Rose']),
    Student('Peter', ['Maggie', 'Nate', 'Olivia', 'Quincy', 'Rose']),
    Student('Quincy', ['Maggie', 'Nate', 'Olivia', 'Peter', 'Rose']),
    Student('Rose', ['Maggie', 'Nate', 'Olivia', 'Peter', 'Quincy']),
    Student('Sam', ['Tina', 'Uma', 'Victor', 'Wendy', 'Xavier']),
    Student('Tina', ['Sam', 'Uma', 'Victor', 'Wendy', 'Xavier']),
    Student('Uma', ['Sam', 'Tina', 'Victor', 'Wendy', 'Xavier']),
    Student('Victor', ['Sam', 'Tina', 'Uma', 'Wendy', 'Xavier']),
    Student('Wendy', ['Sam', 'Tina', 'Uma', 'Victor', 'Xavier']),
    Student('Xavier', ['Sam', 'Tina', 'Uma', 'Victor', 'Wendy'])
]

# Assign the students to rooms
rooms = assign_rooms(students, 7)

# Print the room assignments
for i, room in enumerate(rooms):
    print(f'Room {i+1}:')
    for student in room:
        print(f'  {student.name} (wants to room with {student.preferences})')


