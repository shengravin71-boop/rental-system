from flask import Flask, request, redirect, render_template_string, Response
import psycopg2
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def create_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenants (
            id SERIAL PRIMARY KEY,
            name TEXT,
            nrc TEXT,
            address TEXT,
            phone TEXT,
            unit TEXT,
            start_date TEXT,
            end_date TEXT,
            rent INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


def get_status(end_date):
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        days = (end - datetime.today().date()).days
    except:
        return "Invalid Date", 9999, "normal"

    if days < 0:
        return f"Expired {-days}d", days, "expired"
    elif days <= 7:
        return f"{days}d left", days, "warning"
    else:
        return f"{days}d left", days, "normal"


create_table()


@app.route("/")
def home():
    search = request.args.get("search", "").lower()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tenants")
    tenants = cur.fetchall()
    cur.close()
    conn.close()

    filtered = []
    for t in tenants:
        text = " ".join([str(x) for x in t]).lower()
        if search in text:
            filtered.append(t)

    filtered.sort(key=lambda x: get_status(x[7])[1])

    total_month = sum([(t[8] or 0) for t in filtered])

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
            body { font-family: Arial; background:#f4f4f4; padding:30px; }
            h1 { text-align:center; }
            .stats { text-align:center; font-weight:bold; margin-bottom:15px; }
            .btn { padding:10px 18px; color:white; text-decoration:none; margin:5px; display:inline-block; border:none; cursor:pointer; }
            .green-btn { background:#4CAF50; }
            .blue-btn { background:#2196F3; }
            input { padding:10px; width:320px; margin:5px; }
            table { width:100%; border-collapse:collapse; background:white; margin-top:15px; }
            th, td { border:1px solid #ccc; padding:12px; text-align:center; }
            th { background:#333; color:white; }
            tr { cursor:pointer; }
            .normal { background:#ccffcc; }
            .warning { background:#fff0b3; }
            .expired { background:#ffb3b3; }
        </style>
    </head>
    <body>
        <h1>Rental Management System</h1>

        <div class="stats">
            Current Tenants: {{ count }} &nbsp;&nbsp;&nbsp;
            Monthly Income: {{ monthly }} MMK &nbsp;&nbsp;&nbsp;
            Estimated Yearly Income: {{ yearly }} MMK
        </div>

        <div style="text-align:center;">
            <a class="btn green-btn" href="/add">Add Tenant</a>
            <a class="btn blue-btn" href="/backup">Backup Data</a>
        </div>

        <form style="text-align:center;" method="GET" action="/">
            <input name="search" placeholder="Search tenant, unit, phone..." value="{{ search }}">
            <button class="btn blue-btn" type="submit">Search</button>
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

        <p style="text-align:center;"><b>Click a tenant to view, edit, or delete.</b></p>
    </body>
    </html>
    """, rows=rows, count=len(filtered), monthly=f"{total_month:,}", yearly=f"{total_month * 12:,}", search=search)


@app.route("/add", methods=["GET", "POST"])
def add_tenant():
    if request.method == "POST":
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tenants
            (name, nrc, address, phone, unit, start_date, end_date, rent)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            request.form["name"],
            request.form["nrc"],
            request.form["address"],
            request.form["phone"],
            request.form["unit"],
            request.form["start_date"],
            request.form["end_date"],
            int(request.form["rent"] or 0)
        ))
        conn.commit()
        cur.close()
        conn.close()
        return redirect("/")

    return tenant_form("Add Tenant", "/add")


@app.route("/tenant/<int:tenant_id>")
def tenant_detail(tenant_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tenants WHERE id=%s", (tenant_id,))
    t = cur.fetchone()
    cur.close()
    conn.close()

    if not t:
        return redirect("/")

    status, days, color = get_status(t[7])

    return render_template_string("""
    <html>
    <head>
        <title>Tenant Detail</title>
        <style>
            body { font-family:Arial; background:#f4f4f4; padding:30px; }
            .box { background:white; padding:25px; max-width:600px; margin:auto; border-radius:8px; }
            .btn { padding:10px 18px; color:white; text-decoration:none; display:inline-block; margin:5px; }
            .green { background:#4CAF50; }
            .red { background:#f44336; }
            .gray { background:#777; }
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
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tenants WHERE id=%s", (tenant_id,))
    t = cur.fetchone()

    if not t:
        cur.close()
        conn.close()
        return redirect("/")

    if request.method == "POST":
        cur.execute("""
            UPDATE tenants
            SET name=%s, nrc=%s, address=%s, phone=%s, unit=%s, start_date=%s, end_date=%s, rent=%s
            WHERE id=%s
        """, (
            request.form["name"],
            request.form["nrc"],
            request.form["address"],
            request.form["phone"],
            request.form["unit"],
            request.form["start_date"],
            request.form["end_date"],
            int(request.form["rent"] or 0),
            tenant_id
        ))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(f"/tenant/{tenant_id}")

    cur.close()
    conn.close()
    return tenant_form("Edit Tenant", f"/edit/{tenant_id}", t)


@app.route("/delete/<int:tenant_id>")
def delete_tenant(tenant_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM tenants WHERE id=%s", (tenant_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect("/")


@app.route("/backup")
def backup_data():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tenants ORDER BY id")
    tenants = cur.fetchall()
    cur.close()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "NRC", "Address", "Phone", "Unit", "Start", "End", "Rent"])
    writer.writerows(tenants)

    filename = f"rental_backup_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.csv"

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def tenant_form(title, action, tenant=None):
    values = {
        "name": tenant[1] if tenant else "",
        "nrc": tenant[2] if tenant else "",
        "address": tenant[3] if tenant else "",
        "phone": tenant[4] if tenant else "",
        "unit": tenant[5] if tenant else "",
        "start_date": tenant[6] if tenant else "",
        "end_date": tenant[7] if tenant else "",
        "rent": tenant[8] if tenant else ""
    }

    return render_template_string("""
    <html>
    <head>
        <title>{{ title }}</title>
        <style>
            body { font-family:Arial; background:#f4f4f4; padding:30px; }
            .box { background:white; padding:25px; max-width:600px; margin:auto; border-radius:8px; }
            input { width:100%; padding:10px; margin:8px 0; }
            button { padding:10px 18px; background:#4CAF50; color:white; border:none; cursor:pointer; }
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
            <br>
            <a href="/">Back</a>
        </div>
    </body>
    </html>
    """, title=title, action=action, values=values)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
