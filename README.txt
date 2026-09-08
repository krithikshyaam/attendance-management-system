ATTENDANCE MANAGEMENT SYSTEM - TKINTER GUI
===========================================

This version converts the command-line project into a Tkinter desktop form.

PROJECT FILES
-------------
config.py       - MySQL host, port, username, password and database.
database.py     - Common MySQL connection/query functions.
auth.py         - Login and role-based permissions.
repository.py   - All SELECT/INSERT/DELETE database operations.
gui.py          - Tkinter forms/screens.
main.py         - Starts the application.
test_db.py      - Simple database connection test.
requirements.txt

ROLE ACCESS
-----------

ADMIN
- View Students
- Add/Delete Students
- View Teachers
- Add/Delete Teachers
- View Subjects
- Add/Delete Subjects
- Mark Attendance
- View all Attendance
- View all Attendance Percentage
- Add/Delete Login Users

TEACHER
- View Students
- View Subjects
- Mark Attendance
- View all Attendance
- View Attendance Percentage
- Cannot add/delete Students
- Cannot add/delete Teachers
- Cannot add/delete Subjects
- Cannot manage Login Users

STUDENT
- View own Profile only
- View own Attendance only
- View own Attendance Percentage only
- Cannot mark attendance
- Cannot modify master data
- Cannot view other students' attendance

IMPORTANT LOGIN LINKING
-----------------------
Your existing user_login table contains username/password/role only.
It does not contain student_id or teacher_id.

Therefore this project links:

Student:
  user_login.username = student.roll_no

Example:
  Username: 23CS001
  Student Roll No: 23CS001

Teacher:
  Username can match teacher_code OR the part of teacher email before @.

Example:
  Username: kumar
  Teacher email: kumar@college.edu

DATABASE SETUP
--------------
Your existing SQL database must already contain:

department
class
student
teacher
subject
attendance
user_login

Before running the GUI, verify in MySQL Workbench:

USE attendance_system;

SHOW TABLES;

SELECT * FROM student;
SELECT * FROM teacher;
SELECT * FROM subject;
SELECT * FROM attendance;
SELECT * FROM user_login;

MYSQL SETTINGS
--------------
Open config.py:

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "attendance_system",
}

Replace YOUR_MYSQL_PASSWORD with your actual MySQL password.

If your WAMP root account truly has no password:

"password": ""

INSTALL
-------
Open Terminal / PyCharm terminal inside this project folder:

pip install -r requirements.txt

Tkinter is normally included with standard Windows Python.
You do not normally install tkinter with pip.

TEST DATABASE
-------------
python test_db.py

Expected:

SUCCESS: Database connected successfully.

RUN GUI
-------
python main.py

SAMPLE USERS FROM THE PREVIOUS SQL
----------------------------------
Admin:
  username: admin
  password: admin123

Teacher:
  username: kumar
  password: teacher123

Student:
  username: 23CS001
  password: student123

COMMON ERRORS
-------------

1045 Access denied
- Wrong MySQL username/password.
- Check config.py.

2003 Can't connect
- WAMP MySQL may not be running.
- Port may be wrong.
- Your screenshot showed localhost:3306, so use 3306.

1049 Unknown database
- attendance_system does not exist.

1146 Table doesn't exist
- SQL files were not run in the correct order.

1062 Duplicate entry
- Roll No, email, teacher code, subject code or username already exists.

1451 Cannot delete parent row
- You are trying to delete Student/Teacher/Subject that is already used by attendance.

1452 Foreign key fails
- Selected Department/Class/Student/Teacher/Subject does not exist.

Student Link Missing
- Student login username does not match student's roll_no.
- Use the roll number as Student username.

SECURITY NOTE
-------------
The current college-project database stores login passwords in plain text because
the existing user_login SQL table was designed that way.

For a production application, change the login system to bcrypt or Argon2
password hashing.
