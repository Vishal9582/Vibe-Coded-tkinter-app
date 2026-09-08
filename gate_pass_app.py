"""
Gate Pass Management System
---------------------------------
A desktop application (Tkinter) backed by MySQL for logging who enters
and exits the office gate.

Requirements:
    pip install mysql-connector-python

The database connection (host / IP / port / user / password / database) is
stored in a `config.ini` file next to this script (or next to the .exe when
packaged). You can change it any time from inside the app using the
"DB Settings" button — no code editing or rebuild required.

Before first run:
    1. Start MySQL and run gate_pass_schema.sql to create the database.
    2. Launch the app and set your connection via the "DB Settings" button,
       or edit config.ini directly.
    3. python gate_pass_app.py
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from configparser import ConfigParser

import mysql.connector
from mysql.connector import Error

PASS_TYPES = ["Visitor", "Employee", "Contractor", "Delivery", "VIP", "Interview"]


# ------------------------------------------------------------------
#  Connection settings stored in an external config.ini
# ------------------------------------------------------------------
def get_base_dir():
    # When packaged by PyInstaller, files sit next to the .exe, not the script.
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def save_db_config(config):
    path = os.path.join(get_base_dir(), "config.ini")
    parser = ConfigParser()
    parser["mysql"] = {k: str(v) for k, v in config.items()}
    with open(path, "w") as f:
        parser.write(f)


def load_db_config():
    path = os.path.join(get_base_dir(), "config.ini")
    parser = ConfigParser()
    if os.path.exists(path):
        parser.read(path)
        db = parser["mysql"]
        return {
            "host": db.get("host", "localhost"),
            "port": db.getint("port", 3306),
            "user": db.get("user", "root"),
            "password": db.get("password", ""),
            "database": db.get("database", "gate_pass_db"),
        }
    # First run: create an editable template, then use the defaults.
    default = {"host": "localhost", "port": 3306, "user": "root",
               "password": "", "database": "gate_pass_db"}
    save_db_config(default)
    return default


# ==================================================================
#  Data access layer
# ==================================================================
class Database:
    """Thin wrapper around mysql-connector. Opens a fresh connection per call,
    so changing self.config (e.g. from the settings dialog) takes effect at
    once with no reconnect logic needed."""

    def __init__(self, config):
        self.config = config

    def _connect(self):
        return mysql.connector.connect(**self.config)

    def test(self, config=None):
        """Return (ok, error_message) for the given config (or the current one)."""
        cfg = config or self.config
        try:
            conn = mysql.connector.connect(connection_timeout=5, **cfg)
            conn.close()
            return True, ""
        except Error as e:
            return False, str(e)

    def add_entry(self, data):
        sql = """
            INSERT INTO gate_entries
                (visitor_name, phone, pass_type, purpose, person_to_meet,
                 department, vehicle_number, entry_time, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'IN')
        """
        values = (
            data["visitor_name"], data["phone"], data["pass_type"],
            data["purpose"], data["person_to_meet"], data["department"],
            data["vehicle_number"], datetime.now(),
        )
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, values)
            conn.commit()
        finally:
            conn.close()

    def mark_exit(self, entry_id):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE gate_entries SET exit_time=%s, status='OUT' "
                "WHERE id=%s AND status='IN'",
                (datetime.now(), entry_id),
            )
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def delete_entry(self, entry_id):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM gate_entries WHERE id=%s", (entry_id,))
            conn.commit()
        finally:
            conn.close()

    def fetch_entries(self, search="", status_filter="All"):
        sql = """
            SELECT id, visitor_name, phone, pass_type, person_to_meet,
                   department, vehicle_number, entry_time, exit_time, status
            FROM gate_entries
            WHERE 1=1
        """
        params = []
        if search:
            sql += " AND (visitor_name LIKE %s OR phone LIKE %s OR person_to_meet LIKE %s)"
            like = f"%{search}%"
            params += [like, like, like]
        if status_filter in ("IN", "OUT"):
            sql += " AND status=%s"
            params.append(status_filter)
        sql += " ORDER BY entry_time DESC"

        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            conn.close()

    def stats(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT SUM(status='IN'), SUM(status='OUT'), COUNT(*) "
                "FROM gate_entries WHERE DATE(entry_time)=CURDATE()"
            )
            row = cur.fetchone()
            return {"inside": row[0] or 0, "exited": row[1] or 0, "total": row[2] or 0}
        finally:
            conn.close()


# ==================================================================
#  User interface
# ==================================================================
class GatePassApp(tk.Tk):
    def __init__(self, db):
        super().__init__()
        self.db = db

        self.title("Gate Pass Management System")
        self.geometry("1080x680")
        self.configure(bg="#f2f4f7")
        self.minsize(960, 600)

        self._build_styles()
        self._build_header()
        self._build_form()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()

        self.refresh_table()

    # -- styling ---------------------------------------------------
    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Accent.TButton", background="#2563eb", foreground="white")
        style.map("Accent.TButton", background=[("active", "#1d4ed8")])

    # -- header ----------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self, bg="#1e293b", height=64)
        header.pack(fill="x")
        tk.Label(
            header, text="  \U0001F6AA  Gate Pass Management System",
            bg="#1e293b", fg="white", font=("Segoe UI", 16, "bold"),
        ).pack(side="left", pady=14, padx=8)

    # -- entry form ------------------------------------------------
    def _build_form(self):
        form = tk.LabelFrame(
            self, text="  New Entry  ", bg="#f2f4f7",
            font=("Segoe UI", 11, "bold"), padx=12, pady=10,
        )
        form.pack(fill="x", padx=14, pady=(12, 6))

        self.vars = {
            "visitor_name": tk.StringVar(),
            "phone": tk.StringVar(),
            "pass_type": tk.StringVar(value=PASS_TYPES[0]),
            "purpose": tk.StringVar(),
            "person_to_meet": tk.StringVar(),
            "department": tk.StringVar(),
            "vehicle_number": tk.StringVar(),
        }

        def field(parent, label, var, r, c, combo=False):
            tk.Label(parent, text=label, bg="#f2f4f7",
                     font=("Segoe UI", 10)).grid(row=r, column=c, sticky="w", padx=6, pady=4)
            if combo:
                w = ttk.Combobox(parent, textvariable=var, values=PASS_TYPES,
                                 state="readonly", width=22)
            else:
                w = ttk.Entry(parent, textvariable=var, width=25)
            w.grid(row=r, column=c + 1, padx=6, pady=4, sticky="w")
            return w

        # Fields marked * are required.
        field(form, "Visitor Name *", self.vars["visitor_name"], 0, 0)
        field(form, "Phone *", self.vars["phone"], 0, 2)
        field(form, "Pass Type *", self.vars["pass_type"], 0, 4, combo=True)
        field(form, "Person to Meet *", self.vars["person_to_meet"], 1, 0)
        field(form, "Department *", self.vars["department"], 1, 2)
        field(form, "Vehicle No.", self.vars["vehicle_number"], 1, 4)
        field(form, "Purpose", self.vars["purpose"], 2, 0)

        ttk.Button(form, text="  + Register Entry  ", style="Accent.TButton",
                   command=self.add_entry).grid(row=2, column=4, columnspan=2,
                                                sticky="e", padx=6, pady=6)

    # -- toolbar (search / filter / actions) -----------------------
    def _build_toolbar(self):
        bar = tk.Frame(self, bg="#f2f4f7")
        bar.pack(fill="x", padx=14, pady=(4, 0))

        tk.Label(bar, text="Search:", bg="#f2f4f7",
                 font=("Segoe UI", 10)).pack(side="left")
        self.search_var = tk.StringVar()
        ent = ttk.Entry(bar, textvariable=self.search_var, width=28)
        ent.pack(side="left", padx=6)
        ent.bind("<Return>", lambda e: self.refresh_table())

        tk.Label(bar, text="Status:", bg="#f2f4f7",
                 font=("Segoe UI", 10)).pack(side="left", padx=(10, 2))
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(bar, textvariable=self.filter_var, values=["All", "IN", "OUT"],
                     state="readonly", width=8).pack(side="left")

        ttk.Button(bar, text="Search", command=self.refresh_table).pack(side="left", padx=6)
        ttk.Button(bar, text="Reset", command=self._reset_search).pack(side="left")

        ttk.Button(bar, text="DB Settings", command=self.open_db_settings).pack(side="right", padx=4)
        ttk.Button(bar, text="Mark Exit", command=self.mark_exit).pack(side="right", padx=4)
        ttk.Button(bar, text="Delete", command=self.delete_entry).pack(side="right", padx=4)
        ttk.Button(bar, text="Refresh", command=self.refresh_table).pack(side="right", padx=4)

    # -- data table ------------------------------------------------
    def _build_table(self):
        wrap = tk.Frame(self, bg="#f2f4f7")
        wrap.pack(fill="both", expand=True, padx=14, pady=8)

        cols = ("id", "name", "phone", "type", "meet", "dept",
                "vehicle", "in", "out", "status")
        headings = ("ID", "Name", "Phone", "Pass Type", "Meeting", "Dept",
                    "Vehicle", "Entry Time", "Exit Time", "Status")
        widths = (45, 150, 100, 90, 130, 90, 90, 140, 140, 65)

        self.tree = ttk.Treeview(wrap, columns=cols, show="headings")
        for c, h, w in zip(cols, headings, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center"
                             if c in ("id", "status") else "w")

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self.tree.tag_configure("in", background="#dcfce7")
        self.tree.tag_configure("out", background="#f1f5f9")

    # -- status bar ------------------------------------------------
    def _build_statusbar(self):
        self.status = tk.Label(self, text="", bg="#e2e8f0", anchor="w",
                               font=("Segoe UI", 9), padx=10)
        self.status.pack(fill="x", side="bottom")

    # ============================================================
    #  Database settings dialog
    # ============================================================
    def open_db_settings(self):
        win = tk.Toplevel(self)
        win.title("Database Settings")
        win.geometry("400x330")
        win.configure(bg="#f2f4f7")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Connect to a database",
                 bg="#f2f4f7", font=("Segoe UI", 12, "bold")).grid(
                     row=0, column=0, columnspan=2, pady=(14, 8), padx=14, sticky="w")

        fields = [
            ("Host / IP", "host"),
            ("Port", "port"),
            ("User", "user"),
            ("Password", "password"),
            ("Database", "database"),
        ]
        entries = {}
        for i, (label, key) in enumerate(fields, start=1):
            tk.Label(win, text=label, bg="#f2f4f7", font=("Segoe UI", 10)).grid(
                row=i, column=0, sticky="w", padx=14, pady=6)
            var = tk.StringVar(value=str(self.db.config.get(key, "")))
            ent = ttk.Entry(win, textvariable=var, width=28,
                            show="*" if key == "password" else "")
            ent.grid(row=i, column=1, padx=14, pady=6)
            entries[key] = var

        def test_and_save():
            try:
                port = int(entries["port"].get().strip() or 3306)
            except ValueError:
                messagebox.showerror("Invalid port", "Port must be a number.", parent=win)
                return

            new_config = {
                "host": entries["host"].get().strip() or "localhost",
                "port": port,
                "user": entries["user"].get().strip(),
                "password": entries["password"].get(),
                "database": entries["database"].get().strip(),
            }

            ok, err = self.db.test(new_config)
            if not ok:
                messagebox.showerror("Connection failed",
                                     f"Could not connect:\n\n{err}", parent=win)
                return

            self.db.config = new_config
            save_db_config(new_config)
            messagebox.showinfo("Connected",
                                "Connection successful and saved.", parent=win)
            win.destroy()
            self.refresh_table()

        btns = tk.Frame(win, bg="#f2f4f7")
        btns.grid(row=len(fields) + 1, column=0, columnspan=2, pady=16)
        ttk.Button(btns, text="Test & Save", style="Accent.TButton",
                   command=test_and_save).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="left", padx=6)

    # ============================================================
    #  Actions
    # ============================================================
    def add_entry(self):
        data = {k: v.get().strip() for k, v in self.vars.items()}

        # Required fields — everything except vehicle_number and purpose.
        required = {
            "visitor_name": "Visitor Name",
            "phone": "Phone",
            "pass_type": "Pass Type",
            "person_to_meet": "Person to Meet",
            "department": "Department",
        }
        missing = [label for key, label in required.items() if not data[key]]
        if missing:
            messagebox.showwarning(
                "Missing data",
                "Please fill in these required field(s):\n\n- " + "\n- ".join(missing),
            )
            return

        # Phone must be exactly 10 digits, numbers only.
        if not (data["phone"].isdigit() and len(data["phone"]) == 10):
            messagebox.showwarning(
                "Invalid phone",
                "Phone number must be exactly 10 digits (numbers only).",
            )
            return

        try:
            self.db.add_entry(data)
        except Error as e:
            messagebox.showerror("Database error", str(e))
            return

        for k, v in self.vars.items():
            if k != "pass_type":
                v.set("")
        self.vars["pass_type"].set(PASS_TYPES[0])
        self.refresh_table()

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("No selection", "Select a row first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def mark_exit(self):
        entry_id = self._selected_id()
        if entry_id is None:
            return
        try:
            changed = self.db.mark_exit(entry_id)
        except Error as e:
            messagebox.showerror("Database error", str(e))
            return
        if changed == 0:
            messagebox.showinfo("Already out", "This person is already marked OUT.")
        self.refresh_table()

    def delete_entry(self):
        entry_id = self._selected_id()
        if entry_id is None:
            return
        if not messagebox.askyesno("Confirm", f"Delete entry #{entry_id}?"):
            return
        try:
            self.db.delete_entry(entry_id)
        except Error as e:
            messagebox.showerror("Database error", str(e))
            return
        self.refresh_table()

    def _reset_search(self):
        self.search_var.set("")
        self.filter_var.set("All")
        self.refresh_table()

    def refresh_table(self):
        try:
            rows = self.db.fetch_entries(self.search_var.get().strip(),
                                         self.filter_var.get())
            stats = self.db.stats()
        except Error as e:
            # Don't crash or spam popups — just report it in the status bar so
            # the user can open "DB Settings" and fix the connection.
            self.tree.delete(*self.tree.get_children())
            self.status.config(
                text=f"\u26A0  Not connected to database — click 'DB Settings' to fix.  ({e})"
            )
            return

        self.tree.delete(*self.tree.get_children())
        for r in rows:
            entry_time = r[7].strftime("%Y-%m-%d %H:%M") if r[7] else ""
            exit_time = r[8].strftime("%Y-%m-%d %H:%M") if r[8] else "-"
            display = (r[0], r[1], r[2] or "", r[3], r[4] or "", r[5] or "",
                       r[6] or "", entry_time, exit_time, r[9])
            tag = "in" if r[9] == "IN" else "out"
            self.tree.insert("", "end", values=display, tags=(tag,))

        self.status.config(
            text=f"Connected to {self.db.config['host']}  |  Today  "
                 f"Inside: {stats['inside']}   Exited: {stats['exited']}   "
                 f"Total: {stats['total']}   |  Showing {len(rows)} record(s)"
        )


# ==================================================================
if __name__ == "__main__":
    database = Database(load_db_config())
    app = GatePassApp(database)
    app.mainloop()
