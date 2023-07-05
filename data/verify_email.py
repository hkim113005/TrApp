import pandas as pd

valid_emails = []
for index, row in pd.read_csv("data/acs_emails.csv", usecols=["email"], dtype=str).iterrows():
    valid_emails.append(row["email"])

students = pd.read_csv("data/students.csv", usecols=["name", "email"], dtype=str)

for index, row in students.iterrows():
    if row["email"].lower() not in valid_emails:
        print(row["name"] + ": " + row["email"].lower())
