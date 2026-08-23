import sqlite3
import re
from flask import Flask, render_template, request, redirect, url_for, session
app = Flask(__name__)
app.secret_key = "petadoption123"


# ==========================
# CREATE DATABASE TABLES
# ==========================

def create_table():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # ==========================
    # Users Table
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT,
        email TEXT,
        phone TEXT,
        address TEXT,
        password TEXT
    )
    """)

    # Add role column if it doesn't already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    if "role" not in columns:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT DEFAULT 'Adopter'
        """)

    # ==========================
    # Pets Table
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        breed TEXT,
        age TEXT,
        gender TEXT,
        vaccinated TEXT,
        description TEXT,
        image TEXT,
        status TEXT DEFAULT 'Available'
    )
    """)

    # Add shelter_id column if it doesn't already exist
    cursor.execute("PRAGMA table_info(pets)")
    pet_columns = [column[1] for column in cursor.fetchall()]

    if "shelter_id" not in pet_columns:
        cursor.execute("""
            ALTER TABLE pets
            ADD COLUMN shelter_id INTEGER
        """)
    

    # ==========================
    # Adoptions Table
    # ==========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adoptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pet_id INTEGER,
        adopter_name TEXT,
        phone TEXT,
        address TEXT,
        payment_status TEXT,
        transport_method TEXT,
        request_status TEXT
    )
    """)

    
    # Insert Sample Pets Only Once
    cursor.execute("SELECT COUNT(*) FROM pets")
    count = cursor.fetchone()[0]

    if count == 0:

        pets = [

            (
                "Bruno",
                "Labrador",
                "2 Years",
                "Male",
                "Yes",
                "Friendly and energetic Labrador.",
                "hero.jpg"
            ),

            (
                "Kitty",
                "Persian Cat",
                "1 Year",
                "Female",
                "Yes",
                "Calm and affectionate Persian cat.",
                "hero.jpg"
            ),

            (
                "Snow",
                "Rabbit",
                "8 Months",
                "Male",
                "No",
                "Playful white rabbit.",
                "hero.jpg"
            )

        ]

        cursor.executemany("""
        INSERT INTO pets
        (name, breed, age, gender, vaccinated, description, image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, pets)

    conn.commit()
    conn.close()


# ==========================
# HOME
# ==========================

@app.route('/')
def home():
    return render_template("index.html")


# ==========================
# REGISTER
# ==========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == "POST":

        fullname = request.form["fullname"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()
        password = request.form["password"]

        # Check name
        if not fullname:
            return "Name cannot be empty"

        # Check email
        if not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            return "Please enter a valid email address"

        # Check phone number
        if not re.match(r'^[0-9]{10}$', phone):
            return "Phone number must contain exactly 10 digits"

        # Check password
        if len(password) < 6:
            return "Password must contain at least 6 characters"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users(fullname, email, phone, address, password, role)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            fullname,
            email,
            phone,
            address,
            password,
            "Adopter"
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# ==========================
# LOGIN
# ==========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        if not email:
            return "Email cannot be empty"

        if not password:
            return "Password cannot be empty"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, fullname, email, phone, address, password, role
            FROM users
            WHERE email=? AND password=?
            """,
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            # Store user information in session
            session['user'] = user[1]
            session['user_id'] = user[0]
            session['role'] = user[6]

            # Admin
            if email == "admin@gmail.com":
                session['role'] = "Admin"
                return redirect(url_for('admin'))

            # Shelter
            if user[6] == "Shelter":
                return redirect(url_for('shelter_dashboard'))

            # Adopter
            return redirect(url_for('pets'))

        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route('/shelter-dashboard')
def shelter_dashboard():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM pets
        WHERE shelter_id = ?
    """, (session['user_id'],))

    total_pets = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM pets
        WHERE shelter_id = ?
        AND status = 'Available'
    """, (session['user_id'],))

    available_pets = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM pets
        WHERE shelter_id = ?
        AND status = 'Adopted'
    """, (session['user_id'],))

    adopted_pets = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "shelter_dashboard.html",
        total_pets=total_pets,
        available_pets=available_pets,
        adopted_pets=adopted_pets
    )
    # ==========================
# PET LIST
# ==========================

@app.route('/pets')
def pets():

    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search')

    print("Search =", search)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if search:
        cursor.execute("""
        SELECT * FROM pets
        WHERE status='Available'
        AND (name LIKE ? OR breed LIKE ?)
        """, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM pets WHERE status='Available'")

    pets = cursor.fetchall()

    print("Pets Found =", pets)

    conn.close()

    return render_template("pets.html", pets=pets)
# ==========================
# PET DETAILS
# ==========================

@app.route('/pet_details/<int:pet_id>')
def pet_details(pet_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM pets WHERE id=?",
        (pet_id,)
    )

    pet = cursor.fetchone()

    conn.close()

    return render_template("pet_details.html", pet=pet)
# ==========================
# ADOPTION
# ==========================

@app.route('/adoption/<int:pet_id>', methods=['GET', 'POST'])
def adoption(pet_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == "POST":

        # Get the logged-in user's name automatically
        adopter_name = session['user']

        phone = request.form["phone"]
        address = request.form["address"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO adoptions
        (
            pet_id,
            adopter_name,
            phone,
            address,
            payment_status,
            transport_method,
            request_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pet_id,
            adopter_name,
            phone,
            address,
            "Pending",
            "",
            "Pending"
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("payment", pet_id=pet_id))

    return render_template(
        "adoption.html",
        pet_id=pet_id
    )

    # ==========================
# PAYMENT
# ==========================

@app.route('/payment/<int:pet_id>', methods=['GET', 'POST'])
def payment(pet_id):

    if request.method == "POST":

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE adoptions
        SET payment_status = ?
        WHERE pet_id = ?
        """, ("Paid", pet_id))

        conn.commit()
        conn.close()

        return redirect(url_for("transport", pet_id=pet_id))

    return render_template(
        "payment.html",
        pet_id=pet_id
    )


# ==========================
# TRANSPORT
# ==========================

@app.route('/transport/<int:pet_id>', methods=['GET', 'POST'])
def transport(pet_id):

    if request.method == 'POST':

        transport_method = request.form['transport']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE adoptions
        SET transport_method = ?
        WHERE pet_id = ?
        """, (transport_method, pet_id))

        conn.commit()
        conn.close()

        return redirect(url_for('success'))

    return render_template("transport.html", pet_id=pet_id)


@app.route('/success')
def success():
    return render_template("success.html")
# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route('/admin')
def admin():

    # Check if user is logged in
    if 'user' not in session:
        return redirect(url_for('login'))

    # Check if the logged-in user is Admin
    if session['user'] != "Admin":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Dashboard Statistics
    cursor.execute("SELECT COUNT(*) FROM pets")
    total_pets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pets WHERE status='Available'")
    available_pets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pets WHERE status='Adopted'")
    adopted_pets = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM adoptions")
    total_requests = cursor.fetchone()[0]

    # Adoption Requests
    cursor.execute("""
    SELECT
        adoptions.id,
        pets.name,
        adoptions.adopter_name,
        adoptions.phone,
        adoptions.payment_status,
        adoptions.transport_method,
        adoptions.request_status
    FROM adoptions
    JOIN pets
    ON adoptions.pet_id = pets.id
    """)

    requests = cursor.fetchall()
    cursor.execute("""
    SELECT * FROM pets
""")

    pets = cursor.fetchall()
    conn.close()

    return render_template(
    "admin.html",
    requests=requests,
    pets=pets,
    total_pets=total_pets,
    available_pets=available_pets,
    adopted_pets=adopted_pets,
    total_requests=total_requests
)
@app.route('/add-pet', methods=['GET', 'POST'])
def add_pet():

    # Only logged-in Admin can access
    if 'user' not in session:
        return redirect(url_for('login'))

    if session['user'] != "Admin":
        return "Access Denied!"

    if request.method == 'POST':

        name = request.form['name']
        breed = request.form['breed']
        age = request.form['age']
        gender = request.form['gender']
        vaccinated = request.form['vaccinated']
        description = request.form['description']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO pets
        (name, breed, age, gender, vaccinated, description, image, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            "hero.jpg",
            "Available"
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('admin'))

    return render_template("add_pet.html")
@app.route('/edit-pet/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):

    # Only logged-in Admin can edit pets
    if 'user' not in session:
        return redirect(url_for('login'))

    if session['user'] != "Admin":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == 'POST':

        name = request.form['name']
        breed = request.form['breed']
        age = request.form['age']
        gender = request.form['gender']
        vaccinated = request.form['vaccinated']
        description = request.form['description']
        status = request.form['status']

        cursor.execute("""
        UPDATE pets
        SET name=?,
            breed=?,
            age=?,
            gender=?,
            vaccinated=?,
            description=?,
            status=?
        WHERE id=?
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            status,
            pet_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('admin'))

    cursor.execute("""
    SELECT * FROM pets
    WHERE id=?
    """, (pet_id,))

    pet = cursor.fetchone()

    conn.close()

    return render_template("edit_pet.html", pet=pet)

@app.route('/approve/<int:request_id>')
def approve(request_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE adoptions
    SET request_status = 'Approved'
    WHERE id = ?
    """, (request_id,))

    # Check whether the status actually changed
    cursor.execute("""
    SELECT id, request_status
    FROM adoptions
    WHERE id = ?
    """, (request_id,))

    check = cursor.fetchone()
    print("AFTER APPROVE:", check)

    # Find pet ID
    cursor.execute("""
    SELECT pet_id
    FROM adoptions
    WHERE id = ?
    """, (request_id,))

    result = cursor.fetchone()

    if result:
        pet_id = result[0]

        cursor.execute("""
        UPDATE pets
        SET status = 'Adopted'
        WHERE id = ?
        """, (pet_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))

@app.route('/reject/<int:request_id>')
def reject(request_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE adoptions
    SET request_status = ?
    WHERE id = ?
    """, ("Rejected", request_id))

    conn.commit()
    conn.close()

    return redirect(url_for('admin'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template("about.html")
@app.route('/contact')
def contact():
    return render_template("contact.html")
@app.route('/my-requests')
def my_requests():

    if 'user' not in session:
        return redirect(url_for('login'))

    adopter_name = session['user']

    print("Logged-in user =", adopter_name)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        adoptions.id,
        pets.name,
        pets.breed,
        adoptions.request_status,
        adoptions.transport_method,
        adoptions.adopter_name
    FROM adoptions
    JOIN pets
    ON adoptions.pet_id = pets.id
    WHERE adoptions.adopter_name = ?
    """, (adopter_name,))

    requests = cursor.fetchall()

    print("Logged-in user =", adopter_name)
    print("My Requests =", requests)

    conn.close()

@app.route('/shelter-register', methods=['GET', 'POST'])
def shelter_register():

    if request.method == "POST":

        fullname = request.form["fullname"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users(
            fullname,
            email,
            phone,
            address,
            password,
            role
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            fullname,
            email,
            phone,
            address,
            password,
            "Shelter"
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("shelter_register.html")   

    return render_template("my_requests.html", requests=requests)

@app.route('/shelter-add-pet', methods=['GET', 'POST'])
def shelter_add_pet():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    if request.method == 'POST':

        name = request.form['name']
        breed = request.form['breed']
        age = request.form['age']
        gender = request.form['gender']
        vaccinated = request.form['vaccinated']
        description = request.form['description']

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO pets
            (name, breed, age, gender, vaccinated,
             description, image, status, shelter_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            "hero.jpg",
            "Available",
            session['user_id']
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('shelter_dashboard'))

    return render_template("shelter_add_pet.html")

@app.route('/shelter-requests')
def shelter_requests():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adoptions.id,
            pets.name,
            adoptions.adopter_name,
            adoptions.phone,
            adoptions.address,
            adoptions.payment_status,
            adoptions.transport_method,
            adoptions.request_status
        FROM adoptions
        JOIN pets
        ON adoptions.pet_id = pets.id
        WHERE pets.shelter_id = ?
        ORDER BY adoptions.id DESC
    """, (session['user_id'],))

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "shelter_requests.html",
        requests=requests
    )
@app.route('/check-adoptions')
def check_adoptions():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(adoptions)")
    columns = cursor.fetchall()

    conn.close()

    return "<br>".join(str(column) for column in columns)

@app.route('/shelter-pets')
def shelter_pets():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE shelter_id = ?
        ORDER BY id DESC
    """, (session['user_id'],))

    pets = cursor.fetchall()

    conn.close()

    return render_template(
        "shelter_pets.html",
        pets=pets
    )
if __name__ == "__main__":
    create_table()
    app.run(debug=True)