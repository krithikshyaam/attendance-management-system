# ====================================================================
# GUI.PY
# Contains the complete Tkinter desktop interface.
# Important widgets: Tk, Frame, Label, Entry, Combobox, Button, Treeview, Toplevel and messagebox.
# ====================================================================
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import csv
from pathlib import Path

from database import test_connection
from auth import authenticate, has_permission, find_student_for_login, find_teacher_for_login
import repository as repo


class AttendanceApp(tk.Tk):

    # ------------------------------------------------------------
    # Creates the main Tkinter window, initializes user/session variables, applies the theme, and opens the Login screen.
    # ------------------------------------------------------------
    def __init__(self):
        # Main window configuration.
        super().__init__()
        self.title("Attendance Management System - Smart Timetable Dashboard")
        self.geometry("1450x860")
        self.minsize(1180, 720)

        # Logged-in account references.
        self.current_user = None
        self.student_record = None
        self.teacher_record = None

        # Central color palette used by the modern dashboard.
        self.colors = {
            "navy": "#102A43",
            "navy_2": "#163B63",
            "sidebar": "#0B2239",
            "accent": "#2F6FED",
            "accent_hover": "#255CC4",
            "bg": "#F4F7FB",
            "card": "#FFFFFF",
            "border": "#D9E2EC",
            "text": "#243B53",
            "muted": "#627D98",
            "break": "#FFF1CC",
            "lunch": "#E7F4EA",
            "period": "#EDF4FF",
        }

        self.configure(bg=self.colors["bg"])
        self._setup_styles()
        self.show_login()


    # ------------------------------------------------------------
    # Creates consistent ttk styles for the modern dashboard.
    # ------------------------------------------------------------
    def _setup_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Sidebar.TButton",
            background=self.colors["sidebar"],
            foreground="white",
            borderwidth=0,
            focusthickness=0,
            anchor="w",
            padding=(16, 11),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", self.colors["navy_2"])],
            foreground=[("active", "white")],
        )

        style.configure(
            "Primary.TButton",
            background=self.colors["accent"],
            foreground="white",
            borderwidth=0,
            padding=(14, 8),
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "Primary.TButton",
            background=[("active", self.colors["accent_hover"])],
            foreground=[("active", "white")],
        )

        style.configure(
            "Secondary.TButton",
            background="#E9EFF8",
            foreground=self.colors["navy"],
            borderwidth=0,
            padding=(12, 8),
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Secondary.TButton", background=[("active", "#DCE6F3")])

        style.configure(
            "Treeview",
            background="white",
            fieldbackground="white",
            foreground=self.colors["text"],
            rowheight=30,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=self.colors["navy"],
            foreground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padding=(6, 8),
        )
        style.map("Treeview.Heading", background=[("active", self.colors["navy_2"])])

        style.configure("TLabelFrame", background=self.colors["bg"])
        style.configure("TLabelFrame.Label", foreground=self.colors["navy"], font=("Segoe UI", 10, "bold"))

    # ------------------------------------------------------------
    # Formats MySQL TIME/timedelta values as HH:MM for the timetable.
    # ------------------------------------------------------------
    def _format_time(self, value):
        text = str(value)
        if len(text) >= 5:
            return text[:5]
        return text

    # ------------------------------------------------------------
    # Small dashboard card used for Department, Class, Batch and Strength.
    # ------------------------------------------------------------
    def _info_card(self, parent, title, value, column):
        card = tk.Frame(
            parent,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=16,
            pady=12,
        )
        card.grid(row=0, column=column, padx=6, sticky="nsew")
        parent.columnconfigure(column, weight=1)

        tk.Label(
            card,
            text=title.upper(),
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            card,
            text=value,
            bg=self.colors["card"],
            fg=self.colors["navy"],
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------
    # Renders the photo-inspired weekly timetable for one class.
    # ------------------------------------------------------------
    def _render_class_dashboard(self, parent, class_id):
        for widget in parent.winfo_children():
            widget.destroy()

        try:
            summary = repo.get_class_dashboard_summary(class_id)
            slots = repo.get_day_slots()
            timetable = repo.get_class_timetable(class_id)
            courses = repo.get_class_course_summary(class_id)
        except Exception as e:
            self.handle_error(e)
            return

        if not summary:
            tk.Label(parent, text="Class details not found.", bg=self.colors["bg"]).pack(pady=30)
            return

        # summary: class_id, department_code, department_name,
        # class_name, semester, section, strength, admission_year
        admission_year = summary[7]
        batch = f"{admission_year} - {int(admission_year) + 4}" if admission_year else "Not available"
        class_display = f"Sem {summary[4]} / {summary[3]} / {summary[5]}"

        cards = tk.Frame(parent, bg=self.colors["bg"])
        cards.pack(fill="x", pady=(0, 12))
        self._info_card(cards, "Department", f"{summary[1]} - {summary[2]}", 0)
        self._info_card(cards, "Class / Semester / Section", class_display, 1)
        self._info_card(cards, "Batch", batch, 2)
        self._info_card(cards, "Class Strength", str(summary[6]), 3)

        # Build a lookup: (DAY, PERIOD) -> subject/staff values.
        timetable_map = {}
        for row in timetable:
            day, period_no, _start, _end, subject_code, subject_name, teacher_code, teacher_name = row
            timetable_map[(day, period_no)] = {
                "subject_code": subject_code,
                "subject_name": subject_name,
                "teacher_code": teacher_code,
                "teacher_name": teacher_name,
            }

        table_card = tk.Frame(
            parent,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        table_card.pack(fill="x")

        tk.Label(
            table_card,
            text="WEEKLY CLASS TIMETABLE",
            bg=self.colors["card"],
            fg=self.colors["navy"],
            font=("Segoe UI", 12, "bold"),
        ).grid(row=0, column=0, columnspan=len(slots) + 1, sticky="w", pady=(0, 8))

        # Header: Day / Hour, P1, P2, Break, P3, P4, Lunch, P5, P6, Break, P7.
        headers = [("DAY / HOUR", None, "HEADER")]
        for _order, slot_type, slot_name, period_no, start, end in slots:
            if slot_type == "PERIOD":
                label = f"P{period_no}\n{self._format_time(start)}-{self._format_time(end)}"
            else:
                label = slot_name.upper()
            headers.append((label, period_no, slot_type))

        for col, (label, _pno, slot_type) in enumerate(headers):
            bg = self.colors["navy"]
            if slot_type == "BREAK":
                bg = "#A76B00"
            elif slot_type == "LUNCH":
                bg = "#3A7D44"
            cell = tk.Label(
                table_card,
                text=label,
                bg=bg,
                fg="white",
                font=("Segoe UI", 8, "bold"),
                relief="solid",
                bd=1,
                padx=5,
                pady=6,
                justify="center",
            )
            cell.grid(row=1, column=col, sticky="nsew")
            table_card.columnconfigure(col, weight=2 if col == 0 else 1)

        days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
        for r_index, day in enumerate(days, start=2):
            tk.Label(
                table_card,
                text=day.title(),
                bg="#E7ECF3",
                fg=self.colors["navy"],
                font=("Segoe UI", 9, "bold"),
                relief="solid",
                bd=1,
                padx=6,
                pady=11,
            ).grid(row=r_index, column=0, sticky="nsew")

            for c_index, (_order, slot_type, slot_name, period_no, _start, _end) in enumerate(slots, start=1):
                if slot_type == "BREAK":
                    text = "SHORT\nBREAK"
                    bg = self.colors["break"]
                    fg = "#875B00"
                elif slot_type == "LUNCH":
                    text = "LUNCH"
                    bg = self.colors["lunch"]
                    fg = "#2F6B39"
                else:
                    assignment = timetable_map.get((day, period_no))
                    if assignment:
                        text = f"{assignment['subject_name']}\n{assignment['teacher_name']}"
                    else:
                        text = "—"
                    bg = self.colors["period"] if r_index % 2 == 0 else "white"
                    fg = self.colors["text"]

                tk.Label(
                    table_card,
                    text=text,
                    bg=bg,
                    fg=fg,
                    font=("Segoe UI", 8, "bold" if slot_type != "PERIOD" else "normal"),
                    relief="solid",
                    bd=1,
                    padx=4,
                    pady=10,
                    justify="center",
                ).grid(row=r_index, column=c_index, sticky="nsew")

        # Course/teacher summary, similar to the lower table in the supplied reference.
        summary_card = tk.Frame(
            parent,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        summary_card.pack(fill="both", expand=True, pady=(12, 0))

        tk.Label(
            summary_card,
            text="COURSE HANDLING SUMMARY",
            bg=self.colors["card"],
            fg=self.colors["navy"],
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(0, 6))

        columns = ("code", "course", "staff", "hours")
        course_tree = ttk.Treeview(summary_card, columns=columns, show="headings", height=5)
        for key, heading, width in [
            ("code", "Course Code", 110),
            ("course", "Course Name", 320),
            ("staff", "Course Handling Staff", 240),
            ("hours", "Hours / Week", 100),
        ]:
            course_tree.heading(key, text=heading)
            course_tree.column(key, width=width, anchor="center")
        course_tree.pack(fill="both", expand=True)
        for row in courses:
            course_tree.insert("", "end", values=row)

    # ------------------------------------------------------------
    # Saves the currently displayed attendance-report rows as CSV.
    # CSV uses only Python's standard csv module.
    # ------------------------------------------------------------
    def _download_report_csv(self, tree):
        rows = [tree.item(item, "values") for item in tree.get_children()]
        if not rows:
            messagebox.showwarning("No Data", "There are no attendance rows to download.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Attendance Report as CSV",
            defaultextension=".csv",
            initialfile=f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            filetypes=[("CSV files", "*.csv")],
        )
        if not path:
            return

        headers = [tree.heading(col, "text") for col in tree["columns"]]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(headers)
                writer.writerows(rows)
            messagebox.showinfo("Downloaded", f"Attendance report saved successfully:\n{path}")
        except Exception as e:
            self.handle_error(e)

    # ------------------------------------------------------------
    # Saves the currently displayed attendance-report rows as a PDF.
    # reportlab is used because Tkinter itself cannot create PDF files.
    # ------------------------------------------------------------
    def _download_report_pdf(self, tree):
        rows = [tree.item(item, "values") for item in tree.get_children()]
        if not rows:
            messagebox.showwarning("No Data", "There are no attendance rows to download.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Attendance Report as PDF",
            defaultextension=".pdf",
            initialfile=f"attendance_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not path:
            return

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

            headers = [tree.heading(col, "text") for col in tree["columns"]]
            data = [headers] + [[str(value) for value in row] for row in rows]

            pdf = SimpleDocTemplate(
                path,
                pagesize=landscape(A4),
                rightMargin=22,
                leftMargin=22,
                topMargin=24,
                bottomMargin=24,
            )
            styles = getSampleStyleSheet()
            story = [
                Paragraph("Attendance Report", styles["Title"]),
                Paragraph(
                    f"Generated: {datetime.now().strftime('%d-%m-%Y %I:%M %p')} | Records: {len(rows)}",
                    styles["Normal"],
                ),
                Spacer(1, 10),
            ]

            col_widths = [34, 55, 90, 45, 55, 105, 90, 65, 52, 115]
            table = Table(data, repeatRows=1, colWidths=col_widths)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#102A43")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6.5),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#BCCCDC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FB")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
            pdf.build(story)
            messagebox.showinfo("Downloaded", f"PDF attendance report saved successfully:\n{path}")
        except ImportError:
            messagebox.showerror(
                "PDF Library Missing",
                "Install reportlab first:\n\npip install reportlab",
            )
        except Exception as e:
            self.handle_error(e)


    def clear_window(self):
        for w in self.winfo_children():
            w.destroy()


    # ------------------------------------------------------------
    # Deletes widgets only from the dashboard content area while keeping the sidebar visible.
    # ------------------------------------------------------------
    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()


    # ------------------------------------------------------------
    # Checks whether the logged-in role has the requested permission. Displays Access Denied when permission is missing.
    # ------------------------------------------------------------
    def require(self, permission):
        if not has_permission(self.current_user, permission):
            messagebox.showerror("Access Denied", "You do not have permission for this action.")
            return False
        return True


    # ------------------------------------------------------------
    # Converts common MySQL error numbers into messages that are easier for the user to understand.
    # ------------------------------------------------------------
    def handle_error(self, error):
        msg = str(error)
        if "1062" in msg:
            msg = "Duplicate value found. Check roll number, email, code or username."
        elif "1452" in msg:
            msg = "Foreign-key error. Check the selected related record."
        elif "1451" in msg:
            msg = "This record is already used by another table and cannot be deleted."
        elif "1045" in msg:
            msg = "MySQL login failed. Check username/password in config.py."
        elif "2003" in msg:
            msg = "Cannot connect to MySQL. Check WAMP and port 3306."
        messagebox.showerror("Error", msg)


    # ------------------------------------------------------------
    # Displays a page heading and optional subtitle in the dashboard content area.
    # ------------------------------------------------------------
    def title_text(self, title, subtitle=""):
        # Modern page title used by non-dashboard pages.
        wrapper = tk.Frame(self.content, bg=self.colors["bg"])
        wrapper.pack(fill="x", padx=20, pady=(18, 8))
        tk.Label(
            wrapper,
            text=title,
            bg=self.colors["bg"],
            fg=self.colors["navy"],
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                wrapper,
                text=subtitle,
                bg=self.colors["bg"],
                fg=self.colors["muted"],
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(2, 0))

    def tree(self, columns, headings, widths):
        # Reusable modern table with both scrollbars.
        holder = tk.Frame(self.content, bg=self.colors["bg"])
        holder.pack(fill="both", expand=True, padx=20, pady=10)

        tree = ttk.Treeview(holder, columns=columns, show="headings")
        y = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        x = ttk.Scrollbar(holder, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y.set, xscrollcommand=x.set)

        tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        holder.rowconfigure(0, weight=1)
        holder.columnconfigure(0, weight=1)

        for col, head, width in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=width, anchor="center")
        return tree

    def show_login(self):
        self.clear_window()
        self.current_user = None
        self.student_record = None
        self.teacher_record = None

        card = ttk.LabelFrame(self, text=" Attendance System Login ", padding=30)
        card.pack(expand=True)

        ttk.Label(card, text="Attendance Management System", font=("Segoe UI", 22, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )

        ttk.Label(card, text="Username").grid(row=1, column=0, sticky="w", pady=8)
        username = ttk.Entry(card, width=35)
        username.grid(row=1, column=1, pady=8)

        ttk.Label(card, text="Password").grid(row=2, column=0, sticky="w", pady=8)
        password = ttk.Entry(card, width=35, show="*")
        password.grid(row=2, column=1, pady=8)


        # ------------------------------------------------------------
        # Nested Login button action: reads username/password, authenticates, stores the logged-in user, and opens Dashboard.
        # ------------------------------------------------------------
        def login(event=None):
            try:
                user = authenticate(username.get().strip(), password.get())
                if not user:
                    messagebox.showerror("Login Failed", "Invalid username or password.")
                    return

                self.current_user = user
                if user["role"] == "student":
                    self.student_record = find_student_for_login(user["username"])
                elif user["role"] == "teacher":
                    self.teacher_record = find_teacher_for_login(user["username"])

                self.dashboard()
            except Exception as e:
                self.handle_error(e)

        ttk.Button(card, text="Login", command=login, width=20).grid(
            row=3, column=0, columnspan=2, pady=10
        )
        ttk.Button(card, text="Test Database Connection", command=self.test_db).grid(
            row=4, column=0, columnspan=2
        )
        username.focus()
        self.bind("<Return>", login)


    # ------------------------------------------------------------
    # Tests the MySQL connection using the settings in config.py.
    # ------------------------------------------------------------
    def test_db(self):
        ok, msg = test_connection()
        (messagebox.showinfo if ok else messagebox.showerror)("Database", msg)

    # ---------------- Dashboard ----------------

    # ------------------------------------------------------------
    # Creates the sidebar and shows different menu options for Admin, Teacher, and Student roles.
    # ------------------------------------------------------------
    def dashboard(self):
        # Builds a dark header/sidebar and a light working area.
        self.clear_window()
        self.unbind("<Return>")
        self.configure(bg=self.colors["bg"])

        top = tk.Frame(self, bg=self.colors["navy"], height=66)
        top.pack(fill="x")
        top.pack_propagate(False)

        brand = tk.Frame(top, bg=self.colors["navy"])
        brand.pack(side="left", padx=22)
        tk.Label(
            brand,
            text="ATTENDANCE MANAGEMENT SYSTEM",
            bg=self.colors["navy"],
            fg="white",
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", pady=(12, 0))
        tk.Label(
            brand,
            text="Period-based timetable & attendance portal",
            bg=self.colors["navy"],
            fg="#BCCCDC",
            font=("Segoe UI", 8),
        ).pack(anchor="w")

        ttk.Button(top, text="Logout", command=self.show_login, style="Primary.TButton").pack(
            side="right", padx=(8, 20), pady=16
        )
        tk.Label(
            top,
            text=f"{self.current_user['username']}  •  {self.current_user['role'].title()}",
            bg=self.colors["navy"],
            fg="white",
            font=("Segoe UI", 10, "bold"),
        ).pack(side="right", padx=10)

        body = tk.Frame(self, bg=self.colors["bg"])
        body.pack(fill="both", expand=True)

        side = tk.Frame(body, bg=self.colors["sidebar"], width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        tk.Label(
            side,
            text="MENU",
            bg=self.colors["sidebar"],
            fg="#829AB1",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=18, pady=(22, 8))

        self.content = tk.Frame(body, bg=self.colors["bg"])
        self.content.pack(side="right", fill="both", expand=True)

        role = self.current_user["role"]
        if role == "admin":
            menu = [
                ("Dashboard", self.home),
                ("Students", self.students_page),
                ("Teachers", self.teachers_page),
                ("Subjects", self.subjects_page),
                ("Timetable", self.timetable_page),
                ("Mark Attendance", self.mark_attendance_page),
                ("Attendance Report", self.attendance_report_page),
                ("Attendance %", self.percentage_page),
                ("Users", self.users_page),
            ]
        elif role == "teacher":
            menu = [
                ("Dashboard", self.home),
                ("View Students", self.students_page),
                ("View Subjects", self.subjects_page),
                ("Timetable", self.timetable_page),
                ("Mark Attendance", self.mark_attendance_page),
                ("Attendance Report", self.attendance_report_page),
                ("Attendance %", self.percentage_page),
            ]
        else:
            menu = [
                ("Dashboard", self.home),
                ("My Profile", self.my_profile_page),
                ("My Timetable", self.my_timetable_page),
                ("My Attendance", self.my_attendance_page),
                ("My Attendance %", self.my_percentage_page),
            ]

        for text, command in menu:
            ttk.Button(side, text=text, command=command, style="Sidebar.TButton").pack(
                fill="x", padx=8, pady=2
            )

        tk.Label(
            side,
            text="7 Periods\nBreak after P2 • Lunch after P4\nBreak after P6",
            bg=self.colors["sidebar"],
            fg="#9FB3C8",
            justify="left",
            font=("Segoe UI", 8),
        ).pack(side="bottom", anchor="w", padx=18, pady=18)

        self.home()

    def home(self):
        # Dashboard inspired by the supplied class-timetable reference image.
        self.clear_content()

        header = tk.Frame(self.content, bg=self.colors["bg"])
        header.pack(fill="x", padx=22, pady=(18, 8))

        left = tk.Frame(header, bg=self.colors["bg"])
        left.pack(side="left")
        tk.Label(
            left,
            text="Class Timetable Dashboard",
            bg=self.colors["bg"],
            fg=self.colors["navy"],
            font=("Segoe UI", 21, "bold"),
        ).pack(anchor="w")
        tk.Label(
            left,
            text="Weekly timetable, staff allocation and class information in one view",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        dashboard_body = tk.Frame(self.content, bg=self.colors["bg"])
        dashboard_body.pack(fill="both", expand=True, padx=22, pady=(0, 18))

        try:
            classes = repo.get_classes()
        except Exception as e:
            self.handle_error(e)
            return

        # Students automatically see their own class.
        if self.current_user["role"] == "student":
            if not self.ensure_student():
                return
            class_id = self.student_record[7]
            tk.Label(
                header,
                text=f"My Class ID: {class_id}",
                bg=self.colors["card"],
                fg=self.colors["navy"],
                padx=12,
                pady=7,
                font=("Segoe UI", 9, "bold"),
            ).pack(side="right", padx=4)
            self._render_class_dashboard(dashboard_body, class_id)
            return

        # Admin/Teacher can choose which class timetable should be shown.
        class_map = {}
        for c in classes:
            # c = class_id, class_name, semester, section, department_id, department_code
            label = f"{c[5]} | Sem {c[2]} | {c[1]}-{c[3]}"
            class_map[label] = c[0]

        selector_box = tk.Frame(header, bg=self.colors["bg"])
        selector_box.pack(side="right")
        tk.Label(
            selector_box,
            text="View Class",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        class_combo = ttk.Combobox(selector_box, values=list(class_map), state="readonly", width=30)
        class_combo.pack(pady=(2, 0))

        def refresh_dashboard(event=None):
            if class_combo.get():
                self._render_class_dashboard(dashboard_body, class_map[class_combo.get()])

        class_combo.bind("<<ComboboxSelected>>", refresh_dashboard)
        if class_map:
            first = next(iter(class_map))
            class_combo.set(first)
            refresh_dashboard()

    def day_structure(self):
        box = tk.Frame(
            self.content,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=14,
            pady=12,
        )
        box.pack(fill="x", padx=20, pady=(0, 10))

        heading = tk.Frame(box, bg=self.colors["card"])
        heading.pack(fill="x", pady=(0, 10))
        tk.Label(
            heading,
            text="DAILY STRUCTURE",
            bg=self.colors["card"],
            fg=self.colors["navy"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        tk.Label(
            heading,
            text="7 teaching periods  •  breaks and lunch are not attendance periods",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 8),
        ).pack(side="right")

        timeline = tk.Frame(box, bg=self.colors["card"])
        timeline.pack(fill="x")
        try:
            for _, typ, name, pno, start, end in repo.get_day_slots():
                if typ == "PERIOD":
                    title = f"P{pno}"
                    detail = "Teaching period"
                    bg = self.colors["period"]
                    fg = self.colors["navy"]
                    accent = self.colors["accent"]
                else:
                    title = name.title()
                    detail = "No attendance"
                    bg = self.colors["lunch"] if typ == "LUNCH" else self.colors["break"]
                    fg = "#2F6B39" if typ == "LUNCH" else "#875B00"
                    accent = fg

                card = tk.Frame(
                    timeline,
                    bg=bg,
                    highlightbackground=accent,
                    highlightthickness=1,
                    padx=8,
                    pady=7,
                )
                card.pack(side="left", fill="x", expand=True, padx=(0, 5))
                tk.Label(
                    card,
                    text=title,
                    bg=bg,
                    fg=fg,
                    font=("Segoe UI", 9, "bold"),
                ).pack(anchor="w")
                tk.Label(
                    card,
                    text=f"{self._format_time(start)} - {self._format_time(end)}",
                    bg=bg,
                    fg=self.colors["text"],
                    font=("Segoe UI", 8, "bold"),
                ).pack(anchor="w", pady=(2, 0))
                tk.Label(
                    card,
                    text=detail,
                    bg=bg,
                    fg=fg,
                    font=("Segoe UI", 7),
                ).pack(anchor="w", pady=(2, 0))
        except Exception as e:
            self.handle_error(e)

    # ---------------- Students ----------------

    # ------------------------------------------------------------
    # Displays all students. Admin gets Add/Delete buttons; Teacher gets view-only access.
    # ------------------------------------------------------------
    def students_page(self):
        if not self.require("view_students"):
            return
        self.clear_content()
        self.title_text("Students", "Teacher = view only, Admin = add/delete")

        bar = ttk.Frame(self.content)
        bar.pack(fill="x", padx=15)
        if has_permission(self.current_user, "manage_students"):
            ttk.Button(bar, text="Add Student", command=self.add_student_form).pack(side="left", padx=4)
            ttk.Button(bar, text="Delete Selected", command=self.delete_student).pack(side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self.students_page).pack(side="left", padx=4)

        self.student_tree = self.tree(
            ("id","roll","name","email","phone","gender","dept","class","year"),
            ("ID","Roll No","Student Name","Email","Phone","Gender","Dept","Class","Admission"),
            (55,90,150,180,110,80,70,90,80),
        )
        try:
            for row in repo.get_students():
                self.student_tree.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)


    # ------------------------------------------------------------
    # Opens the Student entry form and inserts the entered student through repository.py.
    # ------------------------------------------------------------
    def add_student_form(self):
        if not self.require("manage_students"):
            return
        win = tk.Toplevel(self)
        win.title("Add Student")
        win.geometry("500x520")
        win.grab_set()
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)

        entries = {}
        for i, label in enumerate(["Roll No","Student Name","Email","Phone","Admission Year"]):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky="w", pady=7)
            e = ttk.Entry(f, width=32)
            e.grid(row=i, column=1, pady=7)
            entries[label] = e
        entries["Admission Year"].insert(0, str(datetime.now().year))

        ttk.Label(f, text="Gender").grid(row=5, column=0, sticky="w", pady=7)
        gender = ttk.Combobox(f, values=["Male","Female","Other"], state="readonly", width=29)
        gender.grid(row=5, column=1, pady=7)
        gender.set("Male")

        try:
            departments = repo.get_departments()
            classes = repo.get_classes()
        except Exception as e:
            self.handle_error(e)
            win.destroy()
            return

        dept_map = {f"{d[1]} - {d[2]}": d[0] for d in departments}
        ttk.Label(f, text="Department").grid(row=6, column=0, sticky="w", pady=7)
        dept = ttk.Combobox(f, values=list(dept_map), state="readonly", width=29)
        dept.grid(row=6, column=1, pady=7)

        ttk.Label(f, text="Class").grid(row=7, column=0, sticky="w", pady=7)
        cls = ttk.Combobox(f, state="readonly", width=29)
        cls.grid(row=7, column=1, pady=7)
        class_map = {}


        # ------------------------------------------------------------
        # Performs the load classes operation.
        # ------------------------------------------------------------
        def load_classes(event=None):
            class_map.clear()
            dep_id = dept_map.get(dept.get())
            for c in classes:
                if c[4] == dep_id:
                    label = f"{c[5]} | Sem {c[2]} | {c[1]}-{c[3]}"
                    class_map[label] = c[0]
            cls["values"] = list(class_map)
            cls.set("")

        dept.bind("<<ComboboxSelected>>", load_classes)


        # ------------------------------------------------------------
        # Validates the current popup form and saves its data through repository.py.
        # ------------------------------------------------------------
        def save():
            try:
                repo.add_student({
                    "roll_no": entries["Roll No"].get().strip(),
                    "student_name": entries["Student Name"].get().strip(),
                    "email": entries["Email"].get().strip(),
                    "phone": entries["Phone"].get().strip(),
                    "gender": gender.get(),
                    "department_id": dept_map[dept.get()],
                    "class_id": class_map[cls.get()],
                    "admission_year": int(entries["Admission Year"].get()),
                })
                messagebox.showinfo("Success", "Student added.", parent=win)
                win.destroy()
                self.students_page()
            except Exception as e:
                self.handle_error(e)

        ttk.Button(f, text="Save Student", command=save).grid(row=8, column=0, columnspan=2, pady=20)


    # ------------------------------------------------------------
    # Deletes the selected Student unless MySQL blocks deletion because related attendance exists.
    # ------------------------------------------------------------
    def delete_student(self):
        if not self.require("manage_students"):
            return
        sel = self.student_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a student first.")
            return
        row = self.student_tree.item(sel[0], "values")
        if messagebox.askyesno("Confirm", f"Delete {row[2]}?"):
            try:
                repo.delete_student(row[0])
                self.students_page()
            except Exception as e:
                self.handle_error(e)

    # ---------------- Teachers ----------------

    # ------------------------------------------------------------
    # Displays the Teacher master table.
    # ------------------------------------------------------------
    def teachers_page(self):
        if not self.require("view_teachers"):
            return
        self.clear_content()
        self.title_text("Teachers")
        bar = ttk.Frame(self.content)
        bar.pack(fill="x", padx=15)
        ttk.Button(bar, text="Add Teacher", command=self.add_teacher_form).pack(side="left", padx=4)
        ttk.Button(bar, text="Delete Selected", command=self.delete_teacher).pack(side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self.teachers_page).pack(side="left", padx=4)

        self.teacher_tree = self.tree(
            ("id","code","name","email","phone","dept","designation"),
            ("ID","Code","Teacher Name","Email","Phone","Dept","Designation"),
            (55,80,150,180,110,70,150),
        )
        try:
            for row in repo.get_teachers():
                self.teacher_tree.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)


    # ------------------------------------------------------------
    # Opens the Teacher entry form and inserts a new teacher.
    # ------------------------------------------------------------
    def add_teacher_form(self):
        if not self.require("manage_teachers"):
            return
        win = tk.Toplevel(self)
        win.title("Add Teacher")
        win.geometry("480x430")
        win.grab_set()
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)

        entries = {}
        for i, label in enumerate(["Teacher Code","Teacher Name","Email","Phone","Designation"]):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky="w", pady=7)
            e = ttk.Entry(f, width=32)
            e.grid(row=i, column=1, pady=7)
            entries[label] = e

        deps = repo.get_departments()
        dep_map = {f"{d[1]} - {d[2]}": d[0] for d in deps}
        ttk.Label(f, text="Department").grid(row=5, column=0, sticky="w", pady=7)
        dep = ttk.Combobox(f, values=list(dep_map), state="readonly", width=29)
        dep.grid(row=5, column=1, pady=7)


        # ------------------------------------------------------------
        # Validates the current popup form and saves its data through repository.py.
        # ------------------------------------------------------------
        def save():
            try:
                repo.add_teacher({
                    "teacher_code": entries["Teacher Code"].get().strip(),
                    "teacher_name": entries["Teacher Name"].get().strip(),
                    "email": entries["Email"].get().strip(),
                    "phone": entries["Phone"].get().strip(),
                    "department_id": dep_map[dep.get()],
                    "designation": entries["Designation"].get().strip(),
                })
                messagebox.showinfo("Success", "Teacher added.", parent=win)
                win.destroy()
                self.teachers_page()
            except Exception as e:
                self.handle_error(e)

        ttk.Button(f, text="Save Teacher", command=save).grid(row=6, column=0, columnspan=2, pady=20)


    # ------------------------------------------------------------
    # Deletes the selected Teacher when no dependent records prevent deletion.
    # ------------------------------------------------------------
    def delete_teacher(self):
        if not self.require("manage_teachers"):
            return
        sel = self.teacher_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a teacher first.")
            return
        row = self.teacher_tree.item(sel[0], "values")
        if messagebox.askyesno("Confirm", f"Delete {row[2]}?"):
            try:
                repo.delete_teacher(row[0])
                self.teachers_page()
            except Exception as e:
                self.handle_error(e)

    # ---------------- Subjects ----------------

    # ------------------------------------------------------------
    # Displays Subjects. Admin can modify; Teacher can only view.
    # ------------------------------------------------------------
    def subjects_page(self):
        if not self.require("view_subjects"):
            return
        self.clear_content()
        self.title_text("Subjects")
        bar = ttk.Frame(self.content)
        bar.pack(fill="x", padx=15)
        if has_permission(self.current_user, "manage_subjects"):
            ttk.Button(bar, text="Add Subject", command=self.add_subject_form).pack(side="left", padx=4)
            ttk.Button(bar, text="Delete Selected", command=self.delete_subject).pack(side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self.subjects_page).pack(side="left", padx=4)

        self.subject_tree = self.tree(
            ("id","code","name","semester","dept"),
            ("ID","Code","Subject Name","Semester","Department"),
            (60,100,240,100,110),
        )
        try:
            for row in repo.get_subjects():
                self.subject_tree.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)


    # ------------------------------------------------------------
    # Opens the Subject entry form and inserts a new subject.
    # ------------------------------------------------------------
    def add_subject_form(self):
        if not self.require("manage_subjects"):
            return
        win = tk.Toplevel(self)
        win.title("Add Subject")
        win.geometry("460x350")
        win.grab_set()
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)

        labels = ["Subject Code", "Subject Name", "Semester"]
        entries = {}
        for i, label in enumerate(labels):
            ttk.Label(f, text=label).grid(row=i, column=0, sticky="w", pady=7)
            e = ttk.Entry(f, width=32)
            e.grid(row=i, column=1, pady=7)
            entries[label] = e

        deps = repo.get_departments()
        dep_map = {f"{d[1]} - {d[2]}": d[0] for d in deps}
        ttk.Label(f, text="Department").grid(row=3, column=0, sticky="w", pady=7)
        dep = ttk.Combobox(f, values=list(dep_map), state="readonly", width=29)
        dep.grid(row=3, column=1, pady=7)


        # ------------------------------------------------------------
        # Validates the current popup form and saves its data through repository.py.
        # ------------------------------------------------------------
        def save():
            try:
                repo.add_subject({
                    "subject_code": entries["Subject Code"].get().strip(),
                    "subject_name": entries["Subject Name"].get().strip(),
                    "semester": int(entries["Semester"].get()),
                    "department_id": dep_map[dep.get()],
                })
                messagebox.showinfo("Success", "Subject added.", parent=win)
                win.destroy()
                self.subjects_page()
            except Exception as e:
                self.handle_error(e)

        ttk.Button(f, text="Save Subject", command=save).grid(row=4, column=0, columnspan=2, pady=20)


    # ------------------------------------------------------------
    # Deletes the selected Subject when it is not referenced by timetable or attendance.
    # ------------------------------------------------------------
    def delete_subject(self):
        if not self.require("manage_subjects"):
            return
        sel = self.subject_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a subject first.")
            return
        row = self.subject_tree.item(sel[0], "values")
        if messagebox.askyesno("Confirm", f"Delete {row[2]}?"):
            try:
                repo.delete_subject(row[0])
                self.subjects_page()
            except Exception as e:
                self.handle_error(e)

    # ---------------- Timetable ----------------

    # ------------------------------------------------------------
    # Displays the full weekly Class/Period/Subject/Teacher timetable.
    # ------------------------------------------------------------
    def timetable_page(self):
        if not self.require("view_timetable"):
            return
        self.clear_content()
        self.title_text("Weekly Period Timetable", "Break and lunch are not attendance periods.")
        self.day_structure()
        t = self.tree(
            ("dept","class","day","period","start","end","code","subject","teacher"),
            ("Dept","Class","Day","Period","Start","End","Code","Subject","Teacher"),
            (70,80,100,70,80,80,80,180,150),
        )
        try:
            for row in repo.get_all_timetables():
                row = list(row)
                row[3] = f"P{row[3]}"
                t.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)


    # ------------------------------------------------------------
    # Displays only the timetable of the logged-in Student's class.
    # ------------------------------------------------------------
    def my_timetable_page(self):
        if not self.require("view_own_timetable") or not self.ensure_student():
            return
        self.clear_content()
        self.title_text("My Weekly Timetable")
        self.day_structure()
        t = self.tree(
            ("day","period","start","end","code","subject","staffcode","teacher"),
            ("Day","Period","Start","End","Code","Subject","Staff Code","Teacher"),
            (100,70,80,80,80,180,90,150),
        )
        try:
            for row in repo.get_class_timetable(self.student_record[7]):
                row = list(row)
                row[1] = f"P{row[1]}"
                t.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)

    # ---------------- Period Attendance ----------------

    # ------------------------------------------------------------
    # Period attendance form. Student + Date + Period determine the scheduled Subject and Teacher automatically.
    # ------------------------------------------------------------
    def mark_attendance_page(self):
        if not self.require("mark_attendance"):
            return
        self.clear_content()
        self.title_text(
            "Mark Period Attendance",
            "Choose Student + Date + P1-P7. Subject and teacher load automatically from timetable.",
        )
        self.day_structure()

        box = ttk.LabelFrame(self.content, text=" Period Attendance ", padding=20)
        box.pack(anchor="nw", fill="x", padx=20, pady=12)

        try:
            students = repo.get_student_choices()
            periods = repo.get_periods()
        except Exception as e:
            self.handle_error(e)
            return

        student_map = {
            f"{s[1]} - {s[2]}": {"student_id": s[0], "class_id": s[3]}
            for s in students
        }
        period_map = {
            f"P{p[0]} | {p[2]}-{p[3]}": p[0]
            for p in periods
        }

        ttk.Label(box, text="Student").grid(row=0, column=0, sticky="w", pady=7)
        student = ttk.Combobox(box, values=list(student_map), state="readonly", width=42)
        student.grid(row=0, column=1, pady=7)

        ttk.Label(box, text="Date").grid(row=1, column=0, sticky="w", pady=7)
        date_entry = ttk.Entry(box, width=45)
        date_entry.grid(row=1, column=1, pady=7)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ttk.Label(box, text="Period").grid(row=2, column=0, sticky="w", pady=7)
        period = ttk.Combobox(box, values=list(period_map), state="readonly", width=42)
        period.grid(row=2, column=1, pady=7)

        subject_var = tk.StringVar()
        teacher_var = tk.StringVar()
        ttk.Label(box, text="Subject").grid(row=3, column=0, sticky="w", pady=7)
        ttk.Entry(box, textvariable=subject_var, state="readonly", width=45).grid(row=3, column=1, pady=7)
        ttk.Label(box, text="Teacher").grid(row=4, column=0, sticky="w", pady=7)
        ttk.Entry(box, textvariable=teacher_var, state="readonly", width=45).grid(row=4, column=1, pady=7)

        ttk.Label(box, text="Status").grid(row=5, column=0, sticky="w", pady=7)
        status = ttk.Combobox(box, values=["Present","Absent","Late","Leave"], state="readonly", width=42)
        status.grid(row=5, column=1, pady=7)
        status.set("Present")

        ttk.Label(box, text="Remarks").grid(row=6, column=0, sticky="w", pady=7)
        remarks = ttk.Entry(box, width=45)
        remarks.grid(row=6, column=1, pady=7)

        assignment = {}


        # ------------------------------------------------------------
        # Uses Date->Weekday, Student Class and Period to look up the scheduled Subject/Teacher from period_timetable.
        # ------------------------------------------------------------
        def load_assignment(event=None):
            assignment.clear()
            subject_var.set("")
            teacher_var.set("")
            if not student.get() or not period.get():
                return
            try:
                parsed = datetime.strptime(date_entry.get().strip(), "%Y-%m-%d")
            except ValueError:
                return

            info = student_map[student.get()]
            day = parsed.strftime("%A").upper()
            pno = period_map[period.get()]
            try:
                row = repo.get_period_assignment(info["class_id"], day, pno)
                if not row:
                    subject_var.set("No class scheduled")
                    teacher_var.set("No class scheduled")
                    return
                assignment.update({"subject_id": row[0], "teacher_id": row[3]})
                subject_var.set(f"{row[1]} - {row[2]}")
                teacher_var.set(f"{row[4]} - {row[5]}")
            except Exception as e:
                self.handle_error(e)

        student.bind("<<ComboboxSelected>>", load_assignment)
        period.bind("<<ComboboxSelected>>", load_assignment)
        date_entry.bind("<FocusOut>", load_assignment)
        ttk.Button(box, text="Load Scheduled Subject / Teacher", command=load_assignment).grid(
            row=7, column=0, columnspan=2, pady=(8,4)
        )


        # ------------------------------------------------------------
        # Validates the current popup form and saves its data through repository.py.
        # ------------------------------------------------------------
        def save():
            try:
                datetime.strptime(date_entry.get().strip(), "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.")
                return

            if not student.get() or not period.get():
                messagebox.showwarning("Required", "Select Student and Period.")
                return

            load_assignment()
            if not assignment:
                messagebox.showerror(
                    "No Timetable",
                    "No class is scheduled for this date/period. Break and lunch cannot have attendance.",
                )
                return

            if self.current_user["role"] == "teacher":
                if not self.teacher_record:
                    messagebox.showerror("Teacher Link Missing", "Teacher login could not be linked to teacher record.")
                    return
                if assignment["teacher_id"] != self.teacher_record[0]:
                    messagebox.showerror("Access Denied", "This period belongs to another teacher.")
                    return

            try:
                info = student_map[student.get()]
                repo.mark_attendance({
                    "student_id": info["student_id"],
                    "subject_id": assignment["subject_id"],
                    "teacher_id": assignment["teacher_id"],
                    "attendance_date": date_entry.get().strip(),
                    "period_no": period_map[period.get()],
                    "status": status.get(),
                    "remarks": remarks.get().strip(),
                })
                messagebox.showinfo("Success", "Period attendance marked successfully.")
                student.set("")
                subject_var.set("")
                teacher_var.set("")
                remarks.delete(0, "end")
                assignment.clear()
            except Exception as e:
                self.handle_error(e)

        ttk.Button(box, text="Save Period Attendance", command=save).grid(
            row=8, column=0, columnspan=2, pady=15
        )

    # ---------------- Reports ----------------

    # ------------------------------------------------------------
    # Displays all period-based attendance records in a table.
    # ------------------------------------------------------------
    def attendance_report_page(self):
        # Attendance report with filters plus CSV/PDF download buttons.
        if not self.require("view_all_attendance"):
            return

        self.clear_content()
        self.title_text(
            "Attendance Report",
            "Filter the report on screen, then download exactly the visible rows as CSV or PDF.",
        )

        filters = tk.Frame(
            self.content,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        filters.pack(fill="x", padx=20, pady=(0, 6))

        tk.Label(filters, text="Student / Roll No", bg=self.colors["card"], fg=self.colors["muted"]).grid(row=0, column=0, sticky="w")
        search_entry = ttk.Entry(filters, width=24)
        search_entry.grid(row=1, column=0, padx=(0, 8), pady=(2, 0))

        tk.Label(filters, text="From Date", bg=self.colors["card"], fg=self.colors["muted"]).grid(row=0, column=1, sticky="w")
        from_entry = ttk.Entry(filters, width=14)
        from_entry.grid(row=1, column=1, padx=(0, 8), pady=(2, 0))

        tk.Label(filters, text="To Date", bg=self.colors["card"], fg=self.colors["muted"]).grid(row=0, column=2, sticky="w")
        to_entry = ttk.Entry(filters, width=14)
        to_entry.grid(row=1, column=2, padx=(0, 8), pady=(2, 0))

        tk.Label(filters, text="Status", bg=self.colors["card"], fg=self.colors["muted"]).grid(row=0, column=3, sticky="w")
        status_combo = ttk.Combobox(
            filters,
            values=["All", "Present", "Absent", "Late", "Leave"],
            state="readonly",
            width=12,
        )
        status_combo.grid(row=1, column=3, padx=(0, 10), pady=(2, 0))
        status_combo.set("All")

        count_var = tk.StringVar(value="0 records")
        tk.Label(
            filters,
            textvariable=count_var,
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=1, column=8, padx=(12, 0))

        # Build report table before wiring button commands.
        t = self.tree(
            ("id","roll","student","period","scode","subject","teacher","date","status","remarks"),
            ("ID","Roll No","Student","Period","Sub Code","Subject","Teacher","Date","Status","Remarks"),
            (55,85,140,70,80,170,140,100,80,180),
        )

        def validate_date(value, label):
            if not value:
                return True
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return True
            except ValueError:
                messagebox.showerror("Invalid Date", f"{label} must use YYYY-MM-DD format.")
                return False

        def load_report():
            if not validate_date(from_entry.get().strip(), "From Date"):
                return
            if not validate_date(to_entry.get().strip(), "To Date"):
                return

            for item in t.get_children():
                t.delete(item)

            try:
                rows = repo.get_attendance_report(
                    student_search=search_entry.get().strip(),
                    date_from=from_entry.get().strip(),
                    date_to=to_entry.get().strip(),
                    status=status_combo.get(),
                )
                for row in rows:
                    t.insert("", "end", values=row)
                count_var.set(f"{len(rows)} records")
            except Exception as e:
                self.handle_error(e)

        def reset_filters():
            search_entry.delete(0, "end")
            from_entry.delete(0, "end")
            to_entry.delete(0, "end")
            status_combo.set("All")
            load_report()

        ttk.Button(filters, text="Apply Filters", command=load_report, style="Primary.TButton").grid(row=1, column=4, padx=4)
        ttk.Button(filters, text="Reset", command=reset_filters, style="Secondary.TButton").grid(row=1, column=5, padx=4)
        ttk.Button(filters, text="Download CSV", command=lambda: self._download_report_csv(t), style="Secondary.TButton").grid(row=1, column=6, padx=4)
        ttk.Button(filters, text="Download PDF", command=lambda: self._download_report_pdf(t), style="Primary.TButton").grid(row=1, column=7, padx=4)

        load_report()

    def percentage_page(self):
        if not self.require("view_all_percentage"):
            return
        self.clear_content()
        self.title_text("Attendance Percentage", "Every teaching period counts as one attendance unit.")
        t = self.tree(
            ("roll","name","total","attended","percentage"),
            ("Roll No","Student","Total Periods","Attended","Percentage"),
            (100,180,120,120,120),
        )
        try:
            for row in repo.get_all_percentages():
                row = list(row)
                row[4] = f"{row[4]}%"
                t.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)

    # ---------------- Student own pages ----------------

    # ------------------------------------------------------------
    # Checks that a Student login is linked to an actual student master record.
    # ------------------------------------------------------------
    def ensure_student(self):
        if not self.student_record:
            messagebox.showerror("Student Link Missing", "Student username should match the Roll No.")
            return False
        return True


    # ------------------------------------------------------------
    # Displays only the logged-in Student's profile.
    # ------------------------------------------------------------
    def my_profile_page(self):
        if not self.require("view_own_profile") or not self.ensure_student():
            return
        self.clear_content()
        self.title_text("My Profile")
        r = self.student_record
        fields = [
            ("Student ID", r[0]), ("Roll No", r[1]), ("Name", r[2]),
            ("Email", r[3] or ""), ("Phone", r[4] or ""), ("Gender", r[5] or ""),
            ("Department ID", r[6]), ("Class ID", r[7]), ("Admission Year", r[8]),
        ]
        box = ttk.LabelFrame(self.content, text=" Student Details ", padding=20)
        box.pack(anchor="nw", padx=20, pady=20)
        for i, (label, value) in enumerate(fields):
            ttk.Label(box, text=f"{label}:", font=("Segoe UI", 10, "bold")).grid(row=i, column=0, sticky="w", padx=(0,25), pady=6)
            ttk.Label(box, text=str(value)).grid(row=i, column=1, sticky="w", pady=6)


    # ------------------------------------------------------------
    # Displays only the logged-in Student's attendance records.
    # ------------------------------------------------------------
    def my_attendance_page(self):
        if not self.require("view_own_attendance") or not self.ensure_student():
            return
        self.clear_content()
        self.title_text("My Attendance")
        t = self.tree(
            ("id","period","scode","subject","teacher","date","status","remarks"),
            ("ID","Period","Subject Code","Subject","Teacher","Date","Status","Remarks"),
            (60,70,100,180,150,100,90,200),
        )
        try:
            for row in repo.get_student_attendance(self.student_record[0]):
                t.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)


    # ------------------------------------------------------------
    # Displays subject-wise percentage only for the logged-in Student.
    # ------------------------------------------------------------
    def my_percentage_page(self):
        if not self.require("view_own_percentage") or not self.ensure_student():
            return
        self.clear_content()
        self.title_text("My Attendance Percentage")
        t = self.tree(
            ("code","subject","total","attended","percentage"),
            ("Subject Code","Subject","Total Periods","Attended","Percentage"),
            (110,230,120,120,120),
        )
        try:
            for row in repo.get_student_percentage(self.student_record[0]):
                row = list(row)
                row[4] = f"{row[4]}%"
                t.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)

    # ---------------- User Management ----------------

    # ------------------------------------------------------------
    # Admin-only screen showing login users and roles.
    # ------------------------------------------------------------
    def users_page(self):
        if not self.require("manage_users"):
            return
        self.clear_content()
        self.title_text("Login Users", "Student username = Roll No; teacher username = code/email name.")
        bar = ttk.Frame(self.content)
        bar.pack(fill="x", padx=15)
        ttk.Button(bar, text="Add User", command=self.add_user_form).pack(side="left", padx=4)
        ttk.Button(bar, text="Delete Selected", command=self.delete_user).pack(side="left", padx=4)
        ttk.Button(bar, text="Refresh", command=self.users_page).pack(side="left", padx=4)
        self.user_tree = self.tree(("id","username","role"), ("ID","Username","Role"), (70,200,130))
        try:
            for row in repo.get_users():
                self.user_tree.insert("", "end", values=row)
        except Exception as e:
            self.handle_error(e)


    # ------------------------------------------------------------
    # Admin-only form for creating Admin, Teacher, or Student login users.
    # ------------------------------------------------------------
    def add_user_form(self):
        if not self.require("manage_users"):
            return
        win = tk.Toplevel(self)
        win.title("Add User")
        win.geometry("430x300")
        win.grab_set()
        f = ttk.Frame(win, padding=20)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text="Username").grid(row=0, column=0, sticky="w", pady=8)
        username = ttk.Entry(f, width=30)
        username.grid(row=0, column=1, pady=8)
        ttk.Label(f, text="Password").grid(row=1, column=0, sticky="w", pady=8)
        password = ttk.Entry(f, width=30, show="*")
        password.grid(row=1, column=1, pady=8)
        ttk.Label(f, text="Role").grid(row=2, column=0, sticky="w", pady=8)
        role = ttk.Combobox(f, values=["Admin","Teacher","Student"], state="readonly", width=27)
        role.grid(row=2, column=1, pady=8)


        # ------------------------------------------------------------
        # Validates the current popup form and saves its data through repository.py.
        # ------------------------------------------------------------
        def save():
            try:
                repo.add_user(username.get().strip(), password.get(), role.get())
                messagebox.showinfo("Success", "User added.", parent=win)
                win.destroy()
                self.users_page()
            except Exception as e:
                self.handle_error(e)

        ttk.Button(f, text="Save User", command=save).grid(row=3, column=0, columnspan=2, pady=20)


    # ------------------------------------------------------------
    # Deletes a login user. Current logged-in Admin should not delete their own account.
    # ------------------------------------------------------------
    def delete_user(self):
        if not self.require("manage_users"):
            return
        sel = self.user_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a user first.")
            return
        row = self.user_tree.item(sel[0], "values")
        if str(row[0]) == str(self.current_user["user_id"]):
            messagebox.showwarning("Not Allowed", "You cannot delete your current login.")
            return
        if messagebox.askyesno("Confirm", f"Delete user {row[1]}?"):
            try:
                repo.delete_user(row[0])
                self.users_page()
            except Exception as e:
                self.handle_error(e)
