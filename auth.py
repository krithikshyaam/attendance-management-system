from database import fetch_one


ROLE_PERMISSIONS = {
    "admin": {
        "view_students", "manage_students",
        "view_teachers", "manage_teachers",
        "view_subjects", "manage_subjects",
        "view_timetable", "mark_attendance",
        "view_all_attendance", "view_all_percentage",
        "manage_users",
    },
    "teacher": {
        "view_students", "view_subjects",
        "view_timetable", "mark_attendance",
        "view_all_attendance", "view_all_percentage",
    },
    "student": {
        "view_own_profile", "view_own_timetable",
        "view_own_attendance", "view_own_percentage",
    },
}


def authenticate(username, password):
    row = fetch_one(
        """
        SELECT user_id, username, role
        FROM user_login
        WHERE username = %s AND password = %s
        """,
        (username, password),
    )
    if not row:
        return None
    return {
        "user_id": row[0],
        "username": row[1],
        "role": row[2].strip().lower(),
    }


def has_permission(user, permission):
    return bool(user) and permission in ROLE_PERMISSIONS.get(user["role"], set())


def find_student_for_login(username):
    return fetch_one(
        """
        SELECT student_id, roll_no, student_name, email, phone,
               gender, department_id, class_id, admission_year
        FROM student
        WHERE LOWER(roll_no) = LOWER(%s)
           OR LOWER(SUBSTRING_INDEX(COALESCE(email, ''), '@', 1)) = LOWER(%s)
        LIMIT 1
        """,
        (username, username),
    )


def find_teacher_for_login(username):
    return fetch_one(
        """
        SELECT teacher_id, teacher_code, teacher_name
        FROM teacher
        WHERE LOWER(teacher_code) = LOWER(%s)
           OR LOWER(SUBSTRING_INDEX(COALESCE(email, ''), '@', 1)) = LOWER(%s)
        LIMIT 1
        """,
        (username, username),
    )
