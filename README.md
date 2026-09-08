# Gate Pass Management System

A desktop application for managing and logging entries at an office gate. It is
built with **Python (Tkinter)** for the interactive interface and **MySQL** for
storage, letting a gatekeeper or receptionist register everyone who enters the
premises, record when they leave, and search through the day's log in real time.

## How It Works

The app opens as a single window with three parts: an entry form at the top, a
search/action toolbar in the middle, and a live table of records below.

1. **Register an entry** — The operator fills in the visitor's details and clicks
   *Register Entry*. The app automatically stamps the current time as the entry
   time and saves the record to MySQL with a status of `IN`.
2. **Mark an exit** — When a person leaves, the operator selects their row and
   clicks *Mark Exit*. The app records the exit time and flips the status from
   `IN` to `OUT`.
3. **Search and filter** — Records can be searched by name, phone, or the person
   being visited, and filtered by status (`IN`, `OUT`, or `All`).
4. **Track at a glance** — People currently inside are highlighted in the table,
   and a status bar shows today's live counts of who is inside, who has exited,
   and the total for the day.

All records persist in the MySQL database, so the log survives restarts and can
be queried or reported on independently.

## Features

- Register gate entries with visitor name, phone, pass type
  (Visitor / Employee / Contractor / Delivery / VIP / Interview), purpose,
  person to meet, department, and vehicle number
- Automatic entry timestamp on registration
- One-click exit logging with an automatic exit timestamp and `IN` → `OUT`
  status change
- Search records by name, phone, or person being visited
- Filter records by status (`IN` / `OUT` / `All`)
- Delete records with a confirmation prompt
- Live daily counts (inside / exited / total) in the status bar
- Color-coded table — anyone currently inside is highlighted
- **Input validation** — the phone number is required and must be exactly
  10 digits; all fields are mandatory except vehicle number and purpose

## Tech Stack

- **Python 3**
- **Tkinter** — graphical user interface
- **MySQL** — database, accessed via `mysql-connector-python`

## Database

The app uses a single table, `gate_entries`, inside a `gate_pass_db` database.
Each row represents one gate entry, including the visitor's details, entry and
exit timestamps, and current status. The schema is provided in
`gate_pass_schema.sql`.

## Getting Started

1. Install the MySQL connector:
   ```
   pip install mysql-connector-python
   ```
2. Create the database and table by running the schema:
   ```
   mysql -u root -p < gate_pass_schema.sql
   ```
3. Set your MySQL credentials in the configuration section of the app.
4. Launch the application:
   ```
   python gate_pass_app.py
   ```

## Requirements

- Python 3.x
- MySQL Server
- `mysql-connector-python`
