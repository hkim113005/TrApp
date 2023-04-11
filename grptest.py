import random

def create_groups(num_groups, group_size, students_choices):
    # Create a list of student ids from the choices list
    student_ids = [d['id'] for d in students_choices]
    # Shuffle the list of student ids to randomize the order
    random.shuffle(student_ids)
    
    # Create a dictionary to store the choices for each student
    student_choices = {d['id']: set(d.values()) - {d['id']} for d in students_choices}
    
    # Create a list to store the groups
    groups = [[] for _ in range(num_groups)]
    
    # Keep track of which students have been assigned to a group
    assigned_students = set()
    
    # Iterate over the student ids and assign them to a group
    for student_id in student_ids:
        # Check if the student has any choices left that are not already in their group
        available_choices = student_choices[student_id] - set(sum(groups, [])) - assigned_students
        if available_choices and len(groups[student_id % num_groups]) < group_size:
            # Choose a partner at random from the available choices
            partner_id = random.choice(list(available_choices))
            # Add the student and their partner to the same group
            groups[student_id % num_groups].extend([student_id, partner_id])
            # Remove the partner from the choices of all other students
            for choice_set in student_choices.values():
                if partner_id in choice_set:
                    choice_set.remove(partner_id)
            # Add both students to the set of assigned students
            assigned_students.update([student_id, partner_id])
    
    # Add any remaining students to the groups at random
    remaining_students = set(student_ids) - set(sum(groups, [])) - assigned_students
    remaining_students = list(remaining_students)
    random.shuffle(remaining_students)
    for i, student_id in enumerate(remaining_students):
        groups[i % num_groups].append(student_id)
    
    return groups

students_choices = [
    {'id': 0, 'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5},
    {'id': 1, 'a': 0, 'b': 2, 'c': 3, 'd': 4, 'e': 5},
    {'id': 2, 'a': 0, 'b': 1, 'c': 3, 'd': 4, 'e': 5},
    {'id': 3, 'a': 0, 'b': 1, 'c': 2, 'd': 4, 'e': 5},
    {'id': 4, 'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 5},
    {'id': 5, 'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4},
]

groups = create_groups(num_groups=2, group_size=3, students_choices=students_choices)

print(groups)