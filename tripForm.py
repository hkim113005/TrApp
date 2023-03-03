def form(trip):
    total_students = trip.get_students()

    user_ID = input("Enter your User ID: ")

    while not user_ID in total_students:
        user_ID = input("Please enter a valid User ID: ")

    user = Student.get_student(user_ID)

    try_pass = input("Hello " + user_ID.get_name + ", enter your password: ")

    while not user.check_password(try_pass):
        try_pass = input("This password was incorrect. Try again: ")

    preference_list = []
    valid = True

    for i in range(5):
        while valid:
            target_ID = input("Enter preference number " + i + ": ")

            if target_ID in total_students or not target_ID in preference_list:
                valid = False
            else:
                print("This is invalid as it's either not a valid student, or you have already selected this student.")
        
        preference_list.append(target_ID)
        valid = True