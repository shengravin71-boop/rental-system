from flask import Flask, render_template_string, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

DB = "rental.db"


def create_table():
    conn = sqlite3.connect(DB)
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


def get_tenants():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("SELECT * FROM tenants")
    tenants = c.fetchall()

    conn.close()

    return tenants


@app.route("/")
def home():
    tenants = get_tenants()

    total_month = 0

    html = """

    <html>
    <head>
        <title>Rental Management</title>

        <style>

        body{
            font-family: Arial;
            background:#f2f2f2;
            padding:30px;
        }

        h1{
            color:#333;
        }

        table{
            width:100%;
            border-collapse:collapse;
            background:white;
        }

        th, td{
            padding:12px;
            border:1px solid #ccc;
            text-align:center;
        }

        th{
            background:#444;
            color:white;
        }

        .green{
            background:#ccffcc;
        }

        .yellow{
            background:#fff0b3;
        }

        .red{
            background:#ffb3b3;
        }

        input{
            width:100%;
            padding:10px;
            margin-bottom:10px;
        }

        button{
            padding:10px 20px;
            background:#4CAF50;
            color:white;
            border:none;
            cursor:pointer;
        }

        </style>

    </head>

    <body>

    <h1>Rental Management System</h1>

    <a href="/add">
        <button>Add Tenant</button>
    </a>

    <br><br>

    <table>

    <tr>
        <th>Unit</th>
        <th>Name</th>
        <th>Phone</th>
        <th>Contract End</th>
        <th>Status</th>
    </tr>

    """

    for t in tenants:

        end = datetime.strptime(t[7], "%Y-%m-%d")
        days = (end - datetime.today()).days

        if days < 0:
            color = "red"
            status = f"Expired {-days} days"
        elif days <= 7:
            color = "yellow"
            status = f"{days} days left"
        else:
            color = "green"
            status = f"{days} days left"

        total_month += t[8]

        html += f"""

        <tr class="{color}">
            <td>{t[5]}</td>
            <td>{t[1]}</td>
            <td>{t[4]}</td>
            <td>{t[7]}</td>
            <td>{status}</td>
        </tr>

        """

    html += f"""

    </table>

    <br>

    <h3>Current Tenants: {len(tenants)}</h3>
    <h3>Monthly Income: {total_month:,} MMK</h3>
    <h3>Estimated Yearly Income: {total_month * 12:,} MMK</h3>

    </body>
    </html>

    """

    return render_template_string(html)


@app.route("/add", methods=["GET", "POST"])
def add():

    if request.method == "POST":

        data = (
            request.form["name"],
            request.form["nrc"],
            request.form["address"],
            request.form["phone"],
            request.form["unit"],
            request.form["start"],
            request.form["end"],
            int(request.form["rent"])
        )

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("""
        INSERT INTO tenants
        (name,nrc,address,phone,unit,start_date,end_date,rent)
        VALUES (?,?,?,?,?,?,?,?)
        """, data)

        conn.commit()
        conn.close()

        return redirect("/")

    return """

    <html>
    <body style="font-family:Arial;padding:30px;">

    <h1>Add Tenant</h1>

    <form method="POST">

    <input name="name" placeholder="Tenant Name"><br>
    <input name="nrc" placeholder="NRC / ID"><br>
    <input name="address" placeholder="Address"><br>
    <input name="phone" placeholder="Phone"><br>
    <input name="unit" placeholder="Rental Unit"><br>
    <input name="start" placeholder="Contract Start YYYY-MM-DD"><br>
    <input name="end" placeholder="Contract End YYYY-MM-DD"><br>
    <input name="rent" placeholder="Monthly Rent"><br>

    <button type="submit">Save Tenant</button>

    </form>

    </body>
    </html>

    """


create_table()

app.run(host="0.0.0.0", port=5000)