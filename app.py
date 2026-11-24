from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
from datetime import datetime
import math

app = Flask(__name__)

# 1. Database Setup (With Discount Column)
def init_db():
    conn = sqlite3.connect('hospital_v4.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            disease TEXT,
            doctor TEXT,
            room_type TEXT,
            daily_charge INTEGER,
            medicine_charge INTEGER DEFAULT 0,
            discount INTEGER DEFAULT 0,
            entry_time TEXT,
            exit_time TEXT,
            days_stayed INTEGER,
            total_bill INTEGER,
            paid_amount INTEGER DEFAULT 0,
            balance_due INTEGER DEFAULT 0,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 2. Modern Dashboard UI
HTML_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>City Care Hospital - Billing & Management System</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #f0f4f8; color: #333; }
        .container { max-width: 1400px; margin: auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.08); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #004085; padding-bottom: 15px; margin-bottom: 20px; }
        .header h1 { color: #004085; margin: 0; font-size: 24px; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 25px; }
        .stat-card { padding: 15px; border-radius: 8px; color: white; text-align: center; box-shadow: 0 3px 8px rgba(0,0,0,0.1); }
        .stat-card h2 { margin: 5px 0 0; font-size: 24px; }
        .stat-card p { margin: 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; }
        .bg-blue { background: linear-gradient(135deg, #0062cc, #004085); }
        .bg-orange { background: linear-gradient(135deg, #f39c12, #d35400); }
        .bg-green { background: linear-gradient(135deg, #28a745, #1e7e34); }
        .bg-teal { background: linear-gradient(135deg, #17a2b8, #117a8b); }
        .bg-red { background: linear-gradient(135deg, #dc3545, #a71d2a); }
        
        .form-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; background: #f8f9fa; padding: 18px; border-radius: 8px; border: 1px solid #dee2e6; }
        input, select { padding: 10px; border: 1px solid #ced4da; border-radius: 5px; width: 94%; font-size: 14px; }
        button { padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .btn-add { background-color: #28a745; color: white; grid-column: span 3; font-size: 15px; transition: 0.2s; }
        .btn-add:hover { background-color: #218838; }
        .btn-search { background-color: #007bff; color: white; }
        .btn-update { background-color: #007bff; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin-top: 3px; }
        .btn-exit { background-color: #e67e22; color: white; padding: 5px 9px; text-decoration: none; border-radius: 4px; font-size: 11px; display: inline-block; font-weight: bold; }
        .btn-pay { background-color: #28a745; color: white; padding: 4px 7px; border-radius: 4px; font-size: 11px; }
        .btn-receipt { background-color: #17a2b8; color: white; padding: 5px 8px; text-decoration: none; border-radius: 4px; font-size: 11px; display: inline-block; }
        .btn-delete { background-color: #dc3545; color: white; padding: 5px 8px; text-decoration: none; border-radius: 4px; font-size: 11px; display: inline-block; margin-left: 3px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
        th, td { border: 1px solid #dee2e6; padding: 9px; text-align: center; }
        th { background-color: #004085; color: white; }
        tr:hover { background-color: #f1f5f9; }
        .badge-admitted { background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 11px; }
        .badge-discharged { background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 11px; }
        .small-input { width: 55px; padding: 4px; font-size: 11px; margin-bottom: 2px; }
        .due-text { color: #dc3545; font-weight: bold; }
        .paid-text { color: #28a745; font-weight: bold; }
        .disc-text { color: #6f42c1; font-size: 11px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 CITY CARE HOSPITAL — PATIENT & BILLING PORTAL</h1>
            <span style="color:#666; font-size:14px;">24x7 Admission, Live Billing, Discount & Due Management</span>
        </div>

        <div class="stats-grid">
            <div class="stat-card bg-blue">
                <p>Total Patients</p>
                <h2>{{ stats.total }}</h2>
            </div>
            <div class="stat-card bg-orange">
                <p>Currently Admitted</p>
                <h2>{{ stats.admitted }}</h2>
            </div>
            <div class="stat-card bg-green">
                <p>Discharged</p>
                <h2>{{ stats.discharged }}</h2>
            </div>
            <div class="stat-card bg-teal">
                <p>Total Collected</p>
                <h2>₹{{ stats.collected }}</h2>
            </div>
            <div class="stat-card bg-red">
                <p>Total Balance Due</p>
                <h2>₹{{ stats.pending }}</h2>
            </div>
        </div>

        <h3>➕ New Patient Admission (Entry)</h3>
        <form method="POST" action="/add" class="form-grid">
            <input type="text" name="name" placeholder="Patient Full Name" required>
            <input type="number" name="age" placeholder="Age (Years)" required>
            <select name="gender" required>
                <option value="" disabled selected>Select Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
            </select>
            <input type="text" name="phone" placeholder="Mobile Number" required>
            <input type="text" name="disease" placeholder="Disease / Symptoms" required>
            <input type="text" name="doctor" placeholder="Doctor Name (e.g., Dr. Verma)" required>
            <select name="room_type" required>
                <option value="General Ward">General Ward</option>
                <option value="Semi-Private">Semi-Private Room</option>
                <option value="Private AC">Private AC Room</option>
                <option value="ICU">ICU / Critical Care</option>
            </select>
            <input type="number" name="daily_charge" placeholder="Room Charge/Day (₹)" required>
            <input type="number" name="advance_paid" placeholder="Advance Paid at Entry (₹)" value="0" min="0" required>
            <button type="submit" class="btn-add">Admit Patient & Save Advance</button>
        </form>

        <h3>🔍 Patient Records & Live Billing Ledger</h3>
        <form method="GET" action="/" style="margin-bottom: 12px;">
            <input type="text" name="search" placeholder="Search by Name, Phone, or Doctor..." value="{{ search_query }}" style="width: 300px;">
            <button type="submit" class="btn-search">Search</button>
            <a href="/" style="margin-left:12px; text-decoration:none; color:#0056b3; font-weight:bold;">Reset</a>
        </form>

        <table>
            <tr>
                <th>ID</th>
                <th>Patient Info</th>
                <th>Ward & Doctor</th>
                <th>Entry & Exit Time</th>
                <th>Days</th>
                <th>Net Bill</th>
                <th>Paid Amount</th>
                <th>Balance Due</th>
                <th>Action / Status</th>
            </tr>
            {% for p in patients %}
            <tr>
                <td><b>#{{ p.id }}</b></td>
                <td><b>{{ p.name }}</b><br><small>{{ p.age }} Yrs | {{ p.gender }}<br>📞 {{ p.phone }}</small></td>
                <td><span style="font-weight:bold; color:#0056b3;">{{ p.room_type }} ({{ p.disease }})</span><br><small>{{ p.doctor }}</small></td>
                <td>
                    <small><b>In:</b> {{ p.entry_time }}</small><br>
                    <small><b>Out:</b> {{ p.exit_time if p.exit_time else 'Active' }}</small>
                </td>
                <td><b>{{ p.days_stayed }}d</b></td>
                <td>
                    <b>₹{{ p.total_bill }}</b><br>
                    <small style="color:#666;">Med: ₹{{ p.medicine_charge }}</small>
                    {% if p.discount > 0 %}
                        <br><span class="disc-text">Disc: -₹{{ p.discount }}</span>
                    {% endif %}
                </td>
                <td class="paid-text">₹{{ p.paid_amount }}</td>
                <td class="{{ 'due-text' if p.balance_due > 0 else 'paid-text' }}">
                    {{ '₹' ~ p.balance_due if p.balance_due > 0 else '₹0 (Clear)' }}
                </td>
                <td>
                    {% if p.status == 'Admitted' %}
                        <span class="badge-admitted">Admitted</span>
                        <form method="POST" action="/add_charges/{{ p.id }}" style="margin-top:6px; background:#f8f9fa; padding:6px; border-radius:5px; border:1px solid #ddd;">
                            <input type="number" name="add_med" placeholder="+Med ₹" class="small-input" value="0" min="0" title="Add Medicine Charge">
                            <input type="number" name="add_disc" placeholder="Disc ₹" class="small-input" value="0" min="0" title="Give Discount ₹">
                            <input type="number" name="add_pay" placeholder="+Pay ₹" class="small-input" value="0" min="0" title="Add Payment Received"><br>
                            <button type="submit" class="btn-update">Update Bill / Disc / Pay</button>
                        </form>
                        <div style="margin-top:6px;">
                            <a href="/discharge/{{ p.id }}" class="btn-exit" onclick="return confirm('Discharge patient and finalize bill?');">Discharge</a>
                            <a href="/receipt/{{ p.id }}" target="_blank" class="btn-receipt">🧾</a>
                            <a href="/delete/{{ p.id }}" class="btn-delete" onclick="return confirm('Delete this patient record?');">🗑️</a>
                        </div>
                    {% else %}
                        <span class="badge-discharged">Discharged</span>
                        {% if p.balance_due > 0 %}
                        <form method="POST" action="/pay_due/{{ p.id }}" style="margin-top:5px;">
                            <input type="number" name="due_payment" placeholder="Due ₹" class="small-input" max="{{ p.balance_due }}" min="1" required>
                            <button type="submit" class="btn-pay">+ Pay</button>
                        </form>
                        {% endif %}
                        <div style="margin-top:5px;">
                            <a href="/receipt/{{ p.id }}" target="_blank" class="btn-receipt">🧾 Bill</a>
                            <a href="/delete/{{ p.id }}" class="btn-delete" onclick="return confirm('Delete this patient record?');">🗑️</a>
                        </div>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

# 3. Real Hospital Tax Invoice & Accountant Sign Template (With Discount Row)
RECEIPT_PAGE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Tax Invoice - City Care Hospital (#{{ p.id }})</title>
    <link href="https://googleapis.com" rel="stylesheet">
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background-color: #e9ecef; color: #222; }
        .invoice-container { max-width: 760px; margin: auto; background: white; padding: 35px 40px; border: 1px solid #bbb; box-shadow: 0 5px 25px rgba(0,0,0,0.15); position: relative; }
        .hosp-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #004085; padding-bottom: 15px; }
        .hosp-title h1 { margin: 0; color: #004085; font-size: 26px; letter-spacing: 1px; }
        .hosp-title p { margin: 3px 0; font-size: 12.5px; color: #555; }
        .invoice-meta { text-align: right; font-size: 13px; }
        .invoice-meta h3 { margin: 0 0 5px; color: #dc3545; font-size: 18px; text-transform: uppercase; }
        .patient-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background: #f8f9fa; padding: 14px; border: 1px solid #dee2e6; margin: 18px 0; font-size: 13.5px; }
        .patient-grid div p { margin: 4px 0; }
        .bill-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        .bill-table th { background-color: #004085; color: white; padding: 10px; text-align: left; }
        .bill-table td { padding: 10px; border-bottom: 1px solid #dee2e6; }
        .text-right { text-align: right !important; }
        .summary-box { width: 55%; margin-left: auto; margin-top: 15px; border-collapse: collapse; font-size: 14.5px; }
        .summary-box td { padding: 7px 10px; border-bottom: 1px solid #ddd; }
        .disc-row { color: #6f42c1; font-weight: bold; }
        .grand-total { font-size: 16px; font-weight: bold; background: #f0f4f8; color: #004085; }
        .paid-total { font-weight: bold; color: #155724; background: #d4edda; }
        .due-total { font-weight: bold; color: #721c24; background: #f8d7da; }
        .stamp-paid { position: absolute; bottom: 145px; left: 110px; border: 4px solid #28a745; color: #28a745; font-size: 28px; font-weight: 900; padding: 6px 22px; text-transform: uppercase; letter-spacing: 3px; transform: rotate(-14deg); opacity: 0.85; border-radius: 8px; pointer-events: none; }
        .stamp-due { position: absolute; bottom: 145px; left: 90px; border: 4px solid #dc3545; color: #dc3545; font-size: 22px; font-weight: 900; padding: 6px 18px; text-transform: uppercase; letter-spacing: 2px; transform: rotate(-14deg); opacity: 0.85; border-radius: 8px; pointer-events: none; }
        .footer-sign { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 65px; padding-top: 15px; border-top: 1px dashed #aaa; font-size: 13px; }
        .sign-area { text-align: center; width: 240px; }
        .digital-sign { font-family: 'Great Vibes', cursive; font-size: 32px; color: #003366; margin-bottom: -8px; min-height: 38px; }
        .sign-line { border-top: 1px solid #333; padding-top: 5px; font-weight: bold; }
        .controls-bar { max-width: 760px; margin: 0 auto 15px; background: #fff3cd; padding: 12px 18px; border-radius: 8px; border: 1px solid #ffeeba; display: flex; gap: 10px; align-items: center; justify-content: space-between; }
        .controls-bar input { padding: 7px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; width: 210px; }
        .btn-print { background: #28a745; color: white; border: none; padding: 9px 18px; font-size: 14px; font-weight: bold; border-radius: 5px; cursor: pointer; }
        @media print { body { background: white; margin: 0; } .invoice-container { box-shadow: none; border: 1px solid #000; } .controls-bar { display: none; } }
    </style>
</head>
<body>
    <div class="controls-bar">
        <div>
            <b>✍️ Accountant Sign:</b>
            <input type="text" id="accInput" placeholder="Enter Accountant Name..." onkeyup="updateSign()">
        </div>
        <button class="btn-print" onclick="window.print()">🖨️ Print Official Bill</button>
    </div>

    <div class="invoice-container">
        {% if p.balance_due == 0 %}
            <div class="stamp-paid">PAID IN FULL</div>
        {% else %}
            <div class="stamp-due">BALANCE DUE</div>
        {% endif %}

        <div class="hosp-header">
            <div class="hosp-title">
                <h1>🏥 CITY CARE HOSPITAL</h1>
                <p>Multi-Specialty & Trauma Center (24x7 Emergency Services)</p>
                <p>Main Road, Civil Lines | Helpline: +91-98765-43210</p>
                <p>Reg No: CCH/2026/8841 | GSTIN: 20AABCC1234D1Z5</p>
            </div>
            <div class="invoice-meta">
                <h3>TAX INVOICE / RECEIPT</h3>
                <p><b>Invoice No:</b> INV-2026-00{{ p.id }}</p>
                <p><b>Patient ID:</b> #{{ p.id }}</p>
                <p><b>Status:</b> {{ p.status }}</p>
            </div>
        </div>

        <div class="patient-grid">
            <div>
                <p><b>Patient Name:</b> {{ p.name }}</p>
                <p><b>Age / Gender:</b> {{ p.age }} Years / {{ p.gender }}</p>
                <p><b>Contact No:</b> {{ p.phone }}</p>
                <p><b>Diagnosis:</b> {{ p.disease }}</p>
            </div>
            <div>
                <p><b>Consulting Doctor:</b> {{ p.doctor }}</p>
                <p><b>Ward / Room Type:</b> {{ p.room_type }}</p>
                <p><b>Admission Time:</b> {{ p.entry_time }}</p>
                <p><b>Discharge Time:</b> {{ p.exit_time if p.exit_time else 'Currently Admitted' }}</p>
            </div>
        </div>

        <table class="bill-table">
            <thead>
                <tr>
                    <th>Sr.</th>
                    <th>Description of Services</th>
                    <th class="text-right">Rate (₹)</th>
                    <th class="text-right">Qty / Days</th>
                    <th class="text-right">Amount (₹)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>{{ p.room_type }} Bed & Nursing Charges</td>
                    <td class="text-right">{{ p.daily_charge }}.00</td>
                    <td class="text-right">{{ p.days_stayed }}</td>
                    <td class="text-right">{{ p.days_stayed * p.daily_charge }}.00</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Pharmacy, Medicines & Lab Investigations</td>
                    <td class="text-right">{{ p.medicine_charge }}.00</td>
                    <td class="text-right">1</td>
                    <td class="text-right">{{ p.medicine_charge }}.00</td>
                </tr>
                <tr>
                    <td>3</td>
                    <td>Doctor Consultation & Registration Fee</td>
                    <td class="text-right">500.00</td>
                    <td class="text-right">1</td>
                    <td class="text-right">500.00</td>
                </tr>
            </tbody>
        </table>

        <table class="summary-box">
            <tr>
                <td>Sub-Total Amount:</td>
                <td class="text-right">₹{{ p.total_bill + p.discount }}.00</td>
            </tr>
            {% if p.discount > 0 %}
            <tr class="disc-row">
                <td>Hospital Discount Given:</td>
                <td class="text-right">- ₹{{ p.discount }}.00</td>
            </tr>
            {% endif %}
            <tr class="grand-total">
                <td>Net Payable Bill:</td>
                <td class="text-right">₹{{ p.total_bill }}.00</td>
            </tr>
            <tr class="paid-total">
                <td>Amount Received (Paid):</td>
                <td class="text-right">₹{{ p.paid_amount }}.00</td>
            </tr>
            <tr class="due-total">
                <td>Net Balance Due:</td>
                <td class="text-right">₹{{ p.balance_due }}.00</td>
            </tr>
        </table>

        <div class="footer-sign">
            <div>
                <p style="margin:0; color:#555;">* Computer generated medical invoice.</p>
                <p style="margin:3px 0 0; color:#555;">* Thank you for choosing City Care Hospital.</p>
            </div>
            <div class="sign-area">
                <div class="digital-sign" id="signDisplay">Authorized Sign</div>
                <div class="sign-line">Accountant / Cashier Signature</div>
                <div style="font-size:11px; color:#555; margin-top:2px;">Status: <b>{{ 'PAID' if p.balance_due == 0 else 'PARTIAL / DUE' }}</b></div>
            </div>
        </div>
    </div>

    <script>
        function updateSign() {
            let name = document.getElementById("accInput").value;
            document.getElementById("signDisplay").innerText = name ? name : "Authorized Sign";
        }
    </script>
</body>
</html>
'''

def get_db():
    conn = sqlite3.connect('hospital_v4.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/', methods=['GET'])
def home():
    search_query = request.args.get('search', '')
    conn = get_db()
    cursor = conn.cursor()
    
    total_patients = cursor.execute("SELECT COUNT(*) AS val FROM patients").fetchone()['val']
    admitted_count = cursor.execute("SELECT COUNT(*) AS val FROM patients WHERE status = 'Admitted'").fetchone()['val']
    discharged_count = cursor.execute("SELECT COUNT(*) AS val FROM patients WHERE status = 'Discharged'").fetchone()['val']
    total_collected = cursor.execute("SELECT SUM(paid_amount) AS val FROM patients").fetchone()['val'] or 0
    total_pending = cursor.execute("SELECT SUM(balance_due) AS val FROM patients").fetchone()['val'] or 0
    
    stats = {
        'total': total_patients,
        'admitted': admitted_count,
        'discharged': discharged_count,
        'collected': total_collected,
        'pending': total_pending
    }
    
    if search_query:
        patients = cursor.execute("SELECT * FROM patients WHERE name LIKE ? OR doctor LIKE ? OR phone LIKE ? ORDER BY id DESC", 
                                  ('%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%')).fetchall()
    else:
        patients = cursor.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(HTML_PAGE, patients=patients, search_query=search_query, stats=stats)

@app.route('/add', methods=['POST'])
def add_patient():
    name = request.form['name']
    age = int(request.form['age'])
    gender = request.form['gender']
    phone = request.form['phone']
    disease = request.form['disease']
    doctor = request.form['doctor']
    room_type = request.form['room_type']
    daily_charge = int(request.form['daily_charge'])
    advance_paid = int(request.form.get('advance_paid', 0))
    entry_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    initial_bill = daily_charge + 500
    balance_due = max(0, initial_bill - advance_paid)
    
    conn = get_db()
    conn.execute('''
        INSERT INTO patients (name, age, gender, phone, disease, doctor, room_type, daily_charge, medicine_charge, discount, entry_time, exit_time, days_stayed, total_bill, paid_amount, balance_due, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, gender, phone, disease, doctor, room_type, daily_charge, 0, 0, entry_time, None, 1, initial_bill, advance_paid, balance_due, 'Admitted'))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/add_charges/<int:patient_id>', methods=['POST'])
def add_charges(patient_id):
    add_med = int(request.form.get('add_med', 0))
    add_disc = int(request.form.get('add_disc', 0))
    add_pay = int(request.form.get('add_pay', 0))
    
    conn = get_db()
    record = conn.execute("SELECT medicine_charge, discount, total_bill, paid_amount FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if record:
        new_med = record['medicine_charge'] + add_med
        new_disc = record['discount'] + add_disc
        new_bill = max(0, record['total_bill'] + add_med - add_disc)
        new_paid = record['paid_amount'] + add_pay
        new_balance = max(0, new_bill - new_paid)
        
        conn.execute('''
            UPDATE patients 
            SET medicine_charge = ?, discount = ?, total_bill = ?, paid_amount = ?, balance_due = ?
            WHERE id = ?
        ''', (new_med, new_disc, new_bill, new_paid, new_balance, patient_id))
        conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/discharge/<int:patient_id>')
def discharge_patient(patient_id):
    conn = get_db()
    record = conn.execute("SELECT entry_time, daily_charge, medicine_charge, discount, paid_amount FROM patients WHERE id = ?", (patient_id,)).fetchone()
    
    if record:
        entry_dt = datetime.strptime(record['entry_time'], "%Y-%m-%d %H:%M:%S")
        exit_dt = datetime.now()
        exit_time = exit_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        duration = exit_dt - entry_dt
        days_stayed = max(1, math.ceil(duration.total_seconds() / 86400))
        doctor_fee = 500
        
        gross_bill = (days_stayed * record['daily_charge']) + record['medicine_charge'] + doctor_fee
        total_bill = max(0, gross_bill - record['discount'])
        balance_due = max(0, total_bill - record['paid_amount'])
        
        conn.execute('''
            UPDATE patients 
            SET exit_time = ?, days_stayed = ?, total_bill = ?, balance_due = ?, status = 'Discharged'
            WHERE id = ?
        ''', (exit_time, days_stayed, total_bill, balance_due, patient_id))
        conn.commit()
        
    conn.close()
    return redirect(url_for('home'))

@app.route('/pay_due/<int:patient_id>', methods=['POST'])
def pay_due(patient_id):
    due_payment = int(request.form.get('due_payment', 0))
    conn = get_db()
    record = conn.execute("SELECT total_bill, paid_amount FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if record:
        new_paid = record['paid_amount'] + due_payment
        new_balance = max(0, record['total_bill'] - new_paid)
        conn.execute("UPDATE patients SET paid_amount = ?, balance_due = ? WHERE id = ?", (new_paid, new_balance, patient_id))
        conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/delete/<int:patient_id>')
def delete_patient(patient_id):
    conn = get_db()
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('home'))

@app.route('/receipt/<int:patient_id>')
def view_receipt(patient_id):
    conn = get_db()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    if patient:
        return render_template_string(RECEIPT_PAGE, p=patient)
    return "Record not found", 404

if __name__ == '__main__':
    app.run(debug=True)