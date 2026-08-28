import sqlite3
import re
import os

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = "petadoption123"

# ==========================
# IMAGE UPLOAD SETTINGS
# ==========================

UPLOAD_FOLDER = "static/images"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================
# CREATE DATABASE TABLES
# ==========================
# ==========================
# CREATE DATABASE TABLES
# ==========================

def create_table():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # ==========================
    # USERS TABLE
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
    user_columns = [column[1] for column in cursor.fetchall()]

    if "role" not in user_columns:
        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN role TEXT DEFAULT 'Adopter'
        """)


    # ==========================
    # PETS TABLE
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
    # ADOPTIONS TABLE
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


    # ==========================
    # ADD NEW ADOPTION COLUMNS
    # ==========================

    cursor.execute("PRAGMA table_info(adoptions)")
    adoption_columns = [column[1] for column in cursor.fetchall()]

    if "payment_method" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN payment_method TEXT DEFAULT 'Online'
        """)

    if "payment_amount" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN payment_amount REAL DEFAULT 0
        """)

    if "refund_status" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN refund_status TEXT DEFAULT 'Not Applicable'
        """)

    if "transport_date" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN transport_date TEXT
        """)

    if "transport_time" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN transport_time TEXT
        """)

    if "transport_status" not in adoption_columns:
        cursor.execute("""
            ALTER TABLE adoptions
            ADD COLUMN transport_status TEXT DEFAULT 'Not Scheduled'
        """)


    # ==========================
    # INSERT SAMPLE PETS
    # ==========================

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
        (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, pets)

# ==========================
# MESSAGES TABLE
# ==========================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            subject TEXT,
            message TEXT,
            status TEXT DEFAULT 'Unread',
            reply TEXT,
            created_at TEXT
        )
    """)


# ==========================
# SAVE DATABASE
# ==========================

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

# ==========================
# PET LIST / SEARCH
# ==========================

# ==========================
# PET LIST + SEARCH
# ==========================

# ==========================
# PET LIST / SEARCH / CATEGORY
# ==========================

@app.route('/pets')
def pets():

    if 'user' not in session:
        return redirect(url_for('login'))

    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip().lower()

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = """
        SELECT *
        FROM pets
        WHERE LOWER(TRIM(status)) = 'available'
    """

    params = []

    # ==========================
    # SEARCH
    # ==========================

    if search:

        query += """
            AND (
                LOWER(name) LIKE ?
                OR LOWER(breed) LIKE ?
            )
        """

        search_value = "%" + search.lower() + "%"

        params.append(search_value)
        params.append(search_value)

    # ==========================
    # CATEGORY
    # ==========================

    if category == "dog":

        query += """
            AND (
                LOWER(breed) LIKE '%labrador%'
                OR LOWER(breed) LIKE '%dog%'
                OR LOWER(breed) LIKE '%retriever%'
                OR LOWER(breed) LIKE '%beagle%'
                OR LOWER(breed) LIKE '%german shepherd%'
                OR LOWER(breed) LIKE '%poodle%'
                OR LOWER(breed) LIKE '%husky%'
            )
        """

    elif category == "cat":

        query += """
            AND (
                LOWER(breed) LIKE '%cat%'
                OR LOWER(breed) LIKE '%persian%'
                OR LOWER(breed) LIKE '%siamese%'
                OR LOWER(breed) LIKE '%maine coon%'
            )
        """

    elif category == "rabbit":

        query += """
            AND (
                LOWER(breed) LIKE '%rabbit%'
            )
        """

    query += " ORDER BY id DESC"

    cursor.execute(query, params)

    pets = cursor.fetchall()

    conn.close()

    return render_template(
        "pets.html",
        pets=pets,
        search=search,
        category=category
    )
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

# ==========================
# PAYMENT
# ==========================

@app.route('/payment/<int:pet_id>', methods=['GET', 'POST'])
def payment(pet_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Adopter":
        return "Access Denied!"

    adopter_name = session['user']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Find the adopter's request for this pet
    cursor.execute("""
        SELECT id, request_status
        FROM adoptions
        WHERE pet_id = ?
        AND adopter_name = ?
        ORDER BY id DESC
        LIMIT 1
    """, (pet_id, adopter_name))

    adoption = cursor.fetchone()

    if not adoption:
        conn.close()
        return "Adoption request not found!"

    request_id = adoption[0]
    request_status = adoption[1]

    # Payment is allowed only after shelter approval
    if request_status != "Approved":
        conn.close()
        return "Payment is available only after the shelter approves your request."

    if request.method == "POST":

        payment_method = request.form.get("payment_method")

        if payment_method not in ["Online", "COD"]:
            conn.close()
            return "Please select a valid payment method."

        if payment_method == "Online":

            payment_status = "Paid"
            refund_status = "Not Applicable"

        else:

            payment_status = "COD"
            refund_status = "Not Applicable"

        cursor.execute("""
            UPDATE adoptions
            SET
                payment_method = ?,
                payment_status = ?,
                refund_status = ?
            WHERE id = ?
        """, (
            payment_method,
            payment_status,
            refund_status,
            request_id
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "transport",
                pet_id=pet_id
            )
        )

    conn.close()

    return render_template(
        "payment.html",
        pet_id=pet_id,
        request_id=request_id
    )
# ==========================
# TRANSPORT
# ==========================

# ==========================
# TRANSPORT SCHEDULING
# ==========================

@app.route('/transport/<int:pet_id>', methods=['GET', 'POST'])
def transport(pet_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Adopter":
        return "Access Denied!"

    adopter_name = session['user']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Find this adopter's adoption request
    cursor.execute("""
        SELECT
            id,
            payment_method,
            payment_status,
            request_status,
            transport_method,
            transport_date,
            transport_time,
            transport_status
        FROM adoptions
        WHERE pet_id = ?
        AND adopter_name = ?
        ORDER BY id DESC
        LIMIT 1
    """, (pet_id, adopter_name))

    adoption = cursor.fetchone()

    if not adoption:
        conn.close()
        return "Adoption request not found!"

    request_id = adoption[0]
    payment_method = adoption[1]
    payment_status = adoption[2]
    request_status = adoption[3]

    # Transport is available only after approval
    if request_status != "Approved":
        conn.close()
        return "Transport is available only after shelter approval."

    # Payment must be selected first
    if payment_status not in ["Paid", "COD"]:
        conn.close()
        return redirect(url_for("payment", pet_id=pet_id))

    if request.method == "POST":

        transport_method = request.form.get("transport_method")
        transport_date = request.form.get("transport_date")
        transport_time = request.form.get("transport_time")

        if not transport_method:
            conn.close()
            return "Please select a transport method."

        if not transport_date:
            conn.close()
            return "Please select a transport date."

        if not transport_time:
            conn.close()
            return "Please select a transport time."

        cursor.execute("""
            UPDATE adoptions
            SET
                transport_method = ?,
                transport_date = ?,
                transport_time = ?,
                transport_status = 'Scheduled'
            WHERE id = ?
        """, (
            transport_method,
            transport_date,
            transport_time,
            request_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("success"))

    conn.close()

    return render_template(
        "transport.html",
        pet_id=pet_id,
        adoption=adoption
    )
# ==========================
# VIEW MESSAGES
# ==========================

@app.route('/messages')
def messages():

    if 'user' not in session:
        return redirect(url_for('login'))

    # Only Admin can view messages for now
    if session.get('role') != 'Admin':
        return "Access Denied!"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM messages
        ORDER BY id DESC
    """)

    messages = cursor.fetchall()

    conn.close()

    return render_template(
        "messages.html",
        messages=messages
    )

# ==========================
# REPLY TO MESSAGE
# ==========================

@app.route('/reply-message/<int:message_id>', methods=['POST'])
def reply_message(message_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    # Only Admin can reply
    if session.get('role') != 'Admin':
        return "Access Denied!"

    reply = request.form['reply'].strip()

    if not reply:
        return "Reply cannot be empty"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE messages
        SET reply = ?,
            status = 'Read'
        WHERE id = ?
    """, (reply, message_id))

    conn.commit()
    conn.close()

    return redirect(url_for('messages'))

# ==========================
# MY MESSAGES
# ==========================

@app.route('/my-messages')
def my_messages():

    if 'user' not in session:
        return redirect(url_for('login'))

    user_id = session.get('user_id')

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            email,
            subject,
            message,
            status,
            reply,
            created_at
        FROM messages
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    messages = cursor.fetchall()

    conn.close()

    return render_template(
        "my_messages.html",
        messages=messages
    )
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

        # ==========================
        # IMAGE UPLOAD
        # ==========================

        image_file = request.files.get('image')

        image_name = "hero.jpg"

        if image_file and image_file.filename:

            if not allowed_file(image_file.filename):
                return "Invalid image format. Please use JPG, JPEG, PNG, GIF or WEBP."

            image_name = secure_filename(image_file.filename)

            image_file.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    image_name
                )
            )

        # ==========================
        # DATABASE
        # ==========================

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO pets
        (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image_name,
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

    # Get current pet
    cursor.execute("""
        SELECT *
        FROM pets
        WHERE id = ?
    """, (pet_id,))

    pet = cursor.fetchone()

    if not pet:
        conn.close()
        return "Pet not found"

    # ==========================
    # UPDATE PET
    # ==========================

    if request.method == 'POST':

        name = request.form['name']
        breed = request.form['breed']
        age = request.form['age']
        gender = request.form['gender']
        vaccinated = request.form['vaccinated']
        description = request.form['description']
        status = request.form['status']

        # Keep existing image
        image_name = pet[7]

        # Check for new image
        image_file = request.files.get('image')

        if image_file and image_file.filename:

            if not allowed_file(image_file.filename):
                conn.close()
                return "Invalid image format. Please use JPG, JPEG, PNG, GIF or WEBP."

            image_name = secure_filename(image_file.filename)

            image_file.save(
                os.path.join(
                    app.config['UPLOAD_FOLDER'],
                    image_name
                )
            )

        # Update database
        cursor.execute("""
        UPDATE pets
        SET
            name = ?,
            breed = ?,
            age = ?,
            gender = ?,
            vaccinated = ?,
            description = ?,
            image = ?,
            status = ?
        WHERE id = ?
        """, (
            name,
            breed,
            age,
            gender,
            vaccinated,
            description,
            image_name,
            status,
            pet_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for('admin'))

    conn.close()

    return render_template(
        "edit_pet.html",
        pet=pet
    )

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

# ==========================
# SHELTER APPROVE REQUEST
# ==========================

@app.route('/shelter-approve/<int:request_id>')
def shelter_approve(request_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Make sure this request belongs to this shelter
    cursor.execute("""
        SELECT adoptions.pet_id
        FROM adoptions
        JOIN pets
        ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ?
        AND pets.shelter_id = ?
    """, (request_id, shelter_id))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return "Access Denied!"

    pet_id = result[0]

    # Approve request
    cursor.execute("""
        UPDATE adoptions
        SET request_status = 'Approved'
        WHERE id = ?
    """, (request_id,))

    

    conn.commit()
    conn.close()

    return redirect(url_for('shelter_requests'))

# ==========================
# SHELTER REJECT REQUEST
# ==========================

@app.route('/shelter-reject/<int:request_id>')
def shelter_reject(request_id):

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Shelter":
        return "Access Denied!"

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get request information and verify ownership
    cursor.execute("""
        SELECT
            adoptions.pet_id,
            adoptions.payment_status
        FROM adoptions
        JOIN pets
        ON adoptions.pet_id = pets.id
        WHERE adoptions.id = ?
        AND pets.shelter_id = ?
    """, (request_id, shelter_id))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return "Access Denied!"

    pet_id = result[0]
    payment_status = result[1]

    # Reject request
    cursor.execute("""
        UPDATE adoptions
        SET request_status = 'Rejected'
        WHERE id = ?
    """, (request_id,))

    # If payment was already made,
    # mark refund as pending
    if payment_status == "Paid":

        cursor.execute("""
            UPDATE adoptions
            SET refund_status = 'Refund Pending'
            WHERE id = ?
        """, (request_id,))

    else:

        cursor.execute("""
            UPDATE adoptions
            SET refund_status = 'Not Applicable'
            WHERE id = ?
        """, (request_id,))

    # Pet becomes available again
    cursor.execute("""
        UPDATE pets
        SET status = 'Available'
        WHERE id = ?
    """, (pet_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('shelter_requests'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template("about.html")
# ==========================
# CONTACT / SEND MESSAGE
# ==========================

@app.route('/contact', methods=['GET', 'POST'])
def contact():

    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':

        name = request.form['name'].strip()
        email = request.form['email'].strip()
        subject = request.form['subject'].strip()
        message = request.form['message'].strip()

        # Basic validation

        if not name:
            return "Name cannot be empty"

        if not email:
            return "Email cannot be empty"

        if not subject:
            return "Subject cannot be empty"

        if not message:
            return "Message cannot be empty"

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages
            (
                user_id,
                name,
                email,
                subject,
                message,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            session.get('user_id'),
            name,
            email,
            subject,
            message,
            "Unread"
        ))

        conn.commit()
        conn.close()

        return render_template(
            "contact.html",
            success="Your message has been sent successfully!"
        )

    return render_template("contact.html")
@app.route('/my-requests')
def my_requests():

    if 'user' not in session:
        return redirect(url_for('login'))

    if session.get('role') != "Adopter":
        return redirect(url_for('pets'))

    adopter_name = session['user']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            adoptions.id,
            pets.id,
            pets.name,
            pets.breed,
            adoptions.request_status,
            adoptions.transport_method,
            adoptions.adopter_name,
            adoptions.payment_method,
            adoptions.payment_status,
            adoptions.refund_status
        FROM adoptions
        JOIN pets
        ON adoptions.pet_id = pets.id
        WHERE adoptions.adopter_name = ?
        ORDER BY adoptions.id DESC
    """, (adopter_name,))

    requests = cursor.fetchall()

    conn.close()

    return render_template(
        "my_requests.html",
        requests=requests
    )
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

    shelter_id = session['user_id']

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
    """, (shelter_id,))

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

    shelter_id = session['user_id']

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM pets
        WHERE shelter_id = ?
        ORDER BY id DESC
    """, (shelter_id,))

    pets = cursor.fetchall()

    conn.close()

    return render_template(
        "shelter_pets.html",
        pets=pets
    )
if __name__ == "__main__":
    create_table()
    app.run(debug=True)