import json
import os
import shutil
from scrapper import scrapeData
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time 
from dotenv import load_dotenv
load_dotenv()

def compareGrades(old_file, new_file):
    if not os.path.exists(old_file):
        print("Old grades not found. Skipping comparison.")
        return []

    with open(old_file, "r") as f:
        old_data = json.load(f)
    with open(new_file, "r") as f:
        new_data = json.load(f)

    updates = []

    for course, new_course_info in new_data.items():
        old_course_info = old_data.get(course, {})

        new_quizzes = new_course_info.get("Quizzes/Assignments", [])
        old_quizzes = old_course_info.get("Quizzes/Assignments", [])

        old_quiz_map = {q["Quiz/Assignment"]: q for q in old_quizzes}

        for new_q in new_quizzes:
            name = new_q["Quiz/Assignment"]
            grade = new_q["Grade"]

            if name not in old_quiz_map:
                updates.append(f"{course} - NEW quiz added: {name} -> {grade}")
            else:
                old_grade = old_quiz_map[name].get("Grade", "")
                if old_grade != grade:
                    updates.append(f"{course} - {name} updated: {old_grade} -> {grade}")

        new_mids = new_course_info.get("Midterms", [])
        old_mids = old_course_info.get("Midterms", [])

        old_mid_map = {m["Midterm"]: m for m in old_mids}

        for new_m in new_mids:
            name = new_m["Midterm"]
            grade = new_m["Grade"]

            if name not in old_mid_map:
                updates.append(f" NEW midterm added: {name} -> {grade}")
            else:
                old_grade = old_mid_map[name].get("Grade", "")
                if old_grade != grade:
                    updates.append(f" {name} updated: {old_grade} -> {grade}")
    return (updates)

def updateGrades():
    grades_file = "grades.json"
    old_file = "oldgrades.json"

    if not os.path.exists(old_file):
        with open(old_file, "w") as f:
            json.dump({}, f)

    if not os.path.exists(grades_file):
        with open(grades_file, "w") as f:
            json.dump({}, f)

    shutil.copyfile(grades_file, old_file)

    scrapeData()

    updates = compareGrades(old_file, grades_file)
    print(updates)

    if updates:
        send_email(
            os.getenv("EMAIL_ADDRESS"),
            os.getenv("EMAIL_ADDRESS"),
            "GRADE UPDATE",
            "\n".join(updates)
        )

def send_email(sender_email, receiver_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(sender_email, os.getenv("EMAIL_PASSWORD"))
        server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)
    finally:
        server.quit()

if __name__ == "__main__":
    scrapeData()
    while True:
        updateGrades()
        time.sleep(300)