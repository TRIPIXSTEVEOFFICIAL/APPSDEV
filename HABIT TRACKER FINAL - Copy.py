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
from tkcalendar import Calendar

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
                    status_label.configure(text="Wrong password, amego.", text_color="#e94560")
                    login_frame.configure(border_color="#e94560")
        else:
            status_label.configure(text="User does not exist, please register first.", text_color="#e94560")
            login_frame.configure(border_color="#e94560")

    def register():
        username = user_entry.get()
        password = pass_entry.get()
        if not username or not password:
            status_label.configure(text="Username and password required to register.", text_color="#e94560")
            return

        if not os.path.exists(f"{username}.json"):
            with open(f"{username}.json", "w") as f:
                json.dump({"password": password, "habits": {}, "history": [], "schedules": {}}, f)
            status_label.configure(text="Registered. You can login.", text_color="#4ecca3")
            login_frame.configure(border_color="#4ecca3")
        else:
            status_label.configure(text="User already exists, please register a new one.", text_color="#e94560")
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
    ctk.CTkLabel(login_win, text="v2.1", font=("Arial", 10), text_color="#555555").pack(side="bottom", pady=10)

    login_win.mainloop()


def export_pdf(habit_data, habit_history=None):
    """
    Export habit tracker data to a PDF file.
    Includes habit name, streak (Done/Missed), and status (Finished/Unfinished) with timestamp.
    Also includes history if provided.
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
        pdf.drawString(50, height - 50, f"{current_user}'s, Habit Tracker Report")

        # Current Date
        current_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, height - 80, f"Generated on: {current_date}")
        pdf.line(50, height - 90, width - 50, height - 90)

        # Habit Data
        y = height - 120
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "HABITS SUMMARY")
        y -= 30

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Habit")
        pdf.drawString(250, y, "Status")
        pdf.drawString(350, y, "Progress")
        y -= 20

        pdf.setFont("Helvetica", 12)
        for habit, info in habit_data.items():
            # Determine status
            status = "Finished" if info.get("checked", False) else "Unfinished"
            progress = f"{info.get('progress', 0)}%"

            pdf.drawString(50, y, habit)
            pdf.drawString(250, y, status)
            pdf.drawString(350, y, progress)
            y -= 20

            if y < 100:  # Leave space for history section
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica-Bold", 14)
                pdf.drawString(50, y, "HABITS SUMMARY (continued)")
                y -= 30
                pdf.setFont("Helvetica", 12)

        # Add History section if available
        if habit_history and len(habit_history) > 0:
            # Start a new page for history
            pdf.showPage()
            y = height - 50

            pdf.setFont("Helvetica-Bold", 18)
            pdf.drawString(50, y, f"{current_user}'s ,Habit History Report")
            y -= 30

            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(50, y, "Date & Time")
            pdf.drawString(200, y, "Habit")
            pdf.drawString(350, y, "Action")
            y -= 20

            # Sort history by time (newest first)
            sorted_history = sorted(habit_history, key=lambda x: x["time"], reverse=True)

            pdf.setFont("Helvetica", 10)
            for entry in sorted_history:
                pdf.drawString(50, y, entry["time"])
                pdf.drawString(200, y, entry["habit"])
                pdf.drawString(350, y, entry["status"])
                y -= 15

                if y < 50:
                    pdf.showPage()
                    y = height - 50
                    pdf.setFont("Helvetica-Bold", 12)
                    pdf.drawString(50, y, "Date & Time")
                    pdf.drawString(200, y, "Habit")
                    pdf.drawString(350, y, "Action")
                    y -= 20
                    pdf.setFont("Helvetica", 10)

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


def show_tracker():
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
    ctk.CTkLabel(header_frame, text=f"Welcome! To the Habit Tracker App, {current_user}!",
                 font=("Arial", 24, "bold"), text_color="#ffffff").pack(side="left", padx=20, pady=20)

    # Right side header buttons
    header_buttons = ctk.CTkFrame(header_frame, fg_color="transparent")
    header_buttons.pack(side="right", padx=20, pady=20)

    # Header buttons
    ctk.CTkButton(header_buttons, text="Export PDF",
                  command=lambda: export_pdf(habit_data, habit_history),
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

        # Refresh content if needed
        if tab_name == "history":
            display_history()
            update_habit_filter()  # Update filter dropdown with latest habits

    # Initially pack dashboard
    content_frames["dashboard"].pack(fill="both", expand=True)

    # DASHBOARD TAB CONTENT
    dashboard_frame = content_frames["dashboard"]

    # Habit addition section
    add_habit_frame = ctk.CTkFrame(dashboard_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    add_habit_frame.pack(fill="x", pady=(0, 15))

    add_habit_label = ctk.CTkLabel(add_habit_frame, text="Add your new habit below!", font=("Arial", 16, "bold"))
    add_habit_label.pack(pady=(10, 5), padx=15)

    habit_entry_frame = ctk.CTkFrame(add_habit_frame, fg_color="transparent")
    habit_entry_frame.pack(fill="x", padx=15, pady=(0, 15))

    habit_entry = ctk.CTkEntry(habit_entry_frame, placeholder_text="Enter habit name", height=35)
    habit_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

    def add_habit():
        name = habit_entry.get().strip()
        if name and name not in habit_data:
            habit_data[name] = {"checked": False, "progress": 0,
                                "created_date": datetime.datetime.now().strftime("%Y-%m-%d")}

            # Add creation to history
            habit_history.append({
                "habit": name,
                "status": "Created",
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            save_data()
            draw_habits()
            habit_entry.delete(0, "end")

            # Update all selectors and displays that show habits
            update_habit_filter()  # Update habit selector for timer

            update_habit_filter()  # Update history filter
            update_stats()  # Update stats display

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
                    # Update progress when checked
                    habit_data[habit_name]["progress"] = 100
                save_data()
                update_stats()  # Update stats when habit is checked/unchecked
                # Update all selectors and displays that show habits
                update_habit_selector()  # Update habit selector for timer

                update_habit_filter()  # Update history filter
                update_stats()  # Update stats display

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
                update_stats()  # Update stats display
                # Update all selectors and displays that show habits
                update_habit_selector()  # Update habit selector for timer

                update_habit_filter()  # Update history filter
                update_stats()  # Update stats display

            def delete_habit(habit_name=name):
                if messagebox.askyesno("Delete Habit", f"Are you sure you want to delete '{habit_name}'?"):
                    if habit_name in habit_data:
                        # Add deletion to history before removing
                        habit_history.append({
                            "habit": habit_name,
                            "status": "Deleted",
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

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
                        update_stats()  # Timer section
                        update_habit_filter()

                        # If we're currently on history tab, refresh it
                        if tab_buttons["history"].cget("fg_color") == TEXT_COLOR:
                            display_history()

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


        scheduler_frame = content_frames["scheduler"]

        scheduler_top_frame = ctk.CTkFrame(scheduler_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10,
                                           height=380)  # Increased height
        scheduler_top_frame.pack(fill="x", pady=(0, 15))
        scheduler_top_frame.pack_propagate(False)  # Fix the height

        # Scheduler form
        form_frame = ctk.CTkFrame(scheduler_top_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=15, pady=10)

        # Habit selection
        ctk.CTkLabel(form_frame, text="Select Habit:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
        habit_selector = ctk.CTkComboBox(form_frame, values=list(habit_data.keys()) or ["No habits available"],
                                         width=250)
        habit_selector.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 0))

        if list(habit_data.keys()):  # Set initial value if habits exist
            habit_selector.set(list(habit_data.keys())[0])
        else:
            habit_selector.set("No habits available")

        def update_habit_selector():
            habit_selector.configure(values=list(habit_data.keys()) or ["No habits available"])
            if list(habit_data.keys()):
                habit_selector.set(list(habit_data.keys())[0])
            else:
                habit_selector.set("No habits available")

        # Date selection with calendar and manual input
        ctk.CTkLabel(form_frame, text="Date:", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
        date_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        date_frame.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))

        # Manual date entry
        month_entry = ctk.CTkEntry(date_frame, width=40, placeholder_text="MM")
        month_entry.pack(side="left", padx=(0, 5))

        ctk.CTkLabel(date_frame, text="/").pack(side="left")

        day_entry = ctk.CTkEntry(date_frame, width=40, placeholder_text="DD")
        day_entry.pack(side="left", padx=5)

        ctk.CTkLabel(date_frame, text="/").pack(side="left")

        year_entry = ctk.CTkEntry(date_frame, width=60, placeholder_text="YYYY")
        year_entry.pack(side="left", padx=(5, 5))

        update_habit_selector()
        # Update all selectors and displays that show habits

        update_habit_selector()  # Update timer habit dropdown
        update_habit_filter()  # Update history filter
        update_stats()  # Update stats display
        # Calendar popup button
        def open_calendar():
            cal_window = ctk.CTkToplevel(scheduler_frame)
            cal_window.title("Select Date")
            cal_window.geometry("300x300")
            cal_window.resizable(False, False)

            today = datetime.datetime.now()

            cal = Calendar(cal_window, selectmode="day", year=today.year, month=today.month, day=today.day)
            cal.pack(pady=20)

            def set_date():
                selected_date = cal.get_date()  # Format: MM/DD/YY
                month, day, year_short = selected_date.split('/')
                year = f"20{year_short}" if int(year_short) < 50 else f"19{year_short}"  # Assume 20XX for years < 50

                month_entry.delete(0, 'end')
                month_entry.insert(0, month)

                day_entry.delete(0, 'end')
                day_entry.insert(0, day)

                year_entry.delete(0, 'end')
                year_entry.insert(0, year)

                cal_window.destroy()

            select_button = ctk.CTkButton(cal_window, text="Select", command=set_date)
            select_button.pack(pady=10)

        calendar_button = ctk.CTkButton(date_frame, text="📅", width=30, command=open_calendar)
        calendar_button.pack(side="left", padx=(5, 0))

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

        # Reminder Options Section
        ctk.CTkLabel(form_frame, text="Reminder Options:", anchor="w").grid(row=3, column=0, sticky="w", pady=5)
        reminder_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        reminder_frame.grid(row=3, column=1, sticky="w", pady=5, padx=(10, 0))

        # Enable reminder checkbox
        reminder_var = tk.BooleanVar(value=True)
        reminder_check = ctk.CTkCheckBox(reminder_frame, text="Enable reminder", variable=reminder_var)
        reminder_check.pack(side="left", padx=(0, 10))

        # Reminder time selection
        reminder_time_label = ctk.CTkLabel(reminder_frame, text="Remind")
        reminder_time_label.pack(side="left")

        remind_times = ["At time of event", "5 minutes before", "10 minutes before", "15 minutes before",
                        "30 minutes before", "1 hour before", "1 day before"]
        reminder_time_var = ctk.StringVar(value=remind_times[0])
        reminder_time_dropdown = ctk.CTkComboBox(reminder_frame, values=remind_times, variable=reminder_time_var,
                                                 width=150)
        reminder_time_dropdown.pack(side="left", padx=5)

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

                # Calculate reminder time if enabled
                reminder_time = None
                if reminder_var.get():
                    remind_option = reminder_time_var.get()
                    if remind_option == "At time of event":
                        reminder_time = schedule_time
                    elif remind_option == "5 minutes before":
                        reminder_time = schedule_time - datetime.timedelta(minutes=5)
                    elif remind_option == "10 minutes before":
                        reminder_time = schedule_time - datetime.timedelta(minutes=10)
                    elif remind_option == "15 minutes before":
                        reminder_time = schedule_time - datetime.timedelta(minutes=15)
                    elif remind_option == "30 minutes before":
                        reminder_time = schedule_time - datetime.timedelta(minutes=30)
                    elif remind_option == "1 hour before":
                        reminder_time = schedule_time - datetime.timedelta(hours=1)
                    elif remind_option == "1 day before":
                        reminder_time = schedule_time - datetime.timedelta(days=1)

                # Store the schedule
                schedule_data[schedule_key] = {
                    "habit": habit_name,
                    "date": schedule_time.strftime("%Y-%m-%d"),
                    "time": schedule_time.strftime("%H:%M"),
                    "timestamp": schedule_time.timestamp(),
                    "notified": False,
                    "reminder_enabled": reminder_var.get(),
                    "reminder_option": reminder_time_var.get() if reminder_var.get() else None,
                    "reminder_timestamp": reminder_time.timestamp() if reminder_time else None
                }

                # Add to history
                habit_history.append({
                    "habit": habit_name,
                    "status": "Scheduled",
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                save_data()
                draw_schedules()
                habit_entry.delete(0, "end")

                update_habit_selector()  # Update habit selector for timer
                update_habit_filter()  # Update history filter
                update_stats()  # Update stats display


                # Start a reminder thread for this schedule if it's in the future
                start_reminder_thread(schedule_key, schedule_time, reminder_time if reminder_var.get() else None)

                messagebox.showinfo("Success",
                                    f"Schedule added for '{habit_name}' with {reminder_time_var.get() if reminder_var.get() else 'no'} reminder")

            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Please check your date and time inputs: {str(e)}")

        add_button = ctk.CTkButton(scheduler_top_frame, text="Add Schedule", command=add_schedule)
        add_button.pack(pady=15)

        # Bottom frame for upcoming schedules
        scheduler_bottom_frame = ctk.CTkFrame(scheduler_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=14)
        scheduler_bottom_frame.pack(fill="both", expand=True)

        schedules_header = ctk.CTkLabel(scheduler_bottom_frame, text="Upcoming Schedules", font=("Arial", 18, "bold"))
        schedules_header.pack(pady=(35, 35), padx=35, anchor="w")

        # Scrollable frame for schedules
        schedules_container = ctk.CTkScrollableFrame(scheduler_bottom_frame, fg_color="transparent")
        schedules_container.pack(fill="both", expand=True, padx=40, pady=(40, 40))

        # Function to display schedules
        def draw_schedules():
            # Clear existing widgets
            for widget in schedules_container.winfo_children():
                widget.destroy()

            # Get current time for comparison
            now = datetime.datetime.now()

            # Filter and sort upcoming schedules
            upcoming_schedules = {}
            for key, sched in schedule_data.items():
                sched_time = datetime.datetime.fromtimestamp(sched["timestamp"])
                if sched_time >= now:
                    upcoming_schedules[key] = sched

            # Sort by timestamp
            sorted_schedules = sorted(upcoming_schedules.items(), key=lambda x: x[1]["timestamp"])

            if not sorted_schedules:
                no_schedules_label = ctk.CTkLabel(schedules_container, text="No upcoming schedules")
                no_schedules_label.pack(pady=20)
                return

            # Create schedule items
            for idx, (key, sched) in enumerate(sorted_schedules):
                schedule_frame = ctk.CTkFrame(schedules_container, fg_color=("#e0e0e0", "#333333"), corner_radius=5)
                schedule_frame.pack(fill="x", pady=5)

                # Format date and time for display
                date_obj = datetime.datetime.strptime(f"{sched['date']} {sched['time']}", "%Y-%m-%d %H:%M")
                display_date = date_obj.strftime("%A, %B %d, %Y")
                display_time = date_obj.strftime("%I:%M %p")

                habit_label = ctk.CTkLabel(schedule_frame, text=sched["habit"], font=("Arial", 14, "bold"))
                habit_label.pack(anchor="w", padx=10, pady=(10, 0))

                date_time_label = ctk.CTkLabel(schedule_frame, text=f"{display_date} at {display_time}")
                date_time_label.pack(anchor="w", padx=10, pady=(5, 0))

                # Show reminder info if enabled
                if sched.get("reminder_enabled", False):
                    reminder_label = ctk.CTkLabel(schedule_frame,
                                                  text=f"Reminder: {sched.get('reminder_option', 'At time of event')}")
                    reminder_label.pack(anchor="w", padx=10, pady=(5, 0))

                button_frame = ctk.CTkFrame(schedule_frame, fg_color="transparent")
                button_frame.pack(fill="x", padx=10, pady=10)

                # Function to delete this schedule
                def delete_schedule(schedule_key=key):
                    if messagebox.askyesno("Confirm", f"Delete schedule for '{schedule_data[schedule_key]['habit']}'?"):
                        habit_name = schedule_data[schedule_key]["habit"]
                        del schedule_data[schedule_key]


                        # Add deletion to history
                        habit_history.append({
                            "habit": habit_name,
                            "status": "Schedule Deleted",
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                        save_data()
                        draw_schedules()
                        save_data()
                        draw_habits()
                        update_stats()  # Timer section
                        update_habit_filter()

                delete_button = ctk.CTkButton(button_frame, text="Delete", fg_color="#FF5555", hover_color="#FF0000",
                                              width=80, height=25, command=lambda sk=key: delete_schedule(sk))
                delete_button.pack(side="right")

        # Call draw_schedules once to initialize
        draw_schedules()

        return update_habit_selector, draw_schedules

    # Now let's enhance the reminder functionality
    def start_reminder_thread(schedule_key, schedule_time, reminder_time=None):
        """
        Starts a thread to check for and display reminders

        Parameters:
        schedule_key - The unique key for this schedule
        schedule_time - The datetime when the habit is scheduled
        reminder_time - Optional datetime when to show the reminder (if different from schedule_time)
        """
        import threading
        import time

        def check_and_notify():
            # Reference global schedule_data from the main app
            nonlocal schedule_key, schedule_time, reminder_time

            # If the schedule was deleted, exit the thread
            if schedule_key not in schedule_data:
                return

            # Check both the main time and reminder time
            now = datetime.datetime.now()

            # Check for the reminder time first
            if reminder_time and not schedule_data[schedule_key].get("reminder_notified", False):
                seconds_until_reminder = (reminder_time - now).total_seconds()

                if seconds_until_reminder > 0:
                    # Sleep until reminder time
                    time.sleep(seconds_until_reminder)

                # Check again if schedule exists (could have been deleted while sleeping)
                if schedule_key in schedule_data:
                    # Update the notified flag
                    schedule_data[schedule_key]["reminder_notified"] = True
                    save_data()

                    # Show reminder notification
                    habit_name = schedule_data[schedule_key]["habit"]

                    # Calculate time until event
                    time_diff = schedule_time - reminder_time
                    if time_diff.days > 0:
                        time_until = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''}"
                    elif time_diff.seconds // 3600 > 0:
                        time_until = f"{time_diff.seconds // 3600} hour{'s' if time_diff.seconds // 3600 > 1 else ''}"
                    elif time_diff.seconds // 60 > 0:
                        time_until = f"{time_diff.seconds // 60} minute{'s' if time_diff.seconds // 60 > 1 else ''}"
                    else:
                        time_until = "now"

                    messagebox.showinfo("Reminder", f"Reminder for habit '{habit_name}' in {time_until}")

            # Now check for the main schedule time
            if not schedule_data[schedule_key].get("notified", False):
                seconds_until_schedule = (schedule_time - now).total_seconds()

                if seconds_until_schedule > 0:
                    # Sleep until schedule time
                    time.sleep(seconds_until_schedule)

                # Check again if schedule exists (could have been deleted while sleeping)
                if schedule_key in schedule_data:
                    # Update the notified flag
                    schedule_data[schedule_key]["notified"] = True
                    save_data()

                    # Show the main notification
                    habit_name = schedule_data[schedule_key]["habit"]
                    messagebox.showinfo("Habit Reminder", f"Time to complete your habit: '{habit_name}'")

        # Start the thread
        reminder_thread = threading.Thread(target=check_and_notify)
        reminder_thread.daemon = True  # Thread will close when main program exits
        reminder_thread.start()

        # HISTORY TAB CONTENT

    history_frame = content_frames["history"]

    # Filter and sort options
    controls_frame = ctk.CTkFrame(history_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10, height=80)
    controls_frame.pack(fill="x", pady=(0, 15))
    controls_frame.pack_propagate(False)  # Fix height

    # Filter by habit dropdown
    filter_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    filter_frame.pack(side="left", padx=15, pady=15, fill="y")

    ctk.CTkLabel(filter_frame, text="Filter by Habit:").pack(side="left", padx=(0, 10))

    habit_filter = ctk.CTkComboBox(filter_frame, values=["All Habits"] + list(habit_data.keys()), width=150)
    habit_filter.pack(side="left")
    habit_filter.set("All Habits")

    def update_habit_filter():
        habit_filter.configure(values=["All Habits"] + list(habit_data.keys()))
        habit_filter.set("All Habits")

    # Sort options
    sort_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
    sort_frame.pack(side="right", padx=15, pady=15, fill="y")

    ctk.CTkLabel(sort_frame, text="Sort by:").pack(side="left", padx=(0, 10))

    sort_options = ctk.CTkComboBox(sort_frame, values=["Newest First", "Oldest First"], width=120)
    sort_options.pack(side="left")
    sort_options.set("Newest First")

    # Apply button
    ctk.CTkButton(controls_frame, text="Apply Filter",
                  command=lambda: display_history(),
                  fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED,
                  width=100).pack(side="left", padx=15)

    # History list
    history_list_frame = ctk.CTkScrollableFrame(history_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    history_list_frame.pack(fill="both", expand=True)

    history_header = ctk.CTkLabel(history_list_frame, text="Activity History", font=("Arial", 16, "bold"))
    history_header.pack(pady=(10, 15), padx=15, anchor="w")

    def display_history():
        # Clear previous history items (except the header)
        for widget in list(history_list_frame.winfo_children())[1:]:
            widget.destroy()

        if not habit_history:
            no_history = ctk.CTkLabel(history_list_frame, text="No history yet. Start using the app!",
                                      font=("Arial", 14))
            no_history.pack(pady=20)
            return

        # Filter by habit if needed
        selected_habit = habit_filter.get()
        filtered_history = habit_history
        if selected_habit != "All Habits":
            filtered_history = [item for item in habit_history if item["habit"] == selected_habit]

        # Sort by time with error handling
        valid_history = []
        for item in filtered_history:
            try:
                if "time" in item and item["time"]:
                    # Try to parse the datetime string
                    datetime.datetime.strptime(item["time"], "%Y-%m-%d %H:%M:%S")
                    valid_history.append(item)
            except (ValueError, TypeError):
                # Skip items with invalid datetime format
                continue

        sort_by = sort_options.get()
        sorted_history = sorted(valid_history,
                                key=lambda x: datetime.datetime.strptime(x["time"], "%Y-%m-%d %H:%M:%S"),
                                reverse=(sort_by == "Newest First"))

        if not sorted_history:
            no_matches = ctk.CTkLabel(history_list_frame, text="No matching history items found.",
                                      font=("Arial", 14))
            no_matches.pack(pady=20)
            return

        # Display history items
        for item in sorted_history:
            # Create frame for history item
            history_item = ctk.CTkFrame(history_list_frame, fg_color="transparent", height=50)
            history_item.pack(fill="x", padx=10, pady=3)
            history_item.pack_propagate(False)  # Keep consistent height

            # Status indicator color
            status_color = TEXT_COLOR  # Default
            if item["status"] == "Completed" or item["status"] == "Done":
                status_color = "#4ecca3"  # Green
            elif item["status"] == "Deleted" or item["status"] == "Schedule Deleted":
                status_color = "#e94560"  # Red
            elif item["status"] == "Created":
                status_color = "#4da6ff"  # Blue
            elif item["status"] == "Scheduled":
                status_color = "#ffcc00"  # Yellow

            # Status indicator
            status_indicator = ctk.CTkFrame(history_item, fg_color=status_color, width=10, corner_radius=5)
            status_indicator.pack(side="left", fill="y", padx=(5, 10), pady=5)

            # Date and time
            time_label = ctk.CTkLabel(history_item, text=item["time"], font=("Arial", 12),
                                      width=160, anchor="w")
            time_label.pack(side="left", pady=10)

            # Habit name
            habit_label = ctk.CTkLabel(history_item, text=item["habit"], font=("Arial", 12, "bold"),
                                       width=160, anchor="w")
            habit_label.pack(side="left", pady=10)

            # Status
            status_label = ctk.CTkLabel(history_item, text=item["status"], font=("Arial", 12),
                                        width=100, anchor="w")
            status_label.pack(side="left", pady=10)

    # RIGHT SIDE PANEL (STATS & TIMER)
    # Stats section
    stats_frame = ctk.CTkFrame(right_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    stats_frame.pack(fill="x", padx=15, pady=15)

    stats_label = ctk.CTkLabel(stats_frame, text="Your Stats", font=("Arial", 16, "bold"))
    stats_label.pack(pady=(10, 5), padx=15, anchor="w")

    # Stats content
    stats_content = ctk.CTkFrame(stats_frame, fg_color="transparent")
    stats_content.pack(fill="x", padx=15, pady=(0, 15))

    def update_stats():
        # Clear previous stats
        for widget in stats_content.winfo_children():
            widget.destroy()

        total_habits = len(habit_data)
        completed_habits = sum(1 for h in habit_data.values() if h.get("checked", False))
        completion_rate = (completed_habits / total_habits * 100) if total_habits > 0 else 0

        # Total habits
        ctk.CTkLabel(stats_content, text=f"Total Habits: {total_habits}", font=("Arial", 14)).pack(anchor="w", pady=3)

        # Completed habits
        ctk.CTkLabel(stats_content, text=f"Completed Today: {completed_habits}", font=("Arial", 14)).pack(anchor="w",
                                                                                                          pady=3)

        # Completion rate
        ctk.CTkLabel(stats_content, text=f"Completion Rate: {completion_rate:.1f}%", font=("Arial", 14)).pack(
            anchor="w", pady=3)

        # Progress bar
        prog_frame = ctk.CTkFrame(stats_content, fg_color="transparent", height=30)
        prog_frame.pack(fill="x", pady=10)
        prog_frame.pack_propagate(False)

        prog_bar = ctk.CTkProgressBar(prog_frame)
        prog_bar.set(completion_rate / 100)
        prog_bar.pack(fill="x")

        def record_timer_session(total_time, remaining_time):
            """Record a timer session in the history"""
            time_spent = total_time - remaining_time

            # Update habit progress based on time
            habit_name = timer_habit_selector.get()
            if habit_name != "No habits available" and time_spent > 0:
                hours_spent = time_spent // 3600
                minutes_spent = (time_spent % 3600) // 60
                seconds_spent = time_spent % 60

                # Format time string based on duration
                time_str = ""
                if hours_spent > 0:
                    time_str = f"{hours_spent} hr {minutes_spent} min {seconds_spent} sec"
                else:
                    time_str = f"{minutes_spent} min {seconds_spent} sec"

                # Add timer session to history
                habit_history.append({
                    "habit": habit_name,
                    "status": f"Timer Session ({time_str})",
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                # Update progress if it wasn't already completed
                if not habit_data[habit_name].get("checked", False):
                    # Calculate progress based on actual time spent compared to target time
                    target_time = total_time
                    percentage_completed = min(100, (time_spent / target_time) * 100)

                    # Update progress only if this session's progress is better than existing
                    habit_data[habit_name]["progress"] = max(habit_data[habit_name].get("progress", 0),
                                                             int(percentage_completed))

                    # Mark as checked if progress is 100%
                    if habit_data[habit_name]["progress"] >= 100:
                        habit_data[habit_name]["checked"] = True
                        habit_history.append({
                            "habit": habit_name,
                            "status": "Completed via Timer",
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

                save_data()
                draw_habits()
                update_stats()  # Timer section
                update_habit_filter()

        timer_frame = ctk.CTkFrame(right_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=15)
        timer_frame.pack(fill="x", padx=15, pady=(15, 15))

        timer_label = ctk.CTkLabel(timer_frame, text="Countdown Timer", font=("Arial", 16, "bold"))
        timer_label.pack(pady=(40, 40), padx=50, anchor="w")

        # Timer content
        timer_habit_frame = ctk.CTkFrame(timer_frame, fg_color="transparent")
        timer_habit_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(timer_habit_frame, text="Select Habit:").pack(side="left")

        timer_habit_selector = ctk.CTkComboBox(timer_habit_frame,
                                               values=list(habit_data.keys()) or ["No habits available"],
                                               width=150)
        timer_habit_selector.pack(side="left", padx=(10, 10))

        if list(habit_data.keys()):  # Set initial value if habits exist
            timer_habit_selector.set(list(habit_data.keys())[0])
        else:
            timer_habit_selector.set("No habits available")

        def update_timer_habit_selector():
            timer_habit_selector.configure(values=list(habit_data.keys()) or ["No habits available"])
            if list(habit_data.keys()):
                timer_habit_selector.set(list(habit_data.keys())[0])
            else:
                timer_habit_selector.set("No habits available")

        # Time setter frame
        time_setter_frame = ctk.CTkFrame(timer_frame, fg_color="transparent")
        time_setter_frame.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(time_setter_frame, text="Set Time:").pack(side="left")

        # Hours, minutes and seconds entry
        hours_entry = ctk.CTkEntry(time_setter_frame, width=50, placeholder_text="Hr")
        hours_entry.pack(side="left", padx=(10, 0))
        hours_entry.insert(0, "00")  # Default to 0 hours

        ctk.CTkLabel(time_setter_frame, text=":").pack(side="left", padx=(2, 2))

        minutes_entry = ctk.CTkEntry(time_setter_frame, width=50, placeholder_text="Min")
        minutes_entry.pack(side="left")
        minutes_entry.insert(0, "25")  # Default to 25 minutes (pomodoro)

        ctk.CTkLabel(time_setter_frame, text=":").pack(side="left", padx=(2, 2))

        seconds_entry = ctk.CTkEntry(time_setter_frame, width=50, placeholder_text="Sec")
        seconds_entry.pack(side="left")
        seconds_entry.insert(0, "00")  # Default to 0 seconds

        # Timer display
        timer_display_frame = ctk.CTkFrame(timer_frame, fg_color=DARK_COLOR, height=80, corner_radius=5)
        timer_display_frame.pack(fill="x", padx=15, pady=10)
        timer_display_frame.pack_propagate(False)

        timer_time = ctk.CTkLabel(timer_display_frame, text="25:00", font=("Arial", 30, "bold"))
        timer_time.pack(pady=(15, 5))

        # Add progress bar
        progress_bar = ctk.CTkProgressBar(timer_display_frame, width=250, height=10,
                                          progress_color=TEXT_COLOR, fg_color="#333333")
        progress_bar.pack(pady=(0, 10))
        progress_bar.set(0)  # Initialize at 0

        # Timer controls
        timer_controls = ctk.CTkFrame(timer_frame, fg_color="transparent")
        timer_controls.pack(fill="x", padx=15, pady=(0, 15))

        # Timer variables
        timer_running = False
        timer_seconds = 0  # Will be set when timer starts
        timer_thread = None
        timer_stop_event = threading.Event()
        initial_seconds = 0  # To track the initial time set

        def update_timer_display():
            hours = timer_seconds // 3600
            minutes = (timer_seconds % 3600) // 60
            seconds = timer_seconds % 60
            timer_time.configure(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Update progress bar
            if initial_seconds > 0:
                progress_value = 1 - (timer_seconds / initial_seconds)
                progress_bar.set(progress_value)
            else:
                progress_bar.set(0)

        # Update display initially
        update_timer_display()
        update_timer_habit_selector()
        update_habit_filter()

        # Update display when time inputs change
        def on_time_inputs_changed(*args):
            if not timer_running:
                try:
                    hrs = int(hours_entry.get() or "0")
                    mins = int(minutes_entry.get() or "0")
                    secs = int(seconds_entry.get() or "0")
                    timer_time.configure(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
                except ValueError:
                    pass

        # Track changes to time entry fields
        hours_var = ctk.StringVar()
        minutes_var = ctk.StringVar()
        seconds_var = ctk.StringVar()
        hours_entry.configure(textvariable=hours_var)
        minutes_entry.configure(textvariable=minutes_var)
        seconds_entry.configure(textvariable=seconds_var)
        hours_var.trace_add("write", on_time_inputs_changed)
        minutes_var.trace_add("write", on_time_inputs_changed)
        seconds_var.trace_add("write", on_time_inputs_changed)

        def timer_tick():
            nonlocal timer_seconds
            while not timer_stop_event.is_set() and timer_seconds > 0:
                time.sleep(1)
                timer_seconds -= 1

                # Use after method to update UI from main thread
                app.after(0, update_timer_display)

                # Check if timer reached zero
                if timer_seconds <= 0:
                    app.after(0, lambda: handle_timer_completion())
                    break

        def handle_timer_completion():
            habit_name = timer_habit_selector.get()

            # Show completion notification
            messagebox.showinfo("Timer Complete", f"Time's up for {habit_name}!")

            # Record the completed session
            record_timer_session(initial_seconds, 0)  # All time was used

            # Reset the timer
            reset_timer(auto_reset=True)  # Auto reset without calculating time again

        def start_timer():
            nonlocal timer_running, timer_thread, timer_stop_event, timer_seconds, initial_seconds

            if timer_running:
                return

            habit_name = timer_habit_selector.get()
            if habit_name == "No habits available":
                messagebox.showinfo("No Habit", "Please add habits first")
                return

            # Set timer value based on custom inputs
            try:
                # Get and validate custom time inputs
                hrs = hours_entry.get().strip() or "0"
                mins = minutes_entry.get().strip() or "0"
                secs = seconds_entry.get().strip() or "0"

                try:
                    hrs = int(hrs)
                    mins = int(mins)
                    secs = int(secs)

                    # Basic validation
                    if hrs < 0 or mins < 0 or secs < 0 or mins >= 60 or secs >= 60:
                        raise ValueError("Invalid time format")

                    if hrs == 0 and mins == 0 and secs == 0:
                        messagebox.showinfo("Invalid Time", "Please enter a time greater than 0")
                        return

                    timer_seconds = hrs * 3600 + mins * 60 + secs
                except ValueError:
                    messagebox.showinfo("Invalid Time", "Please enter valid numbers for hours, minutes and seconds")
                    return

                initial_seconds = timer_seconds  # Store initial time for progress calculation
                update_timer_display()
            except ValueError:
                messagebox.showinfo("Invalid Time", "Please enter a valid time")
                return

            timer_running = True
            timer_stop_event.clear()
            timer_thread = threading.Thread(target=timer_tick)
            timer_thread.daemon = True
            timer_thread.start()

            start_btn.configure(state="disabled")
            stop_btn.configure(state="normal")
            reset_btn.configure(state="normal")
            hours_entry.configure(state="disabled")
            minutes_entry.configure(state="disabled")
            seconds_entry.configure(state="disabled")

        def stop_timer():
            nonlocal timer_running, timer_thread

            if not timer_running:
                return

            timer_stop_event.set()
            if timer_thread:
                timer_thread.join(0.1)

            timer_running = False
            start_btn.configure(state="normal")
            stop_btn.configure(state="disabled")
            hours_entry.configure(state="normal")
            minutes_entry.configure(state="normal")
            seconds_entry.configure(state="normal")

        def reset_timer(auto_reset=False):
            nonlocal timer_seconds, initial_seconds
            stop_timer()

            # Only calculate and record time if not an auto-reset (auto-reset already recorded)
            if not auto_reset:
                # Calculate time spent before reset
                time_spent = initial_seconds - timer_seconds
                record_timer_session(initial_seconds, timer_seconds)

            # Reset timer display
            try:
                hrs = int(hours_entry.get() or "0")
                mins = int(minutes_entry.get() or "0")
                secs = int(seconds_entry.get() or "0")
                timer_seconds = hrs * 3600 + mins * 60 + secs
                update_timer_display()
            except ValueError:
                timer_seconds = 0
                update_timer_display()
                update_timer_habit_selector()

            # Reset progress bar
            progress_bar.set(0)
            reset_btn.configure(state="disabled")

        # Timer buttons
        start_btn = ctk.CTkButton(timer_controls, text="Start", command=start_timer,
                                  fg_color=TEXT_COLOR, hover_color=CALENDAR_SELECTED, width=70)
        start_btn.pack(side="left", padx=(0, 5))

        stop_btn = ctk.CTkButton(timer_controls, text="Stop", command=stop_timer,
                                 state="disabled", fg_color="#666666", hover_color="#aa5555", width=70)
        stop_btn.pack(side="left", padx=5)

        reset_btn = ctk.CTkButton(timer_controls, text="Reset", command=reset_timer,
                                  state="disabled", fg_color=HIGHLIGHT_COLOR, hover_color="#1a5f7a", width=70)
        reset_btn.pack(side="left", padx=5)

    # Notification section
    notif_frame = ctk.CTkFrame(right_frame, fg_color=HIGHLIGHT_COLOR, corner_radius=10)
    notif_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    notif_label = ctk.CTkLabel(notif_frame, text="Notifications", font=("Arial", 16, "bold"))
    notif_label.pack(pady=(10, 5), padx=15, anchor="w")

    # Notifications content
    notif_content = ctk.CTkScrollableFrame(notif_frame, fg_color="transparent")
    notif_content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def add_notification(message, importance="normal"):
        # Create notification item
        notif_item = ctk.CTkFrame(notif_content, fg_color=DARK_COLOR, corner_radius=5, height=60)
        notif_item.pack(fill="x", pady=5)
        notif_item.pack_propagate(False)

        # Color based on importance
        color = "#4ecca3"  # Green for normal
        if importance == "warning":
            color = "#ffcc00"  # Yellow
        elif importance == "critical":
            color = "#e94560"  # Red

        indicator = ctk.CTkFrame(notif_item, fg_color=color, width=5, corner_radius=2)
        indicator.pack(side="left", fill="y", padx=(5, 0), pady=5)

        message_label = ctk.CTkLabel(notif_item, text=message, font=("Arial", 12),
                                     wraplength=250, justify="left")
        message_label.pack(side="left", padx=10, pady=10, fill="both", expand=True)

        # Time
        time_label = ctk.CTkLabel(notif_item, text=datetime.datetime.now().strftime("%H:%M"),
                                  font=("Arial", 10), text_color="#888888")
        time_label.pack(side="right", padx=10)

        return notif_item

    # Add welcome notification
    add_notification(f"Welcome back, {current_user}! Ready to track your habits?")

    # Function to check upcoming schedules and show notifications
    def check_schedules():
        now = datetime.datetime.now()
        current_timestamp = now.timestamp()

        notifications_shown = 0

        # Check all schedules
        for key, schedule in schedule_data.items():
            schedule_timestamp = schedule["timestamp"]

            # If the schedule is in the past and hasn't been notified yet
            if schedule_timestamp <= current_timestamp and not schedule["notified"]:
                habit_name = schedule["habit"]
                schedule_time = f"{schedule['date']} at {schedule['time']}"

                # Show notification
                add_notification(f"Time to do: {habit_name}\nScheduled for {schedule_time}", "warning")

                # Mark as notified
                schedule_data[key]["notified"] = True
                save_data()

                notifications_shown += 1

                # Limit notifications per check
                if notifications_shown >= 3:
                    break

        # Continue checking every interval
        app.after(reminder_interval * 1000, check_schedules)

    # Thread to handle reminder notifications
    def start_reminder_thread(schedule_key, schedule_time):
        def reminder_task():
            now = datetime.datetime.now()
            wait_seconds = max(0, (schedule_time - now).total_seconds())

            # Wait until scheduled time
            if wait_seconds > 0:
                time.sleep(wait_seconds)

            # Check if schedule still exists and hasn't been notified
            if schedule_key in schedule_data and not schedule_data[schedule_key]["notified"]:
                habit_name = schedule_data[schedule_key]["habit"]
                schedule_str = f"{schedule_data[schedule_key]['date']} at {schedule_data[schedule_key]['time']}"

                # Show desktop notification if possible
                try:
                    if platform.system() == "Windows":
                        from random import ToastNotifier
                        toaster = ToastNotifier()
                        toaster.show_toast("Habit Reminder", f"Time to do: {habit_name}", duration=10)
                    elif platform.system() == "Darwin":  # macOS
                        os.system(
                            f"""osascript -e 'display notification "Time to do: {habit_name}" with title "Habit Reminder"'""")
                    elif platform.system() == "Linux":
                        os.system(f"""notify-send "Habit Reminder" "Time to do: {habit_name}" """)
                except Exception:
                    pass  # Silent fail if notification fails

                # Mark as notified
                schedule_data[schedule_key]["notified"] = True
                save_data()

        # Start thread
        thread = threading.Thread(target=reminder_task)
        thread.daemon = True
        thread.start()
        notification_threads.append(thread)

    # Start schedule checking
    app.after(1000, check_schedules)

    # Initialize displays
    draw_habits()
    display_history()
    update_stats()
    update_habit_filter()

    # Setup reminder threads for existing schedules
    for key, schedule in schedule_data.items():
        if not schedule["notified"]:
            try:
                schedule_time = datetime.datetime.strptime(
                    f"{schedule['date']} {schedule['time']}",
                    "%Y-%m-%d %H:%M"
                )
                start_reminder_thread(key, schedule_time)
            except ValueError:
                pass

    app.mainloop()


if __name__ == "__main__":
    show_login()
