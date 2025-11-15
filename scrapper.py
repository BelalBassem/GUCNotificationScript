from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import json
import time
from dotenv import load_dotenv
load_dotenv()
import os

def scrapeData():
    GUC_USERNAME = os.getenv("GUC_USERNAME")
    GUC_PASSWORD = os.getenv("GUC_PASSWORD")
    DATA_FILE = "grades.json"

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    grades_url = f"https://{GUC_USERNAME}:{GUC_PASSWORD}@apps.guc.edu.eg/student_ext/Grade/CheckGrade_01.aspx"
    driver.get(grades_url)

    dropdown_element = wait.until(
        EC.presence_of_element_located((By.ID, "ContentPlaceHolderright_ContentPlaceHoldercontent_smCrsLst"))
    )
    dropdown = Select(dropdown_element)
    course_names = [opt.text.strip() for opt in dropdown.options if opt.get_attribute("value") != ""]

    grades_data = {}

    for course_name in course_names:
        dropdown_element = wait.until(
            EC.presence_of_element_located((By.ID, "ContentPlaceHolderright_ContentPlaceHoldercontent_smCrsLst"))
        )
        dropdown = Select(dropdown_element)
        dropdown.select_by_visible_text(course_name)
        time.sleep(2)  

        course_info = {"Quizzes/Assignments": []}

        try:
            i = 0
            while True:
                quiz_rows = driver.find_elements(By.ID, f"ContentPlaceHolderright_ContentPlaceHoldercontent_rptrNtt_stdRw_{i}")
                if not quiz_rows: 
                    break

                for row in quiz_rows:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 3: 
                        course_info["Quizzes/Assignments"].append({
                            "Quiz/Assignment": tds[0].text.strip(),
                            "Grade": tds[2].text.strip()    
                        })

                i += 1
        except Exception as e:
            print("Error scraping quizzes:", e)

        grades_data[course_name] = course_info


    try:
        course_info["Midterms"] = []

        
        midterm_table = driver.find_element(By.ID, "ContentPlaceHolderright_ContentPlaceHoldercontent_midDg")
        rows = midterm_table.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
        
            if len(tds) >= 2:
                course_name = tds[0].text.strip()
                grade = tds[1].text.strip()
                if course_name and grade:
                    course_info["Midterms"].append({
                        "Midterm": course_name,
                        "Grade": grade
                    })

        if not course_info["Midterms"]:
            print("No midterms found.")
    except Exception as e:
        print("Error scraping midterms:", e)


    with open(DATA_FILE, "w") as f:
        json.dump(grades_data, f, indent=4)

    print("Grades scraped successfully!")
    driver.quit()
