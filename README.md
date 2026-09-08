# Gate Pass Management System

A desktop application for managing and logging entries at an office gate. It is
built with **Python (Tkinter)** for the interactive interface and **MySQL** for
storage, letting a gatekeeper or receptionist register everyone who enters the
premises, record when they leave, and search through the day's log in real time.

The database connection is fully configurable from inside the app, so the same
program can point at a local MySQL, another machine on the network, or an online
database — without editing code or rebuilding.

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
   and a status bar shows the connected database along with today's live counts
   of who is inside, who has exited, and the total for the day.

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
- **Switchable database** — change the host / IP / port / credentials from
  inside the app via the *DB Settings* button; settings are saved and reused

## Tech Stack

- **Python 3**
- **Tkinter** — graphical user interface
- **MySQL** — database, accessed via `mysql-connector-python`

## Database

The app uses a single table, `gate_entries`, inside a `gate_pass_db` database.
Each row represents one gate entry, including the visitor's details, entry and
exit timestamps, and current status. The schema is provided in
`gate_pass_schema.sql`.

Connection details are stored in a `config.ini` file kept next to the app (it is
created automatically on first run). You normally never edit this by hand — the
in-app *DB Settings* dialog manages it for you.

## Connecting a Database

### Step 1 — Create the database

On the machine (or server) that will host MySQL, run the schema once to create
the `gate_pass_db` database and its table:

```
mysql -u root -p < gate_pass_schema.sql
```

### Step 2 — Connect from the app

Launch the app and click the **DB Settings** button in the toolbar. Fill in the
five fields and click **Test & Save**. The app verifies the connection before
saving, so you get immediate feedback if anything is wrong. Use whichever of the
following matches your setup:

**Local database (same computer)**
- Host / IP: `localhost`
- Port: `3306`
- User / Password: your MySQL login
- Database: `gate_pass_db`

**Another computer on the same network**
- Host / IP: that machine's IP address, e.g. `192.168.1.50`
- Port: `3306`
- User / Password / Database: as configured on that server

  The host machine's MySQL must allow remote connections, the user must be
  granted access from the connecting machines, and port `3306` must be open in
  its firewall.

**Online / cloud database**
- Host / IP: the hostname your provider gives you
- Port: the port your provider gives you (often `3306`)
- User / Password / Database: the credentials issued by the provider

Once saved, the connection is remembered for next time, and the status bar shows
which host you are connected to. You can switch databases again at any point from
the same dialog.

> If the app starts and cannot reach the saved database, it does not crash — the
> status bar shows a "Not connected" message so you can open **DB Settings** and
> correct it.

## Getting Started

1. Install the MySQL connector:
   ```
   pip install mysql-connector-python
   ```
2. Create the database and table:
   ```
   mysql -u root -p < gate_pass_schema.sql
   ```
3. Run the app:
   ```
   python gate_pass_app.py
   ```
4. Click **DB Settings**, enter your connection details, and click **Test & Save**.

## Requirements

- Python 3.x
- MySQL Server (local, networked, or cloud-hosted)
- `mysql-connector-python`
