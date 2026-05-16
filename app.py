from flask import Flask, request, redirect, render_template_string, send_file
import sqlite3
import os
import shutil
from datetime import datetime

app = Flask(__name__)

DB = "rental.db"
BACKUP_FOLDER = "Backups"


def connect_db():
    return sqlite3.connect(DB)


def create_table():
    conn = connect_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            nrc TEXT,
            address TEXT,
            phone TEXT,
            unit TEXT,
            start_date TEXT,
            end_date TEXT,
            rent INTEGER
        )
    """)
    conn.commit()
    conn.close()


def get_status(end_date):
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - datetime.today()).days
    except:
        return "Invalid Date", 9999, "normal"

    if days < 0:
        return f"Expired {-days}d", days, "expired"
    elif days <= 7:
        return f"{days}d left", days, "warning"
    else:
        return f"{days}d left", days, "normal"


@app.route("/")
def home():
    search = request.args.get("search", "").lower()

    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tenants")
    tenants = c.fetchall()
    conn.close()

    filtered = []

    for t in tenants:
        text = " ".join([str(x) for x in t]).lower()
        if search in text:
            filtered.append(t)

    filtered.sort(key=lambda x: get_status(x[7])[1])

    total_month = sum([t[8] or 0 for t in filtered])

    rows = ""

    for t in filtered:
        status, days, color = get_status(t[7])

        rows += f"""
        <tr class="{color}" onclick="window.location='/tenant/{t[0]}'">
            <td>{t[5]}</td>
            <td>{t[1]}</td>
            <td>{t[4]}</td>
            <td>{t[7]}</td>
            <td>{status}</td>
        </tr>
        """

    return render_template_string("""
    <html>
    <head>
        <title>Rental Management System</title>
        <style>
            body {
                font-family: Arial;
                background: #f4f4f4;
                padding: 30px;
            }

            h1 {
                text-align: center;
            }

            .stats {
                display: flex;
                justify-content: center;
                gap: 40px;
                font-weight: bold;
                margin-bottom: 15px;
            }

            .top-buttons {
                text-align: center;
                margin-bottom: 15px;
            }

            button, .btn {
                padding: 10px 18px;
                border: none;
                color: white;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }

            .green-btn { background: #4CAF50; }
            .blue-btn { background: #2196F3; }
            .red-btn { background: #f44336; }
            .gray-btn { background: #777; }

            input {
                padding: 10px;
                width: 320px;
                margin: 5px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                margin-top: 15px;
            }

            th, td {
                border: 1px solid #ccc;
                padding: 12px;
                text-align: center;
            }

            th {
                background: #333;
                color: white;
            }

            tr {
                cursor: pointer;
            }

            .normal { background: #ccffcc; }
            .warning { background: #fff0b3; }
            .expired { background: #ffb3b3; }

            .hint {
                text-align: center;
                margin-top: 10px;
                font-weight: bold;
            }
        </style>
    </head>

    <body>
        <h1>Rental Management System</h1>

        <div class="stats">
            <div>Current Tenants: {{ count }}</div>
            <div>Monthly Income: {{ monthly }} MMK</div>
            <div>Estimated Yearly Income: {{ yearly }} MMK</div>
        </div>

        <div class="top-buttons">
            <a class="btn green-btn" href="/add">Add Tenant</a>
            <a class="btn blue-btn" href="/backup">Backup Data</a>
        </div>

        <form style="text-align:center;" method="GET" action="/">
            <input name="search" placeholder="Search tenant, unit, phone..." value="{{ search }}">
            <button class="blue-btn" type="submit">Search</button>
        </form>

        <table>
            <tr>
                <th>Unit</th>
                <th>Tenant Name</th>
                <th>Phone</th>
                <th>Contract End</th>
                <th>Status</th>
            </tr>
            {{ rows|safe }}
        </table>

        <div class="hint">Click a tenant to view, edit, or delete.</div>
    </body>
    </html>
    """, rows=rows, count=len(filtered), monthly=f"{total_month:,}", yearly=f"{total_month * 12:,}", search=search)


@app.route("/add", methods=["GET", "POST"])
def add_tenant():
    if request.method == "POST":
        name = request.form["name"]
        nrc = request.form["nrc"]
        address = request.form["address"]
        phone = request.form["phone"]
        unit = request.form["unit"]
        start_date = request.form["start_date"]
        end_date = request.form["end_date"]
        rent = int(request.form["rent"] or 0)

        conn = connect_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO tenants
            (name, nrc, address, phone, unit, start_date, end_date, rent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, nrc, address, phone, unit, start_date, end_date, rent))
        conn.commit()
        conn.close()

        return redirect("/")

    return tenant_form("Add Tenant", "/add")


@app.route("/tenant/<int:tenant_id>")
def tenant_detail(tenant_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,))
    t = c.fetchone()
    conn.close()

    if not t:
        return redirect("/")

    status, days, color = get_status(t[7])

    return render_template_string("""
    <html>
    <head>
        <title>Tenant Detail</title>
        <style>
            body {
                font-family: Arial;
                background: #f4f4f4;
                padding: 30px;
            }

            .box {
                background: white;
                padding: 25px;
                max-width: 600px;
                margin: auto;
                border-radius: 8px;
            }

            p {
                font-size: 16px;
            }

            .btn {
                padding: 10px 18px;
                color: white;
                text-decoration: none;
                display: inline-block;
                margin: 5px;
            }

            .green { background: #4CAF50; }
            .red { background: #f44336; }
            .gray { background: #777; }
        </style>
    </head>

    <body>
        <div class="box">
            <h1>Tenant Detail</h1>

            <p><b>Name:</b> {{ t[1] }}</p>
            <p><b>NRC / ID:</b> {{ t[2] }}</p>
            <p><b>Address:</b> {{ t[3] }}</p>
            <p><b>Phone:</b> {{ t[4] }}</p>
            <p><b>Rental Unit:</b> {{ t[5] }}</p>
            <p><b>Contract:</b> {{ t[6] }} → {{ t[7] }}</p>
            <p><b>Monthly Rent:</b> {{ rent }} MMK</p>
            <p><b>Status:</b> {{ status }}</p>

            <a class="btn green" href="/edit/{{ t[0] }}">Edit Tenant</a>
            <a class="btn red" href="/delete/{{ t[0] }}" onclick="return confirm('Delete this tenant?')">Delete Tenant</a>
            <a class="btn gray" href="/">Back</a>
        </div>
    </body>
    </html>
    """, t=t, rent=f"{t[8]:,}", status=status)


@app.route("/edit/<int:tenant_id>", methods=["GET", "POST"])
def edit_tenant(tenant_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("SELECT * FROM tenants WHERE id=?", (tenant_id,))
    t = c.fetchone()

    if not t:
        conn.close()
        return redirect("/")

    if request.method == "POST":
        data = (
            request.form["name"],
            request.form["nrc"],
            request.form["address"],
            request.form["phone"],
            request.form["unit"],
            request.form["start_date"],
            request.form["end_date"],
            int(request.form["rent"] or 0),
            tenant_id
        )

        c.execute("""
            UPDATE tenants
            SET name=?, nrc=?, address=?, phone=?, unit=?, start_date=?, end_date=?, rent=?
            WHERE id=?
        """, data)

        conn.commit()
        conn.close()

        return redirect(f"/tenant/{tenant_id}")

    conn.close()
    return tenant_form("Edit Tenant", f"/edit/{tenant_id}", t)


@app.route("/delete/<int:tenant_id>")
def delete_tenant(tenant_id):
    conn = connect_db()
    c = conn.cursor()
    c.execute("DELETE FROM tenants WHERE id=?", (tenant_id,))
    conn.commit()
    conn.close()
    return redirect("/")


@app.route("/backup")
def backup_data():
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)

    now = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    backup_file = os.path.join(BACKUP_FOLDER, f"rental_backup_{now}.db")

    shutil.copy(DB, backup_file)

    return send_file(backup_file, as_attachment=True)


def tenant_form(title, action, tenant=None):
    if tenant:
        values = {
            "name": tenant[1],
            "nrc": tenant[2],
            "address": tenant[3],
            "phone": tenant[4],
            "unit": tenant[5],
            "start_date": tenant[6],
            "end_date": tenant[7],
            "rent": tenant[8]
        }
    else:
        values = {
            "name": "",
            "nrc": "",
            "address": "",
            "phone": "",
            "unit": "",
            "start_date": "",
            "end_date": "",
            "rent": ""
        }

    return render_template_string("""
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body {
                font-family: Arial;
                background: #f4f4f4;
                padding: 30px;
            }

            .box {
                background: white;
                padding: 25px;
                max-width: 600px;
                margin: auto;
                border-radius: 8px;
            }

            input {
                width: 100%;
                padding: 10px;
                margin: 8px 0;
            }

            button {
                padding: 10px 18px;
                background: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
            }

            a {
                display: inline-block;
                margin-top: 15px;
            }
        </style>
    </head>

    <body>
        <div class="box">
            <h1>{{ title }}</h1>

            <form method="POST" action="{{ action }}">
                <input name="name" placeholder="Tenant Name" value="{{ values.name }}" required>
                <input name="nrc" placeholder="NRC / ID" value="{{ values.nrc }}">
                <input name="address" placeholder="Address" value="{{ values.address }}">
                <input name="phone" placeholder="Phone" value="{{ values.phone }}">
                <input name="unit" placeholder="Rental Unit" value="{{ values.unit }}" required>
                <input name="start_date" placeholder="Contract Start YYYY-MM-DD" value="{{ values.start_date }}">
                <input name="end_date" placeholder="Contract End YYYY-MM-DD" value="{{ values.end_date }}" required>
                <input name="rent" placeholder="Monthly Rent" value="{{ values.rent }}" required>

                <button type="submit">Save</button>
            </form>

            <a href="/">Back</a>
        </div>
    </body>
    </html>
    """, title=title, action=action, values=values)


create_table()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
