import tkinter as tk
import customtkinter as ctk
import json
import os
import time
import threading
import platform
import subprocess
import datetime

from tkinter import filedialog, messagebox
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas



# Set appearance and theme
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Global variables
current_user = None
notification_threads = []
DARK_COLOR = "#1a1a2e"
ACCENT_COLOR = "#16213e"
HIGHLIGHT_COLOR = "#0f3460"
TEXT_COLOR = "#e94560"
CALENDAR_SELECTED = "#ce1f6a"
reminder_interval = 10  # seconds (for testing, would be higher in production)


def show_login():
    def login():
        username = user_entry.get()
        password = pass_entry.get()
        if os.path.exists(f"{username}.json"):
            with open(f"{username}.json", "r") as f:
                data = json.load(f)
                if data["password"] == password:
                    global current_user
                    current_user = username
                    login_win.after(100, lambda: [login_win.destroy(), show_tracker()])
                else:
                    status_label.configure(text="Wrong password", text_color="#e94560")
                    login_frame.configure(border_color="#e94560")
        else:
            status_label.configure(text="User does not exist", text_color="#e94560")
            login_frame.configure(border_color="#e94560")

    def register():
        username = user_entry.get()
        password = pass_entry.get()
        if not username or not password:
            status_label.configure(text="Username and password required", text_color="#e94560")
            return

        if not os.path.exists(f"{username}.json"):
            with open(f"{username}.json", "w") as f:
                json.dump({"password": password, "habits": {}, "history": [], "schedules": {}}, f)
            status_label.configure(text="Registered. You can login.", text_color="#4ecca3")
            login_frame.configure(border_color="#4ecca3")
        else:
            status_label.configure(text="User already exists", text_color="#e94560")
            login_frame.configure(border_color="#e94560")

    def on_enter(event):
        login()

    # Creating the login window with a modern design
    login_win = ctk.CTk()
    login_win.geometry("800x750")
    login_win.title("Habit Tracker App - Login")
    login_win.configure(fg_color=DARK_COLOR)

    # Add logo/title
    title_frame = ctk.CTkFrame(login_win, fg_color="transparent")
    title_frame.pack(pady=(50, 30))

    ctk.CTkLabel(title_frame, text="Ready to start your day?", font=("Arial", 26, "bold"),
                 text_color=TEXT_COLOR).pack()
    ctk.CTkLabel(title_frame, text="With our brand new habit tracker app!\n Do your habits one step at a time.",
                 font=("Arial", 18), text_color="#eeeeee").pack()

    # Login frame with border
    login_frame = ctk.CTkFrame(login_win, corner_radius=15, border_width=2, border_color=HIGHLIGHT_COLOR)
    login_frame.pack(padx=40, pady=20, fill="x")

    ctk.CTkLabel(login_frame, text="Username:", font=("Arial", 14)).pack(pady=(15, 5), padx=20, anchor="w")
    user_entry = ctk.CTkEntry(login_frame, height=40, font=("Arial", 14),
                              placeholder_text="Enter username")
    user_entry.pack(pady=5, padx=20, fill="x")

    ctk.CTkLabel(login_frame, text="Password:", font=("Arial", 14)).pack(pady=(15, 5), padx=20, anchor="w")
    pass_entry = ctk.CTkEntry(login_frame, height=40, font=("Arial", 14),
                              placeholder_text="Enter password", show="•")
    pass_entry.pack(pady=5, padx=20, fill="x")
    pass_entry.bind("<Return>", on_enter)

    # Buttons frame
    buttons_frame = ctk.CTkFrame(login_win, fg_color="transparent")
    buttons_frame.pack(pady=15, fill="x", padx=40)

    login_btn = ctk.CTkButton(buttons_frame, text="Login", command=login,
                              font=("Arial", 14, "bold"), height=40,
                              fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED)
    login_btn.pack(pady=5, fill="x")

    register_btn = ctk.CTkButton(buttons_frame, text="Register", command=register,
                                 font=("Arial", 14), height=40,
                                 fg_color=HIGHLIGHT_COLOR, hover_color="#1a5f7a")
    register_btn.pack(pady=5, fill="x")

    status_label = ctk.CTkLabel(login_win, text="", font=("Arial", 14))
    status_label.pack(pady=15)

    # Version info
    ctk.CTkLabel(login_win, text="v2.0", font=("Arial", 10), text_color="#555555").pack(side="bottom", pady=10)

    login_win.mainloop()


def export_pdf(habit_data):
    """
    Export habit tracker data to a PDF file.
    Includes habit name, streak (Done/Missed), and status (Finished/Unfinished) with timestamp.
    """
    try:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Save Habit Tracker PDF As"
        )

        if not file_path:
            return

        pdf = canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        # Title
        pdf.setTitle("Habit Tracker Report")
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(50, height - 50, f"Habit Tracker Report, {current_user}")

        # Current Date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 80, f"Generated on: {current_date}")
        pdf.line(50, height - 90, width - 50, height - 90)

        # Habit Data
        y = height - 120
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Habit")
        pdf.drawString(250, y, "Streak")
        pdf.drawString(350, y, "Status")
        y -= 20

        pdf.setFont("Helvetica", 12)
        for habit, info in habit_data.items():
            # Determine streak (Done/Missed)
            streak = "Done" if info.get("streak", 0) > 0 else "Missed"

            # Determine status (Finished/Unfinished)
            status = "Finished" if info.get("status", "") == "Completed" else "Unfinished"

            pdf.drawString(50, y, habit)
            pdf.drawString(250, y, streak)
            pdf.drawString(350, y, status)
            y -= 20

            if y < 50:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 12)

        pdf.save()

        messagebox.showinfo("Export Successful", f"PDF saved to: {file_path}")

        try:
            if os.name == "nt":
                os.startfile(file_path)
            elif platform.system() == "Darwin":
                subprocess.call(["open", file_path])
            else:
                subprocess.call(["xdg-open", file_path])
        except Exception:
            pass

    except Exception as e:
        messagebox.showerror("Export Error", f"Failed to export PDF:\n{e}")

def show_tracker(export_pdf=None):
    app = ctk.CTk()
    app.geometry("1000x700")
    app.title(f"HabitFlow - {current_user}'s Dashboard")
    app.configure(fg_color=DARK_COLOR)
    # Load user data
    user_file = f"{current_user}.json"
    with open(user_file, "r") as f:
        data = json.load(f)
        habit_data = data.get("habits", {})
        habit_history = data.get("history", [])
        schedule_data = data.get("schedules", {})

    # Save user data function
    def save_data():
        with open(user_file, "w") as f:
            json.dump({
                "password": data["password"],
                "habits": habit_data,
                "history": habit_history,
                "schedules": schedule_data
            }, f)

    # Create main frames
    header_frame = ctk.CTkFrame(app, fg_color=ACCENT_COLOR, height=80)
    header_frame.pack(fill="x", padx=0, pady=0)

    # Create a frame for the content area
    content_frame = ctk.CTkFrame(app, fg_color="transparent")
    content_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

    # Split content into left and right sections
    left_frame = ctk.CTkFrame(content_frame, fg_color=ACCENT_COLOR, corner_radius=15)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=0)

    right_frame = ctk.CTkFrame(content_frame, fg_color=ACCENT_COLOR, corner_radius=15, width=350)
    right_frame.pack(side="right", fill="y", padx=(10, 0), pady=0)
    right_frame.pack_propagate(False)  # Prevent frame from shrinking

    # Header components
    ctk.CTkLabel(header_frame, text=f"Welcome! To the Habit Tracker App, {current_user}.",
                 font=("Arial", 24, "bold"), text_color="#ffffff").pack(side="left", padx=20, pady=20)

    # Right side header buttons
    header_buttons = ctk.CTkFrame(header_frame, fg_color="transparent")
    header_buttons.pack(side="right", padx=20, pady=20)

    # Header buttons
    ctk.CTkButton(header_buttons, text="History",
                  command=lambda: show_tab("history"),
                  fg_color=HIGHLIGHT_COLOR, hover_color="#1a5f7a",
                  width=100).pack(side="left", padx=5)

    ctk.CTkButton(header_buttons, text="Export PDF",
                  command=lambda: export_pdf(habit_data),
                  fg_color=HIGHLIGHT_COLOR, hover_color="#1a5f7a",
                  width=100).pack(side="left", padx=5)

    ctk.CTkButton(header_buttons, text="Logout",
                  command=lambda: [app.destroy(), show_login()],
                  fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED,
                  width=100).pack(side="left", padx=5)

    # Tab system for left panel
    tab_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    tab_frame.pack(fill="x", padx=20, pady=(20, 0))

    tabs = ["dashboard", "scheduler", "history"]
    tab_buttons = {}

    for i, tab in enumerate(tabs):
        tab_buttons[tab] = ctk.CTkButton(
            tab_frame,
            text=tab.capitalize(),
            fg_color=TEXT_COLOR if i == 0 else "transparent",
            hover_color=CALENDAR_SELECTED,
            corner_radius=10,
            height=35,
            command=lambda t=tab: show_tab(t)
        )
        tab_buttons[tab].pack(side="left", padx=(0, 10))

    # Content container for tab content
    tab_content = ctk.CTkFrame(left_frame, fg_color="transparent")
    tab_content.pack(fill="both", expand=True, padx=20, pady=20)

    # Dictionary to store content frames
    content_frames = {}

    # Create frames for each tab
    for tab in tabs:
        content_frames[tab] = ctk.CTkFrame(tab_content, fg_color="transparent")
        if tab != "dashboard":  # Initially hide all except dashboard
            content_frames[tab].pack_forget()

    # Show the selected tab
    def show_tab(tab_name):
        # Update button colors
        for tab in tabs:
            if tab == tab_name:
                tab_buttons[tab].configure(fg_color=TEXT_COLOR)
            else:
                tab_buttons[tab].configure(fg_color="transparent")

        # Hide all frames
        for frame in content_frames.values():
            frame.pack_forget()

        # Show selected frame
        content_frames[tab_name].pack(fill="both", expand=True)

    # Initially pack dashboard
    content_frames["dashboard"].pack(fill="both", expand=True)

    # DASHBOARD TAB CONTENT
    dashboard_frame = content_frames["dashboard"]

    # Habit addition section
    add_habit_frame = ctk.CTkFrame(dashboard_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    add_habit_frame.pack(fill="x", pady=(0, 15))

    add_habit_label = ctk.CTkLabel(add_habit_frame, text="Add New Habit", font=("Arial", 16, "bold"))
    add_habit_label.pack(pady=(10, 5), padx=15)

    habit_entry_frame = ctk.CTkFrame(add_habit_frame, fg_color="transparent")
    habit_entry_frame.pack(fill="x", padx=15, pady=(0, 15))

    habit_entry = ctk.CTkEntry(habit_entry_frame, placeholder_text="Enter habit name", height=35)
    habit_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

    def add_habit():
        name = habit_entry.get().strip()
        if name and name not in habit_data:
            habit_data[name] = {"checked": False, "progress": 0, "created_date": datetime.datetime.now().strftime("%Y-%m-%d")}
            save_data()
            draw_habits()
            habit_entry.delete(0, "end")
            update_habit_selector()  # Update habit selector for timer
        elif name in habit_data:
            messagebox.showinfo("Duplicate", "This habit already exists")

    add_btn = ctk.CTkButton(habit_entry_frame, text="Add", command=add_habit, width=100,
                            fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED)
    add_btn.pack(side="right")

    # Habits list section
    habits_list_frame = ctk.CTkScrollableFrame(dashboard_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    habits_list_frame.pack(fill="both", expand=True)

    habits_header = ctk.CTkLabel(habits_list_frame, text="Your Habits", font=("Arial", 16, "bold"))
    habits_header.pack(pady=(10, 15), padx=15, anchor="w")

    def draw_habits():
        # Clear previous habits (except the header)
        for widget in list(habits_list_frame.winfo_children())[1:]:
            widget.destroy()

        if not habit_data:
            no_habits_label = ctk.CTkLabel(habits_list_frame, text="No habits added yet. Add your first habit above!",
                                           font=("Arial", 14))
            no_habits_label.pack(pady=20)
            return

        # Sort habits by name
        sorted_habits = sorted(habit_data.keys())

        for name in sorted_habits:
            habit_item = ctk.CTkFrame(habits_list_frame, fg_color="transparent", height=60)
            habit_item.pack(fill="x", padx=10, pady=5)
            habit_item.pack_propagate(False)  # Keep consistent height

            # Left side with checkbox and name
            habit_left = ctk.CTkFrame(habit_item, fg_color="transparent")
            habit_left.pack(side="left", fill="y")

            chk_var = tk.BooleanVar(value=habit_data[name]["checked"])

            def toggle_habit_check(var, index, mode, habit_name=name):
                habit_data[habit_name]["checked"] = chk_var.get()
                if chk_var.get():
                    habit_history.append({
                        "habit": habit_name,
                        "status": "Completed",
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                save_data()

            chk_var.trace_add("write", toggle_habit_check)

            chk = ctk.CTkCheckBox(habit_left, text="", variable=chk_var, width=20,
                                  checkbox_width=22, checkbox_height=22)
            chk.pack(side="left", padx=(5, 10), pady=10)

            habit_name_label = ctk.CTkLabel(habit_left, text=name, font=("Arial", 14, "bold"))
            habit_name_label.pack(side="left", pady=10)

            # Right side with progress and buttons
            habit_right = ctk.CTkFrame(habit_item, fg_color="transparent")
            habit_right.pack(side="right", fill="y")

            def mark_done(habit_name=name):
                habit_data[habit_name]["progress"] = 100
                habit_data[habit_name]["checked"] = True
                habit_history.append({
                    "habit": habit_name,
                    "status": "Done",
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                save_data()
                draw_habits()

            def delete_habit(habit_name=name):
                if messagebox.askyesno("Delete Habit", f"Are you sure you want to delete '{habit_name}'?"):
                    if habit_name in habit_data:
                        del habit_data[habit_name]

                        # Also remove any schedules for this habit
                        keys_to_delete = []
                        for schedule_key in schedule_data:
                            if schedule_data[schedule_key]["habit"] == habit_name:
                                keys_to_delete.append(schedule_key)

                        for key in keys_to_delete:
                            del schedule_data[key]

                        save_data()
                        draw_habits()
                        update_habit_selector()


                        # Progress bar

            prog = ctk.CTkProgressBar(habit_item, width=120)
            prog.set(habit_data[name]["progress"] / 100)
            prog.pack(side="left", padx=15, fill="y")

            # Progress percentage label
            prog_label = ctk.CTkLabel(habit_item, text=f"{habit_data[name]['progress']}%", width=40)
            prog_label.pack(side="left", padx=(0, 10))

            # Mark done button
            done_btn = ctk.CTkButton(habit_right, text="Done", width=60, height=30,
                                     command=mark_done, fg_color=TEXT_COLOR,
                                     hover_color=CALENDAR_SELECTED, font=("Arial", 12))
            done_btn.pack(side="left", padx=5)

            # Delete button
            del_btn = ctk.CTkButton(habit_right, text="✕", width=30, height=30,
                                    command=delete_habit, fg_color="#666666",
                                    hover_color="#aa5555", font=("Arial", 12))
            del_btn.pack(side="left", padx=5)

    # SCHEDULER TAB CONTENT
    scheduler_frame = content_frames["scheduler"]

    scheduler_top_frame = ctk.CTkFrame(scheduler_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10, height=320)
    scheduler_top_frame.pack(fill="x", pady=(0, 15))
    scheduler_top_frame.pack_propagate(False)  # Fix the height

    scheduler_header = ctk.CTkLabel(scheduler_top_frame, text="Schedule a Habit", font=("Arial", 16, "bold"))
    scheduler_header.pack(pady=(15, 10), padx=15, anchor="w")

    # Scheduler form
    form_frame = ctk.CTkFrame(scheduler_top_frame, fg_color="transparent")
    form_frame.pack(fill="x", padx=15, pady=10)

    # Habit selection
    ctk.CTkLabel(form_frame, text="Select Habit:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
    habit_selector = ctk.CTkComboBox(form_frame, values=list(habit_data.keys()) or ["No habits available"], width=250)
    habit_selector.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 0))

    def update_habit_selector():
        habit_selector.configure(values=list(habit_data.keys()) or ["No habits available"])
        if list(habit_data.keys()):
            habit_selector.set(list(habit_data.keys())[0])
        else:
            habit_selector.set("No habits available")

    # Date selection (MM/DD/YYYY)
    ctk.CTkLabel(form_frame, text="Date (MM/DD/YYYY):", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
    date_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    date_frame.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))

    month_entry = ctk.CTkEntry(date_frame, width=40, placeholder_text="MM")
    month_entry.pack(side="left", padx=(0, 5))

    ctk.CTkLabel(date_frame, text="/").pack(side="left")

    day_entry = ctk.CTkEntry(date_frame, width=40, placeholder_text="DD")
    day_entry.pack(side="left", padx=5)

    ctk.CTkLabel(date_frame, text="/").pack(side="left")

    year_entry = ctk.CTkEntry(date_frame, width=60, placeholder_text="YYYY")
    year_entry.pack(side="left", padx=(5, 0))

    # Time selection (HH:MM)
    ctk.CTkLabel(form_frame, text="Time (HH:MM):", anchor="w").grid(row=2, column=0, sticky="w", pady=5)
    time_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
    time_frame.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 0))

    hour_entry = ctk.CTkEntry(time_frame, width=40, placeholder_text="HH")
    hour_entry.pack(side="left")

    ctk.CTkLabel(time_frame, text=":").pack(side="left")

    minute_entry = ctk.CTkEntry(time_frame, width=40, placeholder_text="MM")
    minute_entry.pack(side="left", padx=(5, 0))

    # For default date values
    today = datetime.datetime.now()
    month_entry.insert(0, f"{today.month:02d}")
    day_entry.insert(0, f"{today.day:02d}")
    year_entry.insert(0, f"{today.year}")
    hour_entry.insert(0, f"{today.hour:02d}")
    minute_entry.insert(0, f"{(today.minute + 5) % 60:02d}")  # Default to 5 minutes from now

    # Add schedule button
    def add_schedule():
        habit_name = habit_selector.get()
        if habit_name == "No habits available":
            messagebox.showinfo("No Habit", "Please add habits first")
            return

        try:
            # Validate date
            month = int(month_entry.get())
            day = int(day_entry.get())
            year = int(year_entry.get())
            hour = int(hour_entry.get())
            minute = int(minute_entry.get())

            # Basic validation
            if not (1 <= month <= 12 and 1 <= day <= 31 and year >= 2023 and 0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid date/time values")

            # Create a datetime object to validate the date further
            schedule_time = datetime.datetime(year, month, day, hour, minute)

            # Create a unique key for this schedule
            schedule_key = f"{habit_name}_{schedule_time.strftime('%Y%m%d%H%M%S')}"

            # Store the schedule
            schedule_data[schedule_key] = {
                "habit": habit_name,
                "date": schedule_time.strftime("%Y-%m-%d"),
                "time": schedule_time.strftime("%H:%M"),
                "timestamp": schedule_time.timestamp(),
                "notified": False
            }

            save_data()

            draw_schedules()

            # Start a reminder thread for this schedule if it's in the future
            start_reminder_thread(schedule_key, schedule_time)

            messagebox.showinfo("Success", f"Schedule added for '{habit_name}'")

        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your date and time inputs: {str(e)}")

    schedule_btn = ctk.CTkButton(
        form_frame, text="Add Schedule",
        command=add_schedule,
        fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED
    )
    schedule_btn.grid(row=3, column=1, sticky="w", pady=15, padx=(10, 0))

    # Calendar view in scheduler tab
    calendar_frame = ctk.CTkFrame(scheduler_top_frame, fg_color="transparent")
    calendar_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    # Month navigation for calendar
    cal_header_frame = ctk.CTkFrame(calendar_frame, fg_color="transparent")
    cal_header_frame.pack(fill="x", pady=(0, 10))

    # Schedules list
    schedules_frame = ctk.CTkScrollableFrame(scheduler_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    schedules_frame.pack(fill="both", expand=True)

    schedules_header = ctk.CTkLabel(schedules_frame, text="Your Scheduled Habits", font=("Arial", 16, "bold"))
    schedules_header.pack(pady=(10, 15), padx=15, anchor="w")

    def draw_schedules():
        # Clear previous schedules (except the header)
        for widget in list(schedules_frame.winfo_children())[1:]:
            widget.destroy()

        if not schedule_data:
            no_schedules_label = ctk.CTkLabel(schedules_frame, text="No scheduled habits yet.", font=("Arial", 14))
            no_schedules_label.pack(pady=20)
            return

        # Sort schedules by date/time
        sorted_schedules = sorted(
            schedule_data.items(),
            key=lambda x: (x[1]["date"], x[1]["time"])
        )

        for schedule_key, schedule in sorted_schedules:
            schedule_item = ctk.CTkFrame(schedules_frame, fg_color=ACCENT_COLOR, corner_radius=5, height=60)
            schedule_item.pack(fill="x", padx=10, pady=5)
            schedule_item.pack_propagate(False)

            # Date and time
            date_fmt = datetime.datetime.strptime(f"{schedule['date']} {schedule['time']}", "%Y-%m-%d %H:%M")
            date_str = date_fmt.strftime("%b %d, %Y at %I:%M %p")

            date_label = ctk.CTkLabel(schedule_item, text=date_str, font=("Arial", 12))
            date_label.pack(anchor="w", padx=15, pady=(10, 0))

            # Habit name
            habit_label = ctk.CTkLabel(schedule_item, text=schedule["habit"], font=("Arial", 14, "bold"))
            habit_label.pack(anchor="w", padx=15, pady=(0, 10))

            # Delete button
            def delete_schedule(key=schedule_key):
                if messagebox.askyesno("Delete Schedule", "Are you sure you want to delete this schedule?"):
                    del schedule_data[key]
                    save_data()
                    draw_schedules()


            del_btn = ctk.CTkButton(schedule_item, text="✕", width=30, height=30,
                                    command=delete_schedule, fg_color="#666666",
                                    hover_color="#aa5555", font=("Arial", 12))
            del_btn.place(relx=1.0, rely=0.5, anchor="e", x=-15)

    # Initialize calendar

    draw_schedules()

    # HISTORY TAB CONTENT
    history_frame = content_frames["history"]

    history_header = ctk.CTkLabel(history_frame, text="Habit History", font=("Arial", 18, "bold"))
    history_header.pack(pady=(0, 15), anchor="w")

    # Search section
    search_frame = ctk.CTkFrame(history_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    search_frame.pack(fill="x", pady=(0, 15))

    search_inner = ctk.CTkFrame(search_frame, fg_color="transparent")
    search_inner.pack(fill="x", padx=15, pady=15)

    ctk.CTkLabel(search_inner, text="Filter by Habit:", font=("Arial", 14)).pack(side="left", padx=(0, 10))

    habit_filter = ctk.CTkComboBox(search_inner, values=["All Habits"] + list(habit_data.keys()), width=200)
    habit_filter.pack(side="left")
    habit_filter.set("All Habits")

    def filter_history():
        display_history()

    ctk.CTkButton(search_inner, text="Filter", command=filter_history,
                  fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED).pack(side="left", padx=10)

    # History list
    history_list_frame = ctk.CTkScrollableFrame(history_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    history_list_frame.pack(fill="both", expand=True)

    def display_history():
        # Clear previous entries
        for widget in history_list_frame.winfo_children():
            widget.destroy()

        # Filter history based on selection
        selected_habit = habit_filter.get()
        filtered_history = habit_history

        if selected_habit != "All Habits":
            filtered_history = [entry for entry in habit_history if entry["habit"] == selected_habit]

        # Sort history by time (newest first)
        sorted_history = sorted(filtered_history, key=lambda x: x["time"], reverse=True)

        if not sorted_history:
            no_history_label = ctk.CTkLabel(history_list_frame, text="No history entries found.", font=("Arial", 14))
            no_history_label.pack(pady=20)
            return

        # Group by date
        grouped_history = {}
        for entry in sorted_history:
            # Extract date part only
            date_str = entry["time"].split()[0]
            if date_str not in grouped_history:
                grouped_history[date_str] = []
            grouped_history[date_str].append(entry)

        # Display grouped history
        for date_str, entries in grouped_history.items():
            # Format date display
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                date_display = date_obj.strftime("%B %d, %Y")
            except:
                date_display = date_str

            date_header = ctk.CTkFrame(history_list_frame, fg_color=ACCENT_COLOR, corner_radius=5)
            date_header.pack(fill="x", padx=10, pady=(10, 0))

            ctk.CTkLabel(date_header, text=date_display, font=("Arial", 14, "bold")).pack(
                pady=10, padx=15, anchor="w")

            # Entries for this date
            for entry in entries:
                entry_frame = ctk.CTkFrame(history_list_frame, fg_color="transparent")
                entry_frame.pack(fill="x", padx=20, pady=(5, 0))

                # Format time
                try:
                    time_only = entry["time"].split()[1]
                    time_obj = datetime.strptime(time_only, "%H:%M:%S")
                    time_display = time_obj.strftime("%I:%M %p")
                except:
                    time_display = entry["time"].split()[1] if len(entry["time"].split()) > 1 else ""

                time_label = ctk.CTkLabel(entry_frame, text=time_display, width=80, font=("Arial", 12))
                time_label.pack(side="left", padx=(0, 10))

                habit_label = ctk.CTkLabel(entry_frame, text=entry["habit"], font=("Arial", 14))
                habit_label.pack(side="left")

                status_frame = ctk.CTkFrame(entry_frame, fg_color=TEXT_COLOR, corner_radius=10)
                status_frame.pack(side="right", padx=10)

                status_label = ctk.CTkLabel(status_frame, text=entry["status"], font=("Arial", 12), text_color="white")
                status_label.pack(padx=10, pady=2)

    # RIGHT SIDEBAR CONTENT
    sidebar_title = ctk.CTkLabel(right_frame, text="Quick Timer", font=("Arial", 18, "bold"))
    sidebar_title.pack(pady=(20, 15), padx=20, anchor="w")

    # Timer section
    timer_frame = ctk.CTkFrame(right_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    timer_frame.pack(fill="x", padx=20, pady=(0, 15))

    # Habit selection for timer
    habit_timer_frame = ctk.CTkFrame(timer_frame, fg_color="transparent")
    habit_timer_frame.pack(fill="x", padx=15, pady=(15, 10))

    ctk.CTkLabel(habit_timer_frame, text="Select Habit:").pack(anchor="w")

    timer_habit_selector = ctk.CTkComboBox(
        habit_timer_frame,
        values=list(habit_data.keys()) or ["No habits available"],
        width=200
    )
    timer_habit_selector.pack(pady=5, anchor="w")

    # Time inputs
    time_inputs_frame = ctk.CTkFrame(timer_frame, fg_color="transparent")
    time_inputs_frame.pack(fill="x", padx=15, pady=10)

    ctk.CTkLabel(time_inputs_frame, text="Duration:").pack(anchor="w")

    duration_frame = ctk.CTkFrame(time_inputs_frame, fg_color="transparent")
    duration_frame.pack(fill="x", pady=5)

    timer_h = ctk.CTkEntry(duration_frame, width=60, placeholder_text="HH")
    timer_h.pack(side="left", padx=(0, 5))

    timer_m = ctk.CTkEntry(duration_frame, width=60, placeholder_text="MM")
    timer_m.pack(side="left", padx=5)

    timer_s = ctk.CTkEntry(duration_frame, width=60, placeholder_text="SS")
    timer_s.pack(side="left", padx=5)

    # Default timer values
    timer_h.insert(0, "00")
    timer_m.insert(0, "25")
    timer_s.insert(0, "00")

    # Timer display
    timer_display = ctk.CTkLabel(timer_frame, text="00:00:00", font=("Arial", 24, "bold"))
    timer_display.pack(pady=15)

    # Progress bar
    timer_progress = ctk.CTkProgressBar(timer_frame, width=250)
    timer_progress.pack(pady=(0, 15))
    timer_progress.set(0)

    # Timer control buttons
    timer_buttons = ctk.CTkFrame(timer_frame, fg_color="transparent")
    timer_buttons.pack(fill="x", padx=15, pady=(0, 15))

    timer_running = [False]
    pause_event = threading.Event()
    pause_event.set()
    timer_thread = [None]

    def start_timer():
        habit_name = timer_habit_selector.get()
        if habit_name == "No habits available":
            messagebox.showinfo("No Habit", "Please add habits first")
            return

        # Reset existing timer if running
        if timer_running[0]:
            timer_running[0] = False
            if timer_thread[0]:
                timer_thread[0].join(timeout=0.1)

        try:
            h = int(timer_h.get()) if timer_h.get() else 0
            m = int(timer_m.get()) if timer_m.get() else 0
            s = int(timer_s.get()) if timer_s.get() else 0
            total_sec = h * 3600 + m * 60 + s
            if total_sec <= 0:
                messagebox.showinfo("Invalid Time", "Please enter a valid time greater than zero")
                return

            max_sec = total_sec  # Store for progress calculation

            # Update button states
            start_btn.configure(state="disabled")
            pause_btn.configure(state="normal", text="Pause")
            stop_btn.configure(state="normal")

            timer_running[0] = True
            pause_event.set()  # Ensure not paused

            def countdown():
                nonlocal total_sec
                try:
                    while total_sec > 0 and timer_running[0]:
                        pause_event.wait()  # Wait if paused

                        # Update display
                        mins, secs = divmod(total_sec, 60)
                        hrs, mins = divmod(mins, 60)
                        display_text = f"{hrs:02d}:{mins:02d}:{secs:02d}"

                        # We need to use after() to update UI from the non-UI thread
                        app.after(0, lambda t=display_text: timer_display.configure(text=t))

                        # Update progress
                        progress = 1 - (total_sec / max_sec)
                        app.after(0, lambda p=progress: timer_progress.set(p))

                        time.sleep(1)
                        total_sec -= 1

                    if timer_running[0] and total_sec == 0:
                        app.after(0, lambda: timer_display.configure(text="Complete!"))
                        app.after(0, lambda: timer_progress.set(1))

                        # Update habit progress
                        if habit_name in habit_data:
                            habit_data[habit_name]["progress"] = min(100, habit_data[habit_name]["progress"] + 10)
                            habit_history.append({
                                "habit": habit_name,
                                "status": "Timer Completed",
                                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                            save_data()
                            app.after(0, draw_habits)

                            # Show notification
                            app.after(0, lambda: show_notification(f"Timer Complete for '{habit_name}'"))

                    # Reset UI when done
                    app.after(0, reset_timer_ui)
                except Exception as e:
                    print(f"Timer error: {e}")

            timer_thread[0] = threading.Thread(target=countdown)
            timer_thread[0].daemon = True
            timer_thread[0].start()

        except ValueError:
            messagebox.showinfo("Invalid Input", "Please enter valid numbers for hours, minutes, and seconds")

    def toggle_pause():
        if pause_event.is_set():
            pause_event.clear()
            pause_btn.configure(text="Resume")
        else:
            pause_event.set()
            pause_btn.configure(text="Pause")

    def stop_timer():
        timer_running[0] = False
        reset_timer_ui()

    def reset_timer_ui():
        timer_running[0] = False
        timer_display.configure(text="00:00:00")
        timer_progress.set(0)
        start_btn.configure(state="normal")
        pause_btn.configure(state="disabled", text="Pause")
        stop_btn.configure(state="disabled")

    timer_control_frame = ctk.CTkFrame(timer_buttons, fg_color="transparent")
    timer_control_frame.pack(fill="x")

    start_btn = ctk.CTkButton(timer_control_frame, text="Start", fg_color=TEXT_COLOR,
                              hover_color=CALENDAR_SELECTED, command=start_timer)
    start_btn.pack(side="left", expand=True, fill="x", padx=(0, 2))

    pause_btn = ctk.CTkButton(timer_control_frame, text="Pause", fg_color=HIGHLIGHT_COLOR,
                              hover_color="#1a5f7a", command=toggle_pause, state="disabled")
    pause_btn.pack(side="left", expand=True, fill="x", padx=2)

    stop_btn = ctk.CTkButton(timer_control_frame, text="Stop", fg_color="#666666",
                             hover_color="#aa5555", command=stop_timer, state="disabled")
    stop_btn.pack(side="left", expand=True, fill="x", padx=(2, 0))

    # Update timer habit selector
    def update_timer_habit_selector():
        timer_habit_selector.configure(values=list(habit_data.keys()) or ["No habits available"])
        if list(habit_data.keys()):
            timer_habit_selector.set(list(habit_data.keys())[0])
        else:
            timer_habit_selector.set("No habits available")

    update_timer_habit_selector()

    # Stats section
    stats_frame = ctk.CTkFrame(right_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    stats_frame.pack(fill="x", padx=20, pady=(0, 15))

    stats_label = ctk.CTkLabel(stats_frame, text="Your Stats", font=("Arial", 16, "bold"))
    stats_label.pack(pady=(15, 10), padx=15, anchor="w")

    # Stats content
    def update_stats():
        # Clear previous stats
        for widget in list(stats_frame.winfo_children())[1:]:
            widget.destroy()

        if not habit_data:
            no_stats = ctk.CTkLabel(stats_frame, text="No habits to display stats for.")
            no_stats.pack(pady=(0, 15), padx=15)
            return

        total_habits = ctk.CTkLabel(stats_frame, text=f"Total Habits: {len(habit_data)}")
        total_habits.pack(pady=5, padx=15, anchor="w")

        completed = sum(1 for h in habit_data.values() if h.get("checked"))
        completed_habits = ctk.CTkLabel(stats_frame, text=f"Completed: {completed}")
        completed_habits.pack(pady=5, padx=15, anchor="w")

        rate = (completed / len(habit_data)) * 100 if habit_data else 0
        rate_label = ctk.CTkLabel(stats_frame, text=f"Completion Rate: {rate:.1f}%")
        rate_label.pack(pady=5, padx=15, anchor="w")

    update_stats()

    # --- MARK HABIT DONE ---
    def mark_habit_done(habit_name):
        if habit_name in habit_data:
            habit_data[habit_name]["checked"] = True
            habit_data[habit_name]["status"] = "done"
            save_data()
            update_stats()

    # --- CHECK MISSED HABITS ---
    def check_missed_habits():
        now = datetime.datetime.now()
        for habit in habit_data.values():
            sched_time = habit.get("scheduled_time")
            status = habit.get("status", "pending")
            if sched_time and status == "pending":
                try:
                    scheduled_dt = datetime.strptime(sched_time, "%m/%d/%Y %H:%M")
                    if now > scheduled_dt:
                        habit["status"] = "missed"
                        habit["checked"] = False
                except ValueError:
                    continue
        save_data()
        update_stats()

    # Example call to check and update on app load:
    check_missed_habits()
    update_stats()

    # PDF export function
    def export_pdf(habit_data):
        """
        Export habit tracker data to a PDF file.
        Includes habit name, progress, and status (Finished/Unfinished) with timestamp.
        Mimics the 'Your Habits' dashboard style.
        """
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                title="Save Habit Tracker PDF As"
            )

            if not file_path:
                return

            pdf = canvas.Canvas(file_path, pagesize=letter)
            width, height = letter

            # Title
            pdf.setTitle("Habit Tracker Report")
            pdf.setFont("Helvetica-Bold", 18)
            pdf.drawString(50, height - 50, "Habit Tracker Report")

            # Current Date
            current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pdf.setFont("Helvetica", 12)
            pdf.drawString(50, height - 80, f"Generated on: {current_date}")
            pdf.line(50, height - 90, width - 50, height - 90)

            # Habit Data Header
            y_position = height - 120
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y_position, "Habit")
            pdf.drawString(250, y_position, "Status")
            pdf.drawString(350, y_position, "Progress")
            y_position -= 20

            pdf.setFont("Helvetica", 12)
            for name, info in habit_data.items():
                # Determine habit completion status
                if info["checked"]:
                    status = "Finished"
                    checkmark = "✓"  # Completed habit
                else:
                    status = "Unfinished"
                    checkmark = "✗"  # Incomplete habit

                # Habit name with checkmark
                pdf.drawString(50, y_position, f"{checkmark} {name}")

                # Habit status
                pdf.drawString(250, y_position, status)

                # Progress bar as percentage
                progress = f"{info['progress']}%"
                pdf.drawString(350, y_position, progress)
                y_position -= 20

                if y_position < 50:
                    pdf.showPage()
                    y_position = height - 50
                    pdf.setFont("Helvetica", 12)

            pdf.save()

            messagebox.showinfo("Export Successful", f"PDF saved to: {file_path}")

            try:
                if os.name == "nt":
                    os.startfile(file_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", file_path])
                else:
                    subprocess.call(["xdg-open", file_path])
            except Exception:
                pass

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF:\n{e}")

    # Initialize the history display
    display_history()

    # NOTIFICATION SYSTEM
    def show_notification(message):
        """Show a system notification for habit reminders"""
        notification_win = ctk.CTkToplevel(app)
        notification_win.title("Habit Reminder")
        notification_win.geometry("300x150")
        notification_win.attributes('-topmost', True)

        # Calculate position (bottom right of screen)
        screen_width = notification_win.winfo_screenwidth()
        screen_height = notification_win.winfo_screenheight()
        x_coordinate = screen_width - 320
        y_coordinate = screen_height - 200
        notification_win.geometry(f"+{x_coordinate}+{y_coordinate}")

        # Add notification content
        notif_frame = ctk.CTkFrame(notification_win, fg_color=HIGHLIGHT_COLOR)
        notif_frame.pack(fill="both", expand=True, padx=2, pady=2)

        ctk.CTkLabel(notif_frame, text="Habit Reminder", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        ctk.CTkLabel(notif_frame, text=message, wraplength=250).pack(pady=5)

        ctk.CTkButton(notif_frame, text="OK", width=100, command=notification_win.destroy,
                      fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED).pack(pady=10)

        # Auto-close after 10 seconds
        notification_win.after(10000, notification_win.destroy)

    # Reminder checker
    def check_reminders():
        now = datetime.datetime.now()
        current_time = now.timestamp()

        reminders_to_trigger = []

        for schedule_key, schedule in schedule_data.items():
            # Skip if already notified
            if schedule.get("notified", False):
                continue

            # Check if it's time to trigger
            schedule_time = schedule["timestamp"]

            if current_time >= schedule_time:
                # Mark as notified
                schedule_data[schedule_key]["notified"] = True
                save_data()

                # Add to trigger list
                habit_name = schedule["habit"]
                reminders_to_trigger.append(f"Time to do: {habit_name}")

        # Show notifications for any triggered reminders
        for reminder in reminders_to_trigger:
            show_notification(reminder)

        # Schedule next check
        app.after(reminder_interval * 1000, check_reminders)

    # Start the reminder checker
    app.after(1000, check_reminders)

    # Start reminder threads for existing schedules
    def start_reminder_thread(schedule_key, schedule_time):
        # Only start a thread if the schedule is in the future
        now = datetime.datetime.now()
        if schedule_time > now:
            # Calculate seconds until the scheduled time
            delta = (schedule_time - now).total_seconds()

            def reminder_thread():
                try:
                    # Sleep until the scheduled time
                    time.sleep(delta)

                    # Check if the schedule still exists and isn't notified
                    if (schedule_key in schedule_data and
                            not schedule_data[schedule_key].get("notified", False)):
                        # Mark as notified
                        schedule_data[schedule_key]["notified"] = True
                        save_data()

                        # Show notification
                        habit_name = schedule_data[schedule_key]["habit"]
                        app.after(0, lambda: show_notification(f"Time to do: {habit_name}"))
                except Exception as e:
                    print(f"Reminder thread error: {e}")

            # Start the thread
            t = threading.Thread(target=reminder_thread)
            t.daemon = True
            t.start()
            notification_threads.append(t)

    # Start threads for all future schedules
    for schedule_key, schedule in schedule_data.items():
        if not schedule.get("notified", False):
            try:
                schedule_time = datetime.strptime(
                    f"{schedule['date']} {schedule['time']}",
                    "%Y-%m-%d %H:%M"
                )
                start_reminder_thread(schedule_key, schedule_time)
            except Exception as e:
                print(f"Error starting reminder for {schedule_key}: {e}")

    app.mainloop()


if __name__ == "__main__":
    show_login()