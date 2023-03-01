import math
import random

SIZE = 100
GROUP_SIZE = 3
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

for i in range(10):
    students = []
    preferences = []

    for i in range(SIZE):
        temp = []
        while len(temp) < 5:
            num = random.randint(0, SIZE - 1)
            if num not in temp and num != i:
                temp.append(num)
        students.append(i)
        preferences.append(temp)
        
    groups = []
    for i in range(NUM_GROUP):
        groups.append(Group())

    random.shuffle(students)

    for i in range(NUM_GROUP):
        groups[i].add(students.pop())

    while len(students) != 0:
        for i in range(NUM_GROUP):
            if groups[i].get_size() != GROUP_SIZE and len(students) != 0:
                students.remove(groups[i].add_best(students, preferences))

    results = [0, 0, 0, 0]

    for i in range(NUM_GROUP):
        count = 0
        for member1 in groups[i].members:
            satisfied = False
            for member2 in groups[i].members:
                if member2 in preferences[member1]:
                    satisfied = True
                    break
            if satisfied:
                count += 1

        results[count] += 1

    print(results)

    for i in range(NUM_GROUP):
        for j in range(NUM_GROUP):
            if i == j: continue
            