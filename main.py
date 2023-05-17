import math
import random

SIZE = 12
GROUP_SIZE = 5
NUM_GROUP = math.ceil(SIZE / GROUP_SIZE)

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

students = []
preferences = []

best_result = 100

"""
for i in range(SIZE):
    temp = []
    while len(temp) < 5:
        num = random.randint(0, SIZE - 1)
        if num not in temp and num != i:
            temp.append(num)
    preferences.append(temp)
"""

preferences = [
    [5, 6, 3, 10, 4],
    [0, 6, 8, 7, 4],
    [11, 0, 4, 8, 1],
    [1, 6, 8, 0, 2],
    [10, 0, 1, 6, 2],
    [3, 7, 10, 8, 9],
    [9, 3, 2, 11, 4],
    [8, 1, 10, 2, 6],
    [6, 4, 1, 0, 2],
    [10, 6, 1, 3, 5],
    [4, 0, 8, 3, 11],
    [9, 6, 2, 7, 8]
]

for i in range(100):
    # Init students
    for j in range(SIZE):
        students.append(j)

    #Init groups
    groups = []
    for i in range(NUM_GROUP):
        groups.append(Group())

    #Randomize students
    random.shuffle(students)

    #Add random student as group member
    for j in range(NUM_GROUP):
        groups[j].add(students.pop())


    while len(students) > 0:
        for j in range(NUM_GROUP):
            if groups[j].get_size() <= GROUP_SIZE and len(students) > 0:
                students.remove(groups[j].add_best(students, preferences))
    
    
    """
    results = [0, 0, 0, 0]

    for j in range(NUM_GROUP):
        count = 0
        for member1 in groups[j].members:
            satisfied = False
            for member2 in groups[j].members:
                if member2 in preferences[member1]:
                    satisfied = True
                    break
            if satisfied:
                count += 1

        results[count] += 1
        """

    for j in range(15):
        for group1 in groups:
            for member1 in group1.members:
                for group2 in groups:
                    if group1 == group2:
                        continue
                    for member2 in group2.members:
                        current_value = group1.get_value(preferences) + group2.get_value(preferences)
                        group1.remove(member1)
                        group2.remove(member2)
                        group1.add(member2)
                        group2.add(member1)
                        possible_value = group1.get_value(preferences) + group2.get_value(preferences)
                        if current_value >= possible_value:
                            group1.remove(member2)
                            group2.remove(member1)
                            group1.add(member1)
                            group2.add(member2)
                        else:
                            member1, member2 = member2, member1

    """
    results = [0, 0, 0, 0,0]
    unhappy = 0

    for j in range(NUM_GROUP):
        count = 0
        for member1 in groups[j].members:
            satisfied = False
            for member2 in groups[j].members:
                if member1 == member2:
                    continue
                if member2 in preferences[member1]:
                    satisfied = True
                    break
            if satisfied:
                count += 1

        unhappy += groups[j].get_size() - count

        results[count] += 1

    best_result = min(best_result, unhappy)
    """

for group in groups:
    print(group)