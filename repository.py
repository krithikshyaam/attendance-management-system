# ====================================================================
# REPOSITORY.PY
# Contains SQL operations used by the GUI.
# Application flow: gui.py -> repository.py -> database.py -> MySQL.
# ====================================================================
from database import fetch_all, fetch_one, execute_query


# -------------------- Master Data --------------------

# ------------------------------------------------------------
# Returns Department records for forms and dropdowns.
# ------------------------------------------------------------
def get_departments():
    return fetch_all("""
        SELECT department_id, department_code, department_name
        FROM department ORDER BY department_name
    """)



# ------------------------------------------------------------
# Returns Class records joined with Department information.
# ------------------------------------------------------------
def get_classes():
    return fetch_all("""
        SELECT c.class_id, c.class_name, c.semester, c.section,
               c.department_id, d.department_code
        FROM `class` c
        JOIN department d ON d.department_id = c.department_id
        ORDER BY d.department_code, c.semester, c.section
    """)


# -------------------- Students --------------------

# ------------------------------------------------------------
# Returns Student records joined with readable Department and Class values.
# ------------------------------------------------------------
def get_students():
    return fetch_all("""
        SELECT s.student_id, s.roll_no, s.student_name, s.email,
               s.phone, s.gender, d.department_code,
               CONCAT(c.class_name, '-', c.section), s.admission_year
        FROM student s
        JOIN department d ON d.department_id = s.department_id
        JOIN `class` c ON c.class_id = s.class_id
        ORDER BY s.roll_no
    """)



# ------------------------------------------------------------
# Returns compact Student data used by the attendance dropdown, including class_id.
# ------------------------------------------------------------
def get_student_choices():
    return fetch_all("""
        SELECT student_id, roll_no, student_name, class_id
        FROM student ORDER BY roll_no
    """)



# ------------------------------------------------------------
# Inserts one Student with parameterized SQL.
# ------------------------------------------------------------
def add_student(data):
    return execute_query("""
        INSERT INTO student
        (roll_no, student_name, email, phone, gender,
         department_id, class_id, admission_year)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["roll_no"], data["student_name"], data["email"] or None,
        data["phone"] or None, data["gender"], data["department_id"],
        data["class_id"], data["admission_year"],
    ))



# ------------------------------------------------------------
# Deletes the selected Student unless MySQL blocks deletion because related attendance exists.
# ------------------------------------------------------------
def delete_student(student_id):
    execute_query("DELETE FROM student WHERE student_id=%s", (student_id,))


# -------------------- Teachers --------------------

# ------------------------------------------------------------
# Returns Teacher records joined with Department.
# ------------------------------------------------------------
def get_teachers():
    return fetch_all("""
        SELECT t.teacher_id, t.teacher_code, t.teacher_name, t.email,
               t.phone, d.department_code, t.designation
        FROM teacher t
        JOIN department d ON d.department_id = t.department_id
        ORDER BY t.teacher_code
    """)



# ------------------------------------------------------------
# Inserts one Teacher record.
# ------------------------------------------------------------
def add_teacher(data):
    return execute_query("""
        INSERT INTO teacher
        (teacher_code, teacher_name, email, phone, department_id, designation)
        VALUES (%s,%s,%s,%s,%s,%s)
    """, (
        data["teacher_code"], data["teacher_name"], data["email"] or None,
        data["phone"] or None, data["department_id"], data["designation"] or None,
    ))



# ------------------------------------------------------------
# Deletes the selected Teacher when no dependent records prevent deletion.
# ------------------------------------------------------------
def delete_teacher(teacher_id):
    execute_query("DELETE FROM teacher WHERE teacher_id=%s", (teacher_id,))


# -------------------- Subjects --------------------

# ------------------------------------------------------------
# Returns Subject records joined with Department.
# ------------------------------------------------------------
def get_subjects():
    return fetch_all("""
        SELECT s.subject_id, s.subject_code, s.subject_name,
               s.semester, d.department_code
        FROM subject s
        JOIN department d ON d.department_id = s.department_id
        ORDER BY s.subject_code
    """)



# ------------------------------------------------------------
# Inserts one Subject record.
# ------------------------------------------------------------
def add_subject(data):
    return execute_query("""
        INSERT INTO subject (subject_code, subject_name, semester, department_id)
        VALUES (%s,%s,%s,%s)
    """, (
        data["subject_code"], data["subject_name"],
        data["semester"], data["department_id"],
    ))



# ------------------------------------------------------------
# Deletes the selected Subject when it is not referenced by timetable or attendance.
# ------------------------------------------------------------
def delete_subject(subject_id):
    execute_query("DELETE FROM subject WHERE subject_id=%s", (subject_id,))


# -------------------- Periods / Timetable --------------------

# ------------------------------------------------------------
# Returns Period 1 to Period 7 and their timings.
# ------------------------------------------------------------
def get_periods():
    return fetch_all("""
        SELECT period_no, period_name, start_time, end_time
        FROM period_master ORDER BY period_no
    """)



# ------------------------------------------------------------
# Returns complete day slots, including Break 1, Lunch and Break 2.
# ------------------------------------------------------------
def get_day_slots():
    return fetch_all("""
        SELECT slot_order, slot_type, slot_name, period_no, start_time, end_time
        FROM day_slot ORDER BY slot_order
    """)



# ------------------------------------------------------------
# Returns the Subject and Teacher assigned to one Class + Day + Period.
# ------------------------------------------------------------
def get_period_assignment(class_id, day_of_week, period_no):
    return fetch_one("""
        SELECT pt.subject_id, s.subject_code, s.subject_name,
               pt.teacher_id, t.teacher_code, t.teacher_name
        FROM period_timetable pt
        JOIN subject s ON s.subject_id = pt.subject_id
        JOIN teacher t ON t.teacher_id = pt.teacher_id
        WHERE pt.class_id=%s AND pt.day_of_week=%s AND pt.period_no=%s
        LIMIT 1
    """, (class_id, day_of_week, period_no))



# ------------------------------------------------------------
# Returns the complete readable timetable using JOINs.
# ------------------------------------------------------------
def get_all_timetables():
    return fetch_all("""
        SELECT d.department_code,
               CONCAT(c.class_name, '-', c.section),
               pt.day_of_week, pt.period_no, pm.start_time, pm.end_time,
               s.subject_code, s.subject_name, t.teacher_name
        FROM period_timetable pt
        JOIN `class` c ON c.class_id = pt.class_id
        JOIN department d ON d.department_id = c.department_id
        JOIN period_master pm ON pm.period_no = pt.period_no
        JOIN subject s ON s.subject_id = pt.subject_id
        JOIN teacher t ON t.teacher_id = pt.teacher_id
        ORDER BY c.class_id,
          FIELD(pt.day_of_week,'MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY'),
          pt.period_no
    """)



# ------------------------------------------------------------
# Returns the weekly timetable for one class_id.
# ------------------------------------------------------------
def get_class_timetable(class_id):
    return fetch_all("""
        SELECT pt.day_of_week, pt.period_no, pm.start_time, pm.end_time,
               s.subject_code, s.subject_name, t.teacher_code, t.teacher_name
        FROM period_timetable pt
        JOIN period_master pm ON pm.period_no = pt.period_no
        JOIN subject s ON s.subject_id = pt.subject_id
        JOIN teacher t ON t.teacher_id = pt.teacher_id
        WHERE pt.class_id=%s
        ORDER BY
          FIELD(pt.day_of_week,'MONDAY','TUESDAY','WEDNESDAY','THURSDAY','FRIDAY','SATURDAY'),
          pt.period_no
    """, (class_id,))


# -------------------- Attendance --------------------

# ------------------------------------------------------------
# Checks whether the same Student already has attendance for the same Date and Period.
# ------------------------------------------------------------
def attendance_exists(student_id, attendance_date, period_no):
    return fetch_one("""
        SELECT attendance_id FROM attendance
        WHERE student_id=%s AND attendance_date=%s AND period_no=%s
        LIMIT 1
    """, (student_id, attendance_date, period_no))



# ------------------------------------------------------------
# Validates Period 1-7, prevents duplicate attendance, and inserts the attendance row.
# ------------------------------------------------------------
def mark_attendance(data):
    if data["period_no"] not in range(1, 8):
        raise ValueError("Period must be from 1 to 7.")

    if attendance_exists(data["student_id"], data["attendance_date"], data["period_no"]):
        raise ValueError("Attendance already exists for this student, date and period.")

    return execute_query("""
        INSERT INTO attendance
        (student_id, subject_id, teacher_id, attendance_date, period_no, status, remarks)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        data["student_id"], data["subject_id"], data["teacher_id"],
        data["attendance_date"], data["period_no"],
        data["status"], data["remarks"] or None,
    ))



# ------------------------------------------------------------
# Returns all attendance joined with Student, Subject and Teacher names.
# ------------------------------------------------------------
def get_all_attendance():
    return fetch_all("""
        SELECT a.attendance_id, s.roll_no, s.student_name,
               CONCAT('P', COALESCE(a.period_no,1)), sub.subject_code,
               sub.subject_name, t.teacher_name, a.attendance_date,
               a.status, COALESCE(a.remarks,'')
        FROM attendance a
        JOIN student s ON s.student_id = a.student_id
        JOIN subject sub ON sub.subject_id = a.subject_id
        JOIN teacher t ON t.teacher_id = a.teacher_id
        ORDER BY a.attendance_date DESC, a.period_no, s.roll_no
    """)



# ------------------------------------------------------------
# Returns only one Student's attendance rows.
# ------------------------------------------------------------
def get_student_attendance(student_id):
    return fetch_all("""
        SELECT a.attendance_id, CONCAT('P', COALESCE(a.period_no,1)),
               sub.subject_code, sub.subject_name, t.teacher_name,
               a.attendance_date, a.status, COALESCE(a.remarks,'')
        FROM attendance a
        JOIN subject sub ON sub.subject_id = a.subject_id
        JOIN teacher t ON t.teacher_id = a.teacher_id
        WHERE a.student_id=%s
        ORDER BY a.attendance_date DESC, a.period_no
    """, (student_id,))



# ------------------------------------------------------------
# Calculates total periods, attended periods and overall attendance percentage for every Student.
# ------------------------------------------------------------
def get_all_percentages():
    return fetch_all("""
        SELECT s.roll_no, s.student_name,
               COUNT(a.attendance_id) AS total_periods,
               SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) AS attended,
               ROUND(
                 SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END)
                 * 100.0 / COUNT(a.attendance_id), 2
               ) AS percentage
        FROM student s
        JOIN attendance a ON a.student_id=s.student_id
        GROUP BY s.student_id, s.roll_no, s.student_name
        ORDER BY s.roll_no
    """)



# ------------------------------------------------------------
# Calculates subject-wise attendance percentage for one Student.
# ------------------------------------------------------------
def get_student_percentage(student_id):
    return fetch_all("""
        SELECT sub.subject_code, sub.subject_name,
               COUNT(a.attendance_id) AS total_periods,
               SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END) AS attended,
               ROUND(
                 SUM(CASE WHEN a.status IN ('Present','Late') THEN 1 ELSE 0 END)
                 * 100.0 / COUNT(a.attendance_id), 2
               ) AS percentage
        FROM attendance a
        JOIN subject sub ON sub.subject_id=a.subject_id
        WHERE a.student_id=%s
        GROUP BY sub.subject_id, sub.subject_code, sub.subject_name
        ORDER BY sub.subject_code
    """, (student_id,))


# -------------------- Login Users --------------------

# ------------------------------------------------------------
# Returns login users for the Admin Users page.
# ------------------------------------------------------------
def get_users():
    return fetch_all("SELECT user_id, username, role FROM user_login ORDER BY user_id")



# ------------------------------------------------------------
# Inserts username, password and role into user_login.
# ------------------------------------------------------------
def add_user(username, password, role):
    return execute_query(
        "INSERT INTO user_login (username,password,role) VALUES (%s,%s,%s)",
        (username, password, role),
    )



# ------------------------------------------------------------
# Deletes a login user. Current logged-in Admin should not delete their own account.
# ------------------------------------------------------------
def delete_user(user_id):
    execute_query("DELETE FROM user_login WHERE user_id=%s", (user_id,))


# -------------------- Dashboard / Reference Timetable --------------------

# ------------------------------------------------------------
# Returns class metadata used in the dashboard cards.
# COUNT gives class strength; MIN(admission_year) is used to show
# a simple four-year batch range such as 2023 - 2027.
# ------------------------------------------------------------
def get_class_dashboard_summary(class_id):
    return fetch_one("""
        SELECT c.class_id,
               d.department_code,
               d.department_name,
               c.class_name,
               c.semester,
               c.section,
               COUNT(s.student_id) AS class_strength,
               MIN(s.admission_year) AS admission_year
        FROM `class` c
        JOIN department d ON d.department_id = c.department_id
        LEFT JOIN student s ON s.class_id = c.class_id
        WHERE c.class_id = %s
        GROUP BY c.class_id, d.department_code, d.department_name,
                 c.class_name, c.semester, c.section
    """, (class_id,))


# ------------------------------------------------------------
# Returns the lower "Course Handling Summary" shown below the timetable.
# COUNT(timetable_id) works as Hours/Week because one timetable row
# represents one scheduled teaching period.
# ------------------------------------------------------------
def get_class_course_summary(class_id):
    return fetch_all("""
        SELECT sub.subject_code,
               sub.subject_name,
               CONCAT(t.teacher_code, ' - ', t.teacher_name) AS staff,
               COUNT(pt.timetable_id) AS hours_per_week
        FROM period_timetable pt
        JOIN subject sub ON sub.subject_id = pt.subject_id
        JOIN teacher t ON t.teacher_id = pt.teacher_id
        WHERE pt.class_id = %s
        GROUP BY sub.subject_id, sub.subject_code, sub.subject_name,
                 t.teacher_id, t.teacher_code, t.teacher_name
        ORDER BY sub.subject_code
    """, (class_id,))


# ------------------------------------------------------------
# Attendance report query with optional filters.
# All values still use %s placeholders, including LIKE search values.
# ------------------------------------------------------------
def get_attendance_report(student_search="", date_from="", date_to="", status="All"):
    query = """
        SELECT a.attendance_id, s.roll_no, s.student_name,
               CONCAT('P', COALESCE(a.period_no,1)), sub.subject_code,
               sub.subject_name, t.teacher_name, a.attendance_date,
               a.status, COALESCE(a.remarks,'')
        FROM attendance a
        JOIN student s ON s.student_id = a.student_id
        JOIN subject sub ON sub.subject_id = a.subject_id
        JOIN teacher t ON t.teacher_id = a.teacher_id
        WHERE 1 = 1
    """
    params = []

    if student_search:
        search_value = f"%{student_search}%"
        query += " AND (s.roll_no LIKE %s OR s.student_name LIKE %s)"
        params.extend([search_value, search_value])

    if date_from:
        query += " AND a.attendance_date >= %s"
        params.append(date_from)

    if date_to:
        query += " AND a.attendance_date <= %s"
        params.append(date_to)

    if status and status != "All":
        query += " AND a.status = %s"
        params.append(status)

    query += " ORDER BY a.attendance_date DESC, a.period_no, s.roll_no"
    return fetch_all(query, tuple(params))
