import unittest
import sqlite3
import re
import os
from app import app, validate_fullname, validate_email, validate_phone, validate_address, validate_subject, validate_message, validate_pet_fields, validate_upi_id, validate_pet_age, parse_pet_age

class ValidationUnitTests(unittest.TestCase):
    def test_upi_validation(self):
        self.assertFalse(validate_upi_id("")[0])
        self.assertFalse(validate_upi_id("   ")[0])
        self.assertFalse(validate_upi_id(None)[0])
        self.assertFalse(validate_upi_id("invalid")[0])
        self.assertFalse(validate_upi_id("@bank")[0])
        self.assertFalse(validate_upi_id("username@")[0])
        self.assertFalse(validate_upi_id("a@b")[0])
        self.assertTrue(validate_upi_id("name@upi")[0])
        self.assertTrue(validate_upi_id("user.name-123@okhdfcbank")[0])
        self.assertTrue(validate_upi_id("adopter_pay@paytm")[0])

    def test_fullname_validation(self):
        # Empty and whitespace
        self.assertFalse(validate_fullname("")[0])
        self.assertFalse(validate_fullname("   ")[0])
        self.assertFalse(validate_fullname(None)[0])
        # Purely numeric or symbol
        self.assertFalse(validate_fullname("123456")[0])
        self.assertFalse(validate_fullname("---...")[0])
        # Too short / too long
        self.assertFalse(validate_fullname("A")[0])
        self.assertFalse(validate_fullname("A" * 61)[0])
        # Valid names
        self.assertTrue(validate_fullname("John Doe")[0])
        self.assertTrue(validate_fullname("Dr. Mary-Jane O'Connor")[0])
        self.assertTrue(validate_fullname("Happy Paws Shelter 2")[0])

    def test_email_validation(self):
        self.assertFalse(validate_email("")[0])
        self.assertFalse(validate_email("   ")[0])
        self.assertFalse(validate_email("plainaddress")[0])
        self.assertFalse(validate_email("@missinguser.com")[0])
        self.assertFalse(validate_email("user@.com")[0])
        self.assertFalse(validate_email("user with space@domain.com")[0])
        self.assertTrue(validate_email("adopter@gmail.com")[0])
        self.assertTrue(validate_email("shelter.contact@ngo.org")[0])

    def test_phone_validation(self):
        self.assertFalse(validate_phone("")[0])
        self.assertFalse(validate_phone("   ")[0])
        self.assertFalse(validate_phone("12345")[0])
        self.assertFalse(validate_phone("abcdefghij")[0])
        self.assertFalse(validate_phone("987654321012")[0])
        self.assertFalse(validate_phone("98765-43210")[0])
        # Valid standard 10 digits
        self.assertTrue(validate_phone("9876543210")[0])
        # Standard +91 prefix normalized
        self.assertTrue(validate_phone("+919876543210")[0])

    def test_address_validation(self):
        self.assertFalse(validate_address("")[0])
        self.assertFalse(validate_address("   ")[0])
        self.assertFalse(validate_address("123")[0])  # < 5 chars
        self.assertTrue(validate_address("123 Main St, Springfield")[0])

    def test_subject_and_message_validation(self):
        self.assertFalse(validate_subject("")[0])
        self.assertFalse(validate_subject("  ")[0])
        self.assertFalse(validate_subject("Hi")[0])  # < 3 chars
        self.assertTrue(validate_subject("Adoption Inquiry")[0])

        self.assertFalse(validate_message("")[0])
        self.assertFalse(validate_message("Short")[0])  # < 10 chars
        self.assertTrue(validate_message("Hello, I would like more information about adopting Bruno.")[0])

    def test_pet_validation(self):
        self.assertFalse(validate_pet_fields("", "Labrador", "2 Years", "Male", "Yes", "Friendly dog")[0])
        self.assertFalse(validate_pet_fields("Bruno", "", "2 Years", "Male", "Yes", "Friendly dog")[0])
        self.assertFalse(validate_pet_fields("Bruno", "Labrador", "", "Male", "Yes", "Friendly dog")[0])
        self.assertFalse(validate_pet_fields("Bruno", "Labrador", "2 Years", "Unknown", "Yes", "Friendly dog")[0])
        self.assertFalse(validate_pet_fields("Bruno", "Labrador", "2 Years", "Male", "Maybe", "Friendly dog")[0])
        self.assertFalse(validate_pet_fields("Bruno", "Labrador", "2 Years", "Male", "Yes", "Tiny")[0])
        self.assertTrue(validate_pet_fields("Bruno", "Labrador", "2 Years", "Male", "Yes", "Healthy and playful companion.")[0])

    def test_pet_age_dropdown_validation(self):
        # 1. Valid numbers and units
        self.assertTrue(validate_pet_age("1", "Years")[0])
        self.assertEqual(validate_pet_age("1", "Years")[1], "1 Year")
        self.assertTrue(validate_pet_age(2, "Years")[0])
        self.assertEqual(validate_pet_age(2, "Years")[1], "2 Years")
        self.assertTrue(validate_pet_age("1", "Months")[0])
        self.assertEqual(validate_pet_age("1", "Months")[1], "1 Month")
        self.assertTrue(validate_pet_age(6, "Months")[0])
        self.assertEqual(validate_pet_age(6, "Months")[1], "6 Months")
        self.assertTrue(validate_pet_age("2 Years")[0])
        self.assertEqual(validate_pet_age("2 Years")[1], "2 Years")
        self.assertTrue(validate_pet_age("1 Year")[0])
        self.assertEqual(validate_pet_age("1 Year")[1], "1 Year")

        # 2. Strict rejection of 0
        self.assertFalse(validate_pet_age("0", "Years")[0])
        self.assertFalse(validate_pet_age(0, "Months")[0])
        self.assertFalse(validate_pet_age("0 Years")[0])
        self.assertFalse(validate_pet_age("0 Months")[0])
        self.assertFalse(validate_pet_fields("Bruno", "Labrador", "0 Years", "Male", "Yes", "Healthy and playful companion.")[0])

        # 3. Strict rejection of negative numbers
        self.assertFalse(validate_pet_age("-1", "Years")[0])
        self.assertFalse(validate_pet_age(-5, "Months")[0])
        self.assertFalse(validate_pet_age("-2 Years")[0])

        # 4. Strict rejection of numbers > 30
        self.assertFalse(validate_pet_age("31", "Years")[0])
        self.assertFalse(validate_pet_age(35, "Months")[0])
        self.assertFalse(validate_pet_age("40 Years")[0])

        # 5. Strict rejection of empty or missing
        self.assertFalse(validate_pet_age("", "")[0])
        self.assertFalse(validate_pet_age("   ", "Years")[0])
        self.assertFalse(validate_pet_age("5", "   ")[0])
        self.assertFalse(validate_pet_age(None, "Years")[0])
        self.assertFalse(validate_pet_age("5", None)[0])
        self.assertFalse(validate_pet_age("")[0])
        self.assertFalse(validate_pet_age(None)[0])

        # 6. Strict rejection of invalid units
        self.assertFalse(validate_pet_age("5", "Days")[0])
        self.assertFalse(validate_pet_age("2", "Weeks")[0])
        self.assertFalse(validate_pet_age("3", "Decades")[0])

        # 7. Legacy parsing
        self.assertEqual(parse_pet_age("1"), (None, None))
        self.assertEqual(parse_pet_age("3 years"), (3, "Years"))
        self.assertEqual(parse_pet_age("6 Months"), (6, "Months"))
        self.assertEqual(parse_pet_age("1 Month"), (1, "Months"))
        self.assertEqual(parse_pet_age("0 Years"), (None, None))
        self.assertEqual(parse_pet_age("-2 Years"), (None, None))


class EndToEndSystemTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_no_approximate_times_in_templates(self):
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        pattern = re.compile(r"(approximately|estimated\s+time|estimated\s+delivery)", re.IGNORECASE)
        found_matches = []
        for root, _, files in os.walk(templates_dir):
            for file in files:
                if file.endswith(".html"):
                    filepath = os.path.join(root, file)
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for line_no, line in enumerate(f, 1):
                            if pattern.search(line):
                                found_matches.append(f"{file}:{line_no}: {line.strip()}")
        self.assertEqual(found_matches, [], f"Found approximate time references in templates: {found_matches}")

    def test_database_records_adoption_amount_and_no_approximate_times(self):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        
        # Check payment_amount is 500 for all approved adoptions
        cursor.execute("SELECT id, payment_amount, payment_method, payment_status, transport_time FROM adoptions WHERE request_status = 'Approved'")
        approved = cursor.fetchall()
        for row in approved:
            req_id, amount, method, status, t_time = row
            self.assertEqual(amount, 500, f"Request {req_id} has payment_amount={amount}, expected 500")
            if method:
                self.assertIn(method, ['UPI', 'COD'], f"Request {req_id} has invalid method: {method}")
            # Ensure transport_time has no approximate strings
            if t_time:
                self.assertNotIn("approximately", t_time.lower())
                self.assertNotIn("hours", t_time.lower())
        conn.close()

    def test_contact_form_validation(self):
        # Empty name and message
        res = self.client.post('/contact', data={
            'name': '   ',
            'email': 'valid@example.com',
            'subject': 'Inquiry',
            'message': '   '
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"cannot be empty", res.data)

        # Invalid email
        res = self.client.post('/contact', data={
            'name': 'Valid User',
            'email': 'not-an-email',
            'subject': 'Inquiry',
            'message': 'This is a valid long enough message.'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"valid email", res.data)

    def test_register_validation(self):
        # Invalid phone (< 10 digits)
        res = self.client.post('/register', data={
            'role': 'Adopter',
            'fullname': 'New User',
            'email': 'newuser@example.com',
            'phone': '12345',
            'address': 'Valid Address, 123 Street',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"exactly 10 digits", res.data)

        # Whitespace address
        res = self.client.post('/register', data={
            'role': 'Adopter',
            'fullname': 'New User',
            'email': 'newuser2@example.com',
            'phone': '9876543210',
            'address': '    ',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Address cannot be empty", res.data)

    def test_payment_hardcoded_500_and_upi_cod_only(self):
        # Set up a test adopter session
        with self.client.session_transaction() as sess:
            sess['user'] = 'TestAdopter'
            sess['user_id'] = 9999
            sess['role'] = 'Adopter'

        # Insert a temporary test adoption record
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pets LIMIT 1")
        pet_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method)
            VALUES (?, 'TestAdopter', '9876543210', 'Test Address 123', 'Approved', 'Pending', 500, 'Home Delivery')
        """, (pet_id,))
        test_adoption_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            # 1. Reject invalid payment method like 'CreditCard'
            res = self.client.post(f'/payment/{pet_id}', data={'payment_method': 'CreditCard'})
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"valid payment method", res.data)

            # 2. Reject empty UPI ID when method is UPI
            res = self.client.post(f'/payment/{pet_id}', data={'payment_method': 'UPI', 'upi_id': ''})
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"cannot be empty", res.data)

            # 3. Reject invalid UPI ID format
            res = self.client.post(f'/payment/{pet_id}', data={'payment_method': 'UPI', 'upi_id': 'invalidformat'})
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Invalid UPI ID format", res.data)

            # 4. Valid UPI payment (also testing tamper attempt on amount: backend strictly enforces 500)
            res = self.client.post(f'/payment/{pet_id}', data={'payment_method': 'UPI', 'upi_id': 'testadopter@upi', 'amount': '100'})
            self.assertEqual(res.status_code, 302)  # Redirects to payment_success

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT payment_amount, payment_method, payment_status, upi_id, payment_date FROM adoptions WHERE id = ?", (test_adoption_id,))
            record = cursor.fetchone()
            conn.close()

            self.assertEqual(record[0], 500.0, "Backend must ignore client amount and strictly enforce 500!")
            self.assertEqual(record[1], "UPI")
            self.assertEqual(record[2], "Paid")
            self.assertEqual(record[3], "testadopter@upi")
            self.assertIsNotNone(record[4], "payment_date must be saved in database!")

            # 5. Verify payment success card endpoint persists and displays database information
            res = self.client.get(f'/payment-success/{test_adoption_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Payment", res.data)
            self.assertIn(b"Successful", res.data)
            self.assertIn(b"500", res.data)
            self.assertIn(b"testadopter@upi", res.data)
            self.assertIn(str(test_adoption_id).encode(), res.data)

            # 6. Test COD payment method on a new or reset adoption
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("UPDATE adoptions SET payment_status = 'Pending' WHERE id = ?", (test_adoption_id,))
            conn.commit()
            conn.close()

            res = self.client.post(f'/payment/{pet_id}', data={'payment_method': 'COD'})
            self.assertEqual(res.status_code, 302)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT payment_amount, payment_method, payment_status FROM adoptions WHERE id = ?", (test_adoption_id,))
            record = cursor.fetchone()
            conn.close()

            self.assertEqual(record[0], 500.0)
            self.assertEqual(record[1], "COD")
            self.assertEqual(record[2], "COD")

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (test_adoption_id,))
            conn.commit()
            conn.close()

    def test_shelter_transport_status_progression(self):
        # Insert test shelter, pet, and adoption
        test_shelter_id = 9988
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, shelter_id)
            VALUES ('ShelterTransportPet', 'Beagle', '2 Years', 'Female', 'Yes', 'Friendly beagle', 'Available', ?)
        """, (test_shelter_id,))
        pet_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method, transport_status)
            VALUES (?, 'TransportTester', '9876543210', '123 Street', 'Approved', 'Paid', 500, 'Home Delivery', 'Pending')
        """, (pet_id,))
        adoption_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            with self.client.session_transaction() as sess:
                sess['user'] = 'ShelterAdmin'
                sess['user_id'] = test_shelter_id
                sess['role'] = 'Shelter'

            # 1. Pending -> Scheduled
            res = self.client.post(f'/shelter-update-transport-status/{adoption_id}', data={'transport_status': 'Scheduled'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT transport_status FROM adoptions WHERE id = ?", (adoption_id,))
            self.assertEqual(cursor.fetchone()[0], 'Scheduled')

            # 2. Scheduled -> In Transit
            res = self.client.post(f'/shelter-update-transport-status/{adoption_id}', data={'transport_status': 'In Transit'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            cursor.execute("SELECT transport_status FROM adoptions WHERE id = ?", (adoption_id,))
            self.assertEqual(cursor.fetchone()[0], 'In Transit')

            # 3. In Transit -> Delivered
            res = self.client.post(f'/shelter-update-transport-status/{adoption_id}', data={'transport_status': 'Delivered'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            cursor.execute("SELECT transport_status FROM adoptions WHERE id = ?", (adoption_id,))
            self.assertEqual(cursor.fetchone()[0], 'Delivered')
            conn.close()

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (adoption_id,))
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            conn.commit()
            conn.close()

    def test_adopter_delivery_method_strictly_immutable(self):
        # Insert test shelter, pet, and adoption with 'Home Delivery'
        test_shelter_id = 9989
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, shelter_id)
            VALUES ('ImmutablePet', 'Golden', '3 Years', 'Male', 'Yes', 'Gentle dog', 'Available', ?)
        """, (test_shelter_id,))
        pet_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method, transport_status)
            VALUES (?, 'TransitAdopter', '9876543210', '123 Avenue', 'Approved', 'Paid', 500, 'Home Delivery', 'Scheduled')
        """, (pet_id,))
        adoption_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            # 1. Attempting to override delivery method via legacy transit endpoint is blocked and preserved
            with self.client.session_transaction() as sess:
                sess['user'] = 'ShelterAdmin'
                sess['user_id'] = test_shelter_id
                sess['role'] = 'Shelter'

            res = self.client.post(f'/transport-update-transit/{adoption_id}', data={'transit_method': 'Shelter Pickup'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT transport_method FROM adoptions WHERE id = ?", (adoption_id,))
            # Must still be Home Delivery!
            self.assertEqual(cursor.fetchone()[0], 'Home Delivery')
            conn.close()

            # 2. Check adopter view shows the intact choice
            with self.client.session_transaction() as sess:
                sess['user'] = 'TransitAdopter'
                sess['user_id'] = 6666
                sess['role'] = 'Adopter'

            res = self.client.get('/my-requests')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Home Delivery", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (adoption_id,))
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            conn.commit()
            conn.close()

    def test_adopter_delivery_choice_preserved_upon_shelter_approval(self):
        # 1. Set up a test shelter and test pet
        test_shelter_id = 8881
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, shelter_id)
            VALUES ('ChoicePet', 'Retriever', '1 Year', 'Male', 'Yes', 'Lovely puppy', 'Available', ?)
        """, (test_shelter_id,))
        pet_id = cursor.lastrowid
        conn.commit()

        # 2. Adopter submits with 'Shelter Pickup'
        with self.client.session_transaction() as sess:
            sess['user'] = 'ChoiceAdopter'
            sess['user_id'] = 7777
            sess['role'] = 'Adopter'

        res = self.client.post(f'/adoption/{pet_id}', data={
            'adopter_name': 'ChoiceAdopter',
            'phone': '9876543210',
            'address': 'Adopter Address Road 123',
            'transport_method': 'Shelter Pickup'
        })
        self.assertEqual(res.status_code, 302)

        cursor.execute("SELECT id, transport_method FROM adoptions WHERE adopter_name = 'ChoiceAdopter' ORDER BY id DESC LIMIT 1")
        req_id, method = cursor.fetchone()
        self.assertEqual(method, 'Shelter Pickup')
        conn.close()

        try:
            # 2. Shelter logs in and approves with a scheduled date
            with self.client.session_transaction() as sess:
                sess['user'] = 'ShelterOwner'
                sess['user_id'] = test_shelter_id
                sess['role'] = 'Shelter'

            res = self.client.post(f'/approve/{req_id}', data={
                'delivery_date': '2026-10-01'
            })
            self.assertEqual(res.status_code, 302)

            # Verify that transport_method is STILL 'Shelter Pickup', payment_amount is 500
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT transport_method, payment_amount, transport_date, transport_time FROM adoptions WHERE id = ?", (req_id,))
            rec = cursor.fetchone()
            conn.close()

            self.assertEqual(rec[0], 'Shelter Pickup', "Adopter choice must not be modified by shelter!")
            self.assertEqual(rec[1], 500.0)
            self.assertEqual(rec[2], '2026-10-01')
            self.assertFalse(rec[3], "Approximate time must be empty!")

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (req_id,))
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            conn.commit()
            conn.close()

    def test_shelter_pet_and_admin_validation(self):
        # 1. Shelter add pet validation
        with self.client.session_transaction() as sess:
            sess['user'] = 'ShelterAdmin'
            sess['user_id'] = 1
            sess['role'] = 'Shelter'

        # Empty pet name
        res = self.client.post('/shelter-add-pet', data={
            'name': '   ',
            'breed': 'Pug',
            'age': '1 Year',
            'gender': 'Male',
            'vaccinated': 'Yes',
            'description': 'Very playful pug puppy'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Pet name must be between", res.data)

        # Invalid vaccinated status
        res = self.client.post('/shelter-add-pet', data={
            'name': 'Puggy',
            'breed': 'Pug',
            'age': '1 Year',
            'gender': 'Male',
            'vaccinated': 'Maybe',
            'description': 'Very playful pug puppy'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"vaccination status", res.data)

        # 2. Admin edit shelter validation (invalid phone)
        with self.client.session_transaction() as sess:
            sess['user'] = 'SiteAdmin'
            sess['user_id'] = 100
            sess['role'] = 'Admin'

        res = self.client.post('/admin/shelter/1/edit', data={
            'fullname': 'Valid Shelter Name',
            'email': 'shelter@example.com',
            'phone': 'not-a-phone',
            'address': '123 Valid Shelter Road',
            'account_status': 'Approved'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"exactly 10 digits", res.data)

    def test_shelter_reschedules_delivery_date_and_blocks_unauthorized_access(self):
        test_shelter_id = 9993
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, shelter_id)
            VALUES ('DatePet', 'Poodle', '2 Years', 'Female', 'Yes', 'Poodle dog', 'Available', ?)
        """, (test_shelter_id,))
        pet_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method, transport_status, transport_date)
            VALUES (?, 'DateAdopter', '9876543210', '123 Avenue', 'Approved', 'Paid', 500, 'Home Delivery', 'Scheduled', '2026-10-01')
        """, (pet_id,))
        adoption_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            # 1. Non-shelter access to shelter date setter is forbidden
            with self.client.session_transaction() as sess:
                sess['user'] = 'RandomAdopter'
                sess['user_id'] = 7777
                sess['role'] = 'Adopter'

            res = self.client.post(f'/shelter-set-delivery-date/{adoption_id}', data={'delivery_date': '2026-10-15'}, follow_redirects=True)
            self.assertIn(b"Access Denied", res.data)

            # 2. Shelter updates delivery date successfully
            with self.client.session_transaction() as sess:
                sess['user'] = 'ShelterManager'
                sess['user_id'] = test_shelter_id
                sess['role'] = 'Shelter'

            res = self.client.post(f'/shelter-set-delivery-date/{adoption_id}', data={'delivery_date': '2026-10-15'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT transport_date FROM adoptions WHERE id = ?", (adoption_id,))
            self.assertEqual(cursor.fetchone()[0], '2026-10-15')
            conn.close()

            # 3. Reject empty delivery date
            res = self.client.post(f'/shelter-set-delivery-date/{adoption_id}', data={'delivery_date': ''}, follow_redirects=True)
            self.assertIn(b"valid delivery date", res.data)

            # 4. Reject invalid date format
            res = self.client.post(f'/shelter-set-delivery-date/{adoption_id}', data={'delivery_date': 'not-a-date'}, follow_redirects=True)
            self.assertIn(b"Invalid delivery date format", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (adoption_id,))
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            conn.commit()
            conn.close()
            conn.close()

    def test_shelter_scheduled_date_and_transport_status_updating(self):
        test_shelter_id = 9912
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, shelter_id)
            VALUES ('TransitPet', 'Husky', '2 Years', 'Male', 'Yes', 'Friendly husky', 'Available', ?)
        """, (test_shelter_id,))
        pet_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method, transport_status, transport_date, request_date)
            VALUES (?, 'ShelterStatusAdopter', '9876543210', '456 Street', 'Approved', 'Paid', 500, 'Shelter Pickup', 'Transport Not Started', '2026-10-05', '2026-09-23')
        """, (pet_id,))
        req_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            with self.client.session_transaction() as sess:
                sess['user'] = 'ShelterMgr'
                sess['user_id'] = test_shelter_id
                sess['role'] = 'Shelter'

            # 1. Shelter updates scheduled delivery date; delivery method MUST remain untouched
            res = self.client.post(f'/shelter-set-delivery-date/{req_id}', data={'delivery_date': '2026-10-22'}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT transport_date, transport_method FROM adoptions WHERE id = ?", (req_id,))
            row = cursor.fetchone()
            conn.close()
            self.assertEqual(row[0], '2026-10-22')
            self.assertEqual(row[1], 'Shelter Pickup', "Delivery method must not be modified by shelter date update!")

            # 2. Shelter updates transport status through valid values
            for status in ["Scheduled", "Picked Up", "In Transit", "Out for Delivery", "Delivered", "Completed"]:
                res = self.client.post(f'/shelter-update-transport-status/{req_id}', data={'transport_status': status}, follow_redirects=True)
                self.assertEqual(res.status_code, 200)
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute("SELECT transport_status FROM adoptions WHERE id = ?", (req_id,))
                current_status = cursor.fetchone()[0]
                conn.close()
                self.assertEqual(current_status, status)

            # 3. Reject invalid transport status
            res = self.client.post(f'/shelter-update-transport-status/{req_id}', data={'transport_status': 'UnknownStatus'}, follow_redirects=True)
            self.assertIn(b"Invalid transport status", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (req_id,))
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            conn.commit()
            conn.close()

    def test_adopter_delivery_method_selected_at_request_only(self):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM pets LIMIT 1")
        pet_id = cursor.fetchone()[0]

        # 1. Adopter submits request with 'Home Delivery'
        with self.client.session_transaction() as sess:
            sess['user'] = 'MethodAdopter'
            sess['user_id'] = 7712
            sess['role'] = 'Adopter'

        res = self.client.post(f'/adoption/{pet_id}', data={
            'adopter_name': 'MethodAdopter',
            'phone': '9876543210',
            'address': '789 Road, City',
            'transport_method': 'Home Delivery'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        cursor.execute("SELECT id, transport_method, transport_status, request_date FROM adoptions WHERE adopter_name = 'MethodAdopter' ORDER BY id DESC LIMIT 1")
        rec = cursor.fetchone()
        self.assertIsNotNone(rec)
        req_id, method, t_status, req_date = rec
        self.assertEqual(method, 'Home Delivery')
        self.assertIn(t_status, ['Pending', 'Transport Not Started'])
        self.assertIsNotNone(req_date)
        conn.close()

        try:
            # 2. Adopter cannot change delivery method afterwards; accessing /transport redirects to /my-requests
            res = self.client.get(f'/transport/{pet_id}', follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"cannot be changed after submission", res.data)

            # 3. Adopter's my-requests displays Delivery Method, Scheduled Date, and Transport Status view only
            res = self.client.get('/my-requests')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Delivery Method", res.data)
            self.assertIn(b"Home Delivery", res.data)
            self.assertIn(b"Scheduled Date", res.data)
            self.assertIn(b"Transport Status", res.data)
            # Ensure no edit modal exists on adopter side
            self.assertNotIn(b"adopterUpdateDeliveryModal", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id = ?", (req_id,))
            conn.commit()
            conn.close()

    def test_no_transport_provider_module_or_nav_elements(self):
        # 1. Verify no Transport provider user exists in database
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, role FROM users WHERE role IN ('Transport', 'Transport Provider') OR email = 'transport@petadoption.com'")
        transport_users = cursor.fetchall()
        conn.close()
        self.assertEqual(transport_users, [], "No Transport Provider user should exist in users table!")

        # 2. Verify navbar has no Transport role block
        navbar_path = os.path.join(os.path.dirname(__file__), "templates", "navbar.html")
        with open(navbar_path, "r", encoding="utf-8") as f:
            navbar_content = f.read()
        self.assertNotIn("session.get('role') == 'Transport'", navbar_content)
        self.assertNotIn("transport-dashboard", navbar_content)

        # 3. Verify shelter dashboard has delivery management section and profile
        with self.client.session_transaction() as sess:
            sess['user'] = 'Happy Paws Shelter'
            sess['user_id'] = 1
            sess['role'] = 'Shelter'

        res = self.client.get('/shelter-dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"deliveries-section", res.data)
        self.assertIn(b"profile-section", res.data)
        self.assertIn(b"Delivery &amp; Transport", res.data)

        # 4. Verify accessing legacy /transport-dashboard redirects shelter to /shelter-dashboard
        res = self.client.get('/transport-dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/shelter-dashboard', res.headers.get('Location', ''))

    def test_specific_shelter_messaging_workflow_and_security(self):
        # 1. Setup two distinct test shelters and their respective pets
        shelter_a_id = 9101
        shelter_b_id = 9102
        adopter_1_id = 9201
        adopter_2_id = 9202

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # Insert Shelter A and Shelter B
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Shelter Alpha', 'alpha@shelter.org', '9876543210', 'Alpha Road 1', 'pass123', 'Shelter', 'Approved')
        """, (shelter_a_id,))

        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Shelter Beta', 'beta@shelter.org', '9876543211', 'Beta Road 2', 'pass123', 'Shelter', 'Approved')
        """, (shelter_b_id,))

        # Insert Adopter 1 and Adopter 2
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Adopter One', 'adopter1@gmail.com', '9876543212', 'Adopter Lane 1', 'pass123', 'Adopter', 'Approved')
        """, (adopter_1_id,))

        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Adopter Two', 'adopter2@gmail.com', '9876543213', 'Adopter Lane 2', 'pass123', 'Adopter', 'Approved')
        """, (adopter_2_id,))

        # Insert Pet A (owned by Shelter A) and Pet B (owned by Shelter B)
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, image, shelter_id)
            VALUES ('PetAlpha', 'Retriever', '2 Years', 'Male', 'Yes', 'Friendly retriever', 'Available', 'hero.jpg', ?)
        """, (shelter_a_id,))
        pet_a_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, image, shelter_id)
            VALUES ('PetBeta', 'Persian', '1 Year', 'Female', 'Yes', 'Quiet cat', 'Available', 'hero.jpg', ?)
        """, (shelter_b_id,))
        pet_b_id = cursor.lastrowid

        conn.commit()
        conn.close()

        created_msg_ids = []

        try:
            # 2. Adopter 1 views Pet A details: verifies Shelter Alpha is shown and Contact Shelter modal is present
            with self.client.session_transaction() as sess:
                sess['user'] = 'Adopter One'
                sess['user_id'] = adopter_1_id
                sess['role'] = 'Adopter'

            res = self.client.get(f'/pet_details/{pet_a_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Shelter Alpha", res.data)
            self.assertIn(b"Contact Shelter", res.data)
            self.assertIn(b"contactShelterModal", res.data)

            # 3. Adopter 1 sends inquiry about Pet A
            msg_content = "Hello Shelter Alpha, is PetAlpha good with children?"
            res = self.client.post(f'/contact-shelter/{pet_a_id}', data={'message': msg_content}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, shelter_id, pet_id, user_id, message, status, reply FROM messages WHERE user_id = ? AND pet_id = ?", (adopter_1_id, pet_a_id))
            msg_rec = cursor.fetchone()
            self.assertIsNotNone(msg_rec)
            msg_a_id = msg_rec[0]
            created_msg_ids.append(msg_a_id)

            # Verify message is strictly linked to Shelter Alpha and Pet A
            self.assertEqual(msg_rec[1], shelter_a_id, "Message must be routed specifically to Shelter Alpha!")
            self.assertEqual(msg_rec[2], pet_a_id, "Message must be linked to Pet Alpha!")
            self.assertEqual(msg_rec[3], adopter_1_id)
            self.assertEqual(msg_rec[4], msg_content)
            self.assertEqual(msg_rec[5], 'Unread')
            self.assertIsNone(msg_rec[6])
            conn.close()

            # 4. Shelter Alpha logs in: verifies message is in their dashboard inbox
            with self.client.session_transaction() as sess:
                sess['user'] = 'Shelter Alpha'
                sess['user_id'] = shelter_a_id
                sess['role'] = 'Shelter'

            res = self.client.get('/shelter-dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"messages-section", res.data)
            self.assertIn(b"PetAlpha", res.data)
            self.assertIn(b"Adopter One", res.data)
            self.assertIn(msg_content.encode(), res.data)

            # 5. Shelter Beta logs in: verifies Shelter Beta CANNOT see Shelter Alpha's messages
            with self.client.session_transaction() as sess:
                sess['user'] = 'Shelter Beta'
                sess['user_id'] = shelter_b_id
                sess['role'] = 'Shelter'

            res = self.client.get('/shelter-dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(b"PetAlpha", res.data, "Shelter Beta must NOT see PetAlpha messages!")
            self.assertNotIn(msg_content.encode(), res.data, "Shelter Beta must NOT see messages sent to Shelter Alpha!")

            # 6. SECURITY TEST: Shelter Beta attempts to reply to Shelter Alpha's message -> BLOCKED
            res = self.client.post(f'/shelter-reply-message/{msg_a_id}', data={'reply': 'Malicious cross-shelter reply'}, follow_redirects=True)
            self.assertIn(b"Access Denied", res.data)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT reply FROM messages WHERE id = ?", (msg_a_id,))
            self.assertIsNone(cursor.fetchone()[0], "Unauthorized shelter must not be able to modify message reply!")
            conn.close()

            # 7. Shelter Alpha replies legitimately to Adopter 1
            with self.client.session_transaction() as sess:
                sess['user'] = 'Shelter Alpha'
                sess['user_id'] = shelter_a_id
                sess['role'] = 'Shelter'

            alpha_reply = "Yes, PetAlpha is wonderful with children of all ages!"
            res = self.client.post(f'/shelter-reply-message/{msg_a_id}', data={'reply': alpha_reply}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Your reply has been sent directly to the adopter", res.data)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT reply, status FROM messages WHERE id = ?", (msg_a_id,))
            rec = cursor.fetchone()
            self.assertEqual(rec[0], alpha_reply)
            self.assertEqual(rec[1], 'Read')
            conn.close()

            # 8. Adopter 1 views My Messages: sees Shelter Alpha name, PetAlpha name, their message, and Alpha's reply
            with self.client.session_transaction() as sess:
                sess['user'] = 'Adopter One'
                sess['user_id'] = adopter_1_id
                sess['role'] = 'Adopter'

            res = self.client.get('/my-messages')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Shelter Alpha", res.data)
            self.assertIn(b"PetAlpha", res.data)
            self.assertIn(msg_content.encode(), res.data)
            self.assertIn(alpha_reply.encode(), res.data)
            self.assertIn(b"Replied by Shelter", res.data)

            # 9. Adopter 2 logs in: verifies Adopter 2 CANNOT see Adopter 1's messages
            with self.client.session_transaction() as sess:
                sess['user'] = 'Adopter Two'
                sess['user_id'] = adopter_2_id
                sess['role'] = 'Adopter'

            res = self.client.get('/my-messages')
            self.assertEqual(res.status_code, 200)
            self.assertNotIn(b"PetAlpha", res.data)
            self.assertNotIn(msg_content.encode(), res.data)

            # 10. ADOPTION REQUEST WORKFLOW: Adopter 1 submits adoption request for Pet A
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO adoptions (pet_id, adopter_name, phone, address, payment_status, transport_method, request_status, payment_amount, transport_status, adopter_id, request_date)
                VALUES (?, 'Adopter One', '9876543210', '123 Adopter Lane', 'Pending', 'Home Delivery', 'Pending', 500, 'Pending', ?, date('now'))
            """, (pet_a_id, adopter_1_id))
            adoption_req_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Adopter 1 views My Requests -> sees Shelter Alpha identified
            with self.client.session_transaction() as sess:
                sess['user'] = 'Adopter One'
                sess['user_id'] = adopter_1_id
                sess['role'] = 'Adopter'

            res = self.client.get('/my-requests')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Shelter Alpha", res.data)
            self.assertIn(f"contactShelterModalReq{adoption_req_id}".encode(), res.data)

            # Adopter 1 contacts shelter directly regarding this adoption request
            req_inquiry = "Hello Shelter Alpha, when will this adoption request be reviewed?"
            res = self.client.post(f'/contact-shelter/{pet_a_id}', data={
                'adoption_id': str(adoption_req_id),
                'message': req_inquiry
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, shelter_id, pet_id, subject, message FROM messages WHERE user_id = ? AND subject LIKE '%Adoption%'", (adopter_1_id,))
            req_msg_row = cursor.fetchone()
            self.assertIsNotNone(req_msg_row)
            created_msg_ids.append(req_msg_row[0])
            self.assertEqual(req_msg_row[1], shelter_a_id, "Adoption request message must be routed to Shelter Alpha!")
            self.assertEqual(req_msg_row[2], pet_a_id)
            self.assertIn(f"Adoption #{adoption_req_id}", req_msg_row[3])
            conn.close()

            # 11. GENERAL CONTACT WITH PET_ID: Contact page pre-populates pet and shelter
            res = self.client.get(f'/contact?pet_id={pet_a_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Shelter Alpha", res.data)
            self.assertIn(b"Inquiry regarding PetAlpha", res.data)

            res = self.client.post('/contact', data={
                'name': 'Adopter One',
                'email': 'adopter1@example.com',
                'subject': 'Inquiry regarding PetAlpha',
                'message': 'General inquiry routed through contact page to Shelter Alpha.',
                'shelter_id': str(shelter_a_id),
                'pet_id': str(pet_a_id)
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, shelter_id, pet_id FROM messages WHERE message LIKE '%General inquiry routed%'")
            gen_row = cursor.fetchone()
            self.assertIsNotNone(gen_row)
            created_msg_ids.append(gen_row[0])
            self.assertEqual(gen_row[1], shelter_a_id)
            self.assertEqual(gen_row[2], pet_a_id)
            conn.close()

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            for mid in created_msg_ids:
                cursor.execute("DELETE FROM messages WHERE id = ?", (mid,))
            cursor.execute("DELETE FROM messages WHERE user_id IN (?, ?)", (adopter_1_id, adopter_2_id))
            cursor.execute("DELETE FROM adoptions WHERE pet_id IN (?, ?)", (pet_a_id, pet_b_id))
            cursor.execute("DELETE FROM pets WHERE id IN (?, ?)", (pet_a_id, pet_b_id))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?, ?)", (shelter_a_id, shelter_b_id, adopter_1_id, adopter_2_id))
            conn.commit()
            conn.close()

    def test_profile_editing_for_adopter_and_shelter(self):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email IN ('prof_adopter@test.com', 'prof_shelter@test.com', 'collision@test.com')")

        # Create test users
        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Profile Adopter Test', 'prof_adopter@test.com', 'initialpass123', 'Adopter', '9876500001', '101 Adopter Street', 'Approved')
        """)
        adopter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Profile Shelter Test', 'prof_shelter@test.com', 'initialpass123', 'Shelter', '9876500002', '202 Shelter Avenue', 'Approved')
        """)
        shelter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Collision User', 'collision@test.com', 'initialpass123', 'Adopter', '9876500003', '303 Collision Road', 'Approved')
        """)
        collision_id = cursor.lastrowid

        conn.commit()
        conn.close()

        try:
            # 1. Unauthenticated user accessing /profile -> redirects to login
            res = self.client.get('/profile')
            self.assertEqual(res.status_code, 302)
            self.assertIn('/login', res.headers.get('Location', ''))

            # 2. Adopter accessing /profile -> 200 OK, renders profile and edit modal
            with self.client.session_transaction() as sess:
                sess['user'] = 'Profile Adopter Test'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get('/profile')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Profile Adopter Test", res.data)
            self.assertIn(b"prof_adopter@test.com", res.data)
            self.assertIn(b"editProfileModal", res.data)
            self.assertIn(b"Edit Your Profile", res.data)

            # 3. Adopter updates profile with valid details
            update_data = {
                'fullname': 'Updated Adopter Name',
                'email': 'updated_adopter@test.com',
                'phone': '9123456780',
                'address': '789 Updated Blossom Lane, City',
                'new_password': 'newpassword123'
            }
            res = self.client.post('/profile', data=update_data, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Your profile has been updated successfully", res.data)
            self.assertIn(b"Updated Adopter Name", res.data)
            self.assertIn(b"updated_adopter@test.com", res.data)

            # Check DB persistence
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, email, phone, address, password FROM users WHERE id = ?", (adopter_id,))
            user_row = cursor.fetchone()
            self.assertEqual(user_row[0], 'Updated Adopter Name')
            self.assertEqual(user_row[1], 'updated_adopter@test.com')
            self.assertEqual(user_row[2], '9123456780')
            self.assertEqual(user_row[3], '789 Updated Blossom Lane, City')
            self.assertEqual(user_row[4], 'newpassword123')
            conn.close()

            # 4. Adopter validation failure: invalid phone
            res = self.client.post('/profile', data={
                'fullname': 'Updated Adopter Name',
                'email': 'updated_adopter@test.com',
                'phone': '12345',  # Invalid phone
                'address': '789 Updated Blossom Lane, City',
                'new_password': ''
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"valid 10-digit mobile number", res.data)

            # 5. Adopter validation failure: email collision with another user
            res = self.client.post('/profile', data={
                'fullname': 'Updated Adopter Name',
                'email': 'collision@test.com',  # Existing user email
                'phone': '9123456780',
                'address': '789 Updated Blossom Lane, City',
                'new_password': ''
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"already in use by another account", res.data)

            # 6. Shelter visiting /profile is redirected to shelter dashboard profile section
            with self.client.session_transaction() as sess:
                sess['user'] = 'Profile Shelter Test'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            res = self.client.get('/profile')
            self.assertEqual(res.status_code, 302)
            self.assertIn('shelter-dashboard#profile-section', res.headers.get('Location', ''))

            # 7. Shelter viewing shelter dashboard sees profile and edit modal
            res = self.client.get('/shelter-dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"profile-section", res.data)
            self.assertIn(b"editShelterProfileModal", res.data)
            self.assertIn(b"Profile Shelter Test", res.data)

            # 8. Shelter updates profile via /shelter-edit-profile
            shelter_update_data = {
                'fullname': 'Updated Shelter Care Org',
                'email': 'updated_shelter@test.com',
                'phone': '9876543219',
                'address': '456 Rescue Way, Headquarters Complex',
                'new_password': 'shelternewpass456'
            }
            res = self.client.post('/shelter-edit-profile', data=shelter_update_data, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Shelter profile updated successfully", res.data)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, email, phone, address, password FROM users WHERE id = ?", (shelter_id,))
            sh_row = cursor.fetchone()
            self.assertEqual(sh_row[0], 'Updated Shelter Care Org')
            self.assertEqual(sh_row[1], 'updated_shelter@test.com')
            self.assertEqual(sh_row[2], '9876543219')
            self.assertEqual(sh_row[3], '456 Rescue Way, Headquarters Complex')
            self.assertEqual(sh_row[4], 'shelternewpass456')
            conn.close()

            # 9. Shelter validation failure: collision with another account
            res = self.client.post('/shelter-edit-profile', data={
                'fullname': 'Updated Shelter Care Org',
                'email': 'collision@test.com',
                'phone': '9876543219',
                'address': '456 Rescue Way, Headquarters Complex',
                'new_password': ''
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"already in use by another account", res.data)

            # 10. Access control: Adopter cannot edit shelter profile
            with self.client.session_transaction() as sess:
                sess['user'] = 'Updated Adopter Name'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.post('/shelter-edit-profile', data=shelter_update_data, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Access Denied", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?)", (adopter_id, shelter_id, collision_id))
            conn.commit()
            conn.close()

    def test_continuous_two_way_conversation_workflow(self):
        """
        Verify continuous two-way back-and-forth messaging between Adopter and Shelter:
        - One conversation -> many messages architecture (conversations & messages tables).
        - Reuses same conversation_id; no new conversation created for subsequent messages.
        - Back-and-forth back-and-forth without single-reply restrictions.
        - Chronological order (oldest at top, newest at bottom).
        - Input boxes continuously present ("Type your message..." and "Type your reply...").
        - Strict isolation and security: unauthorized shelters/adopters blocked.
        """
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email IN ('conv_adopter@test.com', 'conv_shelter_a@test.com', 'conv_shelter_b@test.com', 'unrelated_adopter@test.com')")

        # 1. Setup test users and pet
        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Continuous Adopter', 'conv_adopter@test.com', 'pass123', 'Adopter', '9876511111', '100 Adopter Blvd', 'Approved')
        """)
        adopter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Continuous Shelter Alpha', 'conv_shelter_a@test.com', 'pass123', 'Shelter', '9876522222', '200 Shelter Way', 'Approved')
        """)
        shelter_a_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Continuous Shelter Beta', 'conv_shelter_b@test.com', 'pass123', 'Shelter', '9876533333', '300 Shelter Lane', 'Approved')
        """)
        shelter_b_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Unrelated Adopter', 'unrelated_adopter@test.com', 'pass123', 'Adopter', '9876544444', '400 Other Way', 'Approved')
        """)
        other_adopter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, shelter_id, status)
            VALUES ('Milo Dog', 'Beagle', '2 Years', 'Male', 'Yes', 'Friendly and playful Beagle pup.', ?, 'Available')
        """, (shelter_a_id,))
        pet_id = cursor.lastrowid

        conn.commit()
        conn.close()

        created_conv_id = None

        try:
            # 2. STEP 1: Adopter sends message 1 about Milo Dog
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            msg_1 = "Hello Shelter Alpha, is Milo good with other dogs?"
            res = self.client.post(f'/contact-shelter/{pet_id}', data={'message': msg_1}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # Verify conversation was created
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, adopter_id, shelter_id, pet_id, status FROM conversations WHERE adopter_id = ? AND shelter_id = ? AND pet_id = ?", (adopter_id, shelter_a_id, pet_id))
            conv_row = cursor.fetchone()
            self.assertIsNotNone(conv_row, "A conversation record must be created")
            created_conv_id = conv_row[0]
            self.assertEqual(conv_row[4], 'Open', "Conversation must start with Open status")

            # Verify message 1 is recorded under this conversation_id
            cursor.execute("SELECT id, conversation_id, sender_id, sender_type, message FROM messages WHERE conversation_id = ?", (created_conv_id,))
            msgs = cursor.fetchall()
            self.assertEqual(len(msgs), 1)
            self.assertEqual(msgs[0][2], adopter_id)
            self.assertEqual(msgs[0][3], 'Adopter')
            self.assertEqual(msgs[0][4], msg_1)
            conn.close()

            # 3. STEP 2: Shelter Alpha logs in, views conversation, sends Reply 1
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Shelter Alpha'
                sess['user_id'] = shelter_a_id
                sess['role'] = 'Shelter'

            res = self.client.get(f'/conversation/{created_conv_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(msg_1.encode(), res.data)
            self.assertIn(b"Type your reply...", res.data, "Shelter must have an input box with placeholder 'Type your reply...'")
            self.assertIn(b"Send Reply", res.data)

            reply_1 = "Yes, Milo loves playing with other dogs at the park!"
            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': reply_1}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(reply_1.encode(), res.data)

            # Verify reply 1 added to SAME conversation_id
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversations WHERE adopter_id = ? AND shelter_id = ?", (adopter_id, shelter_a_id))
            self.assertEqual(cursor.fetchone()[0], 1, "Must NOT create a new conversation; same conversation must be reused")
            cursor.execute("SELECT sender_type, message FROM messages WHERE conversation_id = ? ORDER BY id ASC", (created_conv_id,))
            thread = cursor.fetchall()
            self.assertEqual(len(thread), 2)
            self.assertEqual(thread[1][0], 'Shelter')
            self.assertEqual(thread[1][1], reply_1)
            conn.close()

            # 4. STEP 3: Adopter logs back in: sends Message 2 (proving they are NOT blocked after reply)
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get(f'/conversation/{created_conv_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Type your message...", res.data, "Adopter must have an input box with placeholder 'Type your message...'")
            self.assertIn(b"Send", res.data)
            self.assertIn(reply_1.encode(), res.data)

            msg_2 = "That is wonderful news! Does he require a large yard?"
            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': msg_2}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(msg_2.encode(), res.data)

            # 5. STEP 4: Shelter Alpha replies again (Reply 2)
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Shelter Alpha'
                sess['user_id'] = shelter_a_id
                sess['role'] = 'Shelter'

            reply_2 = "A small yard or regular walks will keep him very happy."
            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': reply_2}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # 6. STEP 5: Adopter sends Message 3 (3rd round of back-and-forth)
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            msg_3 = "Can I schedule a visit to meet Milo this Saturday?"
            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': msg_3}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # 7. STEP 6: Shelter Alpha replies again (Reply 3)
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Shelter Alpha'
                sess['user_id'] = shelter_a_id
                sess['role'] = 'Shelter'

            reply_3 = "Saturday at 11 AM works perfectly. See you then!"
            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': reply_3}, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            # 8. STEP 7: Database Verification of full thread
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            # Still exactly 1 conversation
            cursor.execute("SELECT id, status FROM conversations WHERE adopter_id = ? AND shelter_id = ?", (adopter_id, shelter_a_id))
            convs = cursor.fetchall()
            self.assertEqual(len(convs), 1)
            self.assertEqual(convs[0][1], 'Open', "Conversation status must remain Open throughout unlimited exchanges")

            # 6 messages total in exact chronological order
            cursor.execute("SELECT sender_type, message FROM messages WHERE conversation_id = ? ORDER BY id ASC", (created_conv_id,))
            full_thread = cursor.fetchall()
            self.assertEqual(len(full_thread), 6)
            expected_exchanges = [
                ('Adopter', msg_1),
                ('Shelter', reply_1),
                ('Adopter', msg_2),
                ('Shelter', reply_2),
                ('Adopter', msg_3),
                ('Shelter', reply_3)
            ]
            for idx, (exp_sender, exp_msg) in enumerate(expected_exchanges):
                self.assertEqual(full_thread[idx][0], exp_sender, f"Message {idx+1} sender mismatch")
                self.assertEqual(full_thread[idx][1], exp_msg, f"Message {idx+1} content mismatch")
            conn.close()

            # 9. STEP 8: Verify Chronological Order in rendered template
            res = self.client.get(f'/conversation/{created_conv_id}')
            self.assertEqual(res.status_code, 200)
            data_str = res.data.decode('utf-8')
            pos_1 = data_str.find(msg_1)
            pos_2 = data_str.find(reply_1)
            pos_3 = data_str.find(msg_2)
            pos_4 = data_str.find(reply_2)
            pos_5 = data_str.find(msg_3)
            pos_6 = data_str.find(reply_3)
            self.assertTrue(pos_1 < pos_2 < pos_3 < pos_4 < pos_5 < pos_6, "Messages must appear in strict chronological order")

            # 10. STEP 9: Verify Input Box still present and available for next round
            self.assertIn("Type your reply...", data_str)
            self.assertIn("Send Reply", data_str)

            # 11. STEP 10: Check Adopter's /my-messages view has continuous reply input
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get('/my-messages')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Type your message...", res.data, "my-messages must have input box 'Type your message...'")
            self.assertIn(b"Continuous Shelter Alpha", res.data)
            self.assertIn(b"Milo Dog", res.data)

            # 12. STEP 11: Check Shelter's /shelter-dashboard view has continuous reply input
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Shelter Alpha'
                sess['user_id'] = shelter_a_id
                sess['role'] = 'Shelter'

            res = self.client.get('/shelter-dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Type your reply...", res.data, "shelter-dashboard must have input box 'Type your reply...'")
            self.assertIn(b"Continuous Adopter", res.data)

            # 13. STEP 12: STRICT SECURITY & ISOLATION CHECKS
            # A. Unauthenticated user accessing conversation -> redirect to login
            with self.client.session_transaction() as sess:
                sess.clear()

            res = self.client.get(f'/conversation/{created_conv_id}')
            self.assertEqual(res.status_code, 302)
            self.assertIn('/login', res.headers.get('Location', ''))

            # B. Cross-shelter isolation: Shelter Beta CANNOT view Shelter Alpha's conversation
            with self.client.session_transaction() as sess:
                sess['user'] = 'Continuous Shelter Beta'
                sess['user_id'] = shelter_b_id
                sess['role'] = 'Shelter'

            res = self.client.get(f'/conversation/{created_conv_id}', follow_redirects=True)
            self.assertIn(b"Access Denied", res.data)
            self.assertNotIn(msg_1.encode(), res.data)

            # C. Cross-shelter isolation: Shelter Beta CANNOT send messages into Shelter Alpha's conversation
            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': 'Hacked by Shelter Beta'}, follow_redirects=True)
            self.assertIn(b"Access Denied", res.data)

            # Verify no unauthorized message was inserted
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE conversation_id = ? AND message LIKE '%Hacked%'", (created_conv_id,))
            self.assertEqual(cursor.fetchone()[0], 0)
            conn.close()

            # D. Cross-adopter isolation: Unrelated Adopter CANNOT view or send to this conversation
            with self.client.session_transaction() as sess:
                sess['user'] = 'Unrelated Adopter'
                sess['user_id'] = other_adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get(f'/conversation/{created_conv_id}', follow_redirects=True)
            self.assertIn(b"Access Denied", res.data)

            res = self.client.post(f'/conversation/{created_conv_id}/send', data={'message': 'Hacked by other adopter'}, follow_redirects=True)
            self.assertIn(b"Access Denied", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            if created_conv_id:
                cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (created_conv_id,))
                cursor.execute("DELETE FROM conversations WHERE id = ?", (created_conv_id,))
            cursor.execute("DELETE FROM messages WHERE user_id IN (?, ?)", (adopter_id, other_adopter_id))
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?, ?)", (adopter_id, shelter_a_id, shelter_b_id, other_adopter_id))
            conn.commit()
            conn.close()

    def test_pet_details_shows_full_picture_and_lightbox(self):
        """
        Verify that viewing pet details displays the full uncropped picture of the pet:
        - Image container does not crop or cut off parts of the photo.
        - Provides full picture display and interactive lightbox modal for full-resolution view.
        """
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email IN ('full_photo_adopter@test.com', 'full_photo_shelter@test.com')")

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Full Photo Adopter', 'full_photo_adopter@test.com', 'pass123', 'Adopter', '9876599999', '500 Picture Way', 'Approved')
        """)
        adopter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Full Photo Shelter', 'full_photo_shelter@test.com', 'pass123', 'Shelter', '9876588888', '600 Picture Lane', 'Approved')
        """)
        shelter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, shelter_id, status, image)
            VALUES ('FullPicPet', 'Golden Retriever', '3 Years', 'Female', 'Yes', 'A loving dog with full coat.', ?, 'Available', 'hero_cartoon_pets.jpg')
        """, (shelter_id,))
        pet_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            with self.client.session_transaction() as sess:
                sess['user'] = 'Full Photo Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get(f'/pet_details/{pet_id}')
            self.assertEqual(res.status_code, 200)

            # 1. Verify uncropped photo wrapper and pet image tag
            self.assertIn(b"pet-photo-wrapper", res.data, "Must use pet-photo-wrapper to avoid image cropping")
            self.assertIn(b"pet-detail-img", res.data)
            self.assertIn(b"hero_cartoon_pets.jpg", res.data)

            # 2. Verify full picture badge and lightbox modal triggers
            self.assertIn(b"fullPetImageModal", res.data, "Must include fullPetImageModal for viewing full picture")
            self.assertIn(b"Full Picture", res.data)
            self.assertIn(b"data-bs-target=\"#fullPetImageModal\"", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (adopter_id, shelter_id))
            conn.commit()
            conn.close()

    def test_null_pet_image_renders_fallback_without_type_error(self):
        """
        Verify that a pet with a NULL or empty image does NOT cause TypeError:
        - Safely renders fallback image in /pets
        - Safely renders fallback in /pet_details/<id>
        - Safely renders fallback in /shelter-pets
        """
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email IN ('null_img_sh@test.com', 'null_img_ad@test.com')")

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Null Image Shelter', 'null_img_sh@test.com', 'pass123', 'Shelter', '9876577777', '700 Null Lane', 'Approved')
        """)
        shelter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, password, role, phone, address, account_status)
            VALUES ('Null Image Adopter', 'null_img_ad@test.com', 'pass123', 'Adopter', '9876566666', '800 Null Blvd', 'Approved')
        """)
        adopter_id = cursor.lastrowid

        # Insert pet with NULL image
        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, shelter_id, status, image)
            VALUES ('NoImagePet', 'Pug', '1 Year', 'Male', 'Yes', 'Pug with no uploaded photo.', ?, 'Available', NULL)
        """, (shelter_id,))
        pet_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            # 1. Adopter visits /pets -> must render 200 without TypeError
            with self.client.session_transaction() as sess:
                sess['user'] = 'Null Image Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get('/pets')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"NoImagePet", res.data)
            self.assertIn(b"hero.jpg", res.data)

            # 2. Adopter visits /pet_details/<pet_id> -> must render 200 without TypeError
            res = self.client.get(f'/pet_details/{pet_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"NoImagePet", res.data)
            self.assertIn(b"hero.jpg", res.data)

            # 3. Shelter visits /shelter-pets -> must render 200 without TypeError
            with self.client.session_transaction() as sess:
                sess['user'] = 'Null Image Shelter'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            res = self.client.get('/shelter-pets')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"NoImagePet", res.data)
            self.assertIn(b"hero.jpg", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (shelter_id, adopter_id))
            conn.commit()
            conn.close()

    def test_pet_age_dropdown_templates_and_no_zero_or_manual_input(self):
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        target_templates = ["shelter_add_pet.html", "shelter_edit_pet.html", "add_pet.html", "edit_pet.html"]
        for tmpl in target_templates:
            filepath = os.path.join(templates_dir, tmpl)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Ensure free-text input for age is completely removed
            self.assertNotIn('type="text"\n                        name="age"', content, f"Free-text age input found in {tmpl}")
            self.assertNotIn('name="age"\n                        class="form-control"', content, f"Free-text age input found in {tmpl}")
            self.assertNotIn('type="text" name="age"', content, f"Free-text age input found in {tmpl}")

            # Ensure age_number and age_unit selects exist
            self.assertIn('name="age_number"', content, f"age_number select missing in {tmpl}")
            self.assertIn('name="age_unit"', content, f"age_unit select missing in {tmpl}")

            # Ensure range 1 to 30 is generated without 0
            self.assertIn('range(1, 31)', content, f"range(1, 31) missing in {tmpl}")
            self.assertNotIn('range(0,', content, f"range starting at 0 found in {tmpl}")
            self.assertNotIn('value="0"', content, f"Value 0 found in {tmpl}")

            # Ensure exactly Months and Years options exist for unit
            self.assertIn('value="Months"', content, f"Months unit option missing in {tmpl}")
            self.assertIn('value="Years"', content, f"Years unit option missing in {tmpl}")

    def test_shelter_add_pet_dropdown_workflow_and_rejection(self):
        shelter_id = 9331
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Age Test Shelter', 'age_shelter@test.org', '9876543210', '123 Test St', 'pass123', 'Shelter', 'Approved')
        """, (shelter_id,))
        conn.commit()
        conn.close()

        created_pet_ids = []
        try:
            with self.client.session_transaction() as sess:
                sess['user'] = 'Age Test Shelter'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            # 1. Valid add pet with 6 Months
            res = self.client.post('/shelter-add-pet', data={
                'name': 'PuppySix',
                'breed': 'Labrador',
                'age_number': '6',
                'age_unit': 'Months',
                'gender': 'Male',
                'vaccinated': 'Yes',
                'description': 'Very sweet and playful puppy'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, age FROM pets WHERE name = 'PuppySix' AND shelter_id = ?", (shelter_id,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            p1_id, p1_age = row
            created_pet_ids.append(p1_id)
            self.assertEqual(p1_age, "6 Months")

            # 2. Valid add pet with 1 Year (singular normalization)
            res = self.client.post('/shelter-add-pet', data={
                'name': 'YoungDog',
                'breed': 'Beagle',
                'age_number': '1',
                'age_unit': 'Years',
                'gender': 'Female',
                'vaccinated': 'Yes',
                'description': 'Friendly beagle one year old'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            cursor.execute("SELECT id, age FROM pets WHERE name = 'YoungDog' AND shelter_id = ?", (shelter_id,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            p2_id, p2_age = row
            created_pet_ids.append(p2_id)
            self.assertEqual(p2_age, "1 Year")

            # 3. Reject age_number = 0
            res = self.client.post('/shelter-add-pet', data={
                'name': 'ZeroPet',
                'breed': 'Pug',
                'age_number': '0',
                'age_unit': 'Years',
                'gender': 'Male',
                'vaccinated': 'Yes',
                'description': 'Cute pug puppy with invalid 0 age'
            })
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"between 1 and 30", res.data)
            cursor.execute("SELECT id FROM pets WHERE name = 'ZeroPet'")
            self.assertIsNone(cursor.fetchone())

            # 4. Reject negative age_number
            res = self.client.post('/shelter-add-pet', data={
                'name': 'NegativePet',
                'breed': 'Pug',
                'age_number': '-3',
                'age_unit': 'Months',
                'gender': 'Male',
                'vaccinated': 'Yes',
                'description': 'Cute pug puppy with negative age'
            })
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"between 1 and 30", res.data)
            cursor.execute("SELECT id FROM pets WHERE name = 'NegativePet'")
            self.assertIsNone(cursor.fetchone())

            # 5. Reject empty unit
            res = self.client.post('/shelter-add-pet', data={
                'name': 'MissingUnitPet',
                'breed': 'Pug',
                'age_number': '2',
                'age_unit': '',
                'gender': 'Male',
                'vaccinated': 'Yes',
                'description': 'Cute pug puppy missing age unit'
            })
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Please select both an age number and a unit", res.data)
            cursor.execute("SELECT id FROM pets WHERE name = 'MissingUnitPet'")
            self.assertIsNone(cursor.fetchone())

            # 6. Reject invalid unit
            res = self.client.post('/shelter-add-pet', data={
                'name': 'InvalidUnitPet',
                'breed': 'Pug',
                'age_number': '2',
                'age_unit': 'Weeks',
                'gender': 'Male',
                'vaccinated': 'Yes',
                'description': 'Cute pug puppy with weeks unit'
            })
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Age unit must be either Months or Years", res.data)
            cursor.execute("SELECT id FROM pets WHERE name = 'InvalidUnitPet'")
            self.assertIsNone(cursor.fetchone())
            conn.close()

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            if created_pet_ids:
                cursor.execute(f"DELETE FROM pets WHERE id IN ({','.join(['?']*len(created_pet_ids))})", created_pet_ids)
            cursor.execute("DELETE FROM users WHERE id = ?", (shelter_id,))
            conn.commit()
            conn.close()

    def test_shelter_edit_pet_dropdown_preselection(self):
        shelter_id = 9332
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Preselect Shelter', 'preselect@shelter.org', '9876543210', '456 Test Ave', 'pass123', 'Shelter', 'Approved')
        """, (shelter_id,))

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, image, shelter_id)
            VALUES ('PreselectDog', 'Husky', '2 Years', 'Male', 'Yes', 'Beautiful husky dog', 'Available', 'hero.jpg', ?)
        """, (shelter_id,))
        pet_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            with self.client.session_transaction() as sess:
                sess['user'] = 'Preselect Shelter'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            # 1. GET edit page: verify 2 and Years are pre-selected
            res = self.client.get(f'/shelter-edit-pet/{pet_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'value="2" selected', res.data)
            self.assertIn(b'value="Years" selected', res.data)

            # 2. Update pet age to 5 Months via dropdown
            res = self.client.post(f'/shelter-edit-pet/{pet_id}', data={
                'name': 'PreselectDog',
                'breed': 'Husky',
                'age_number': '5',
                'age_unit': 'Months',
                'gender': 'Male',
                'vaccinated': 'Yes',
                'description': 'Beautiful husky dog updated description',
                'status': 'Available'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT age FROM pets WHERE id = ?", (pet_id,))
            self.assertEqual(cursor.fetchone()[0], "5 Months")
            conn.close()

            # 3. GET edit page again: verify 5 and Months are pre-selected
            res = self.client.get(f'/shelter-edit-pet/{pet_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'value="5" selected', res.data)
            self.assertIn(b'value="Months" selected', res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            cursor.execute("DELETE FROM users WHERE id = ?", (shelter_id,))
            conn.commit()
            conn.close()

    def test_pet_age_display_with_units_across_platform(self):
        shelter_id = 9333
        adopter_id = 9334
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Display Shelter', 'display@shelter.org', '9876543210', '789 Display Rd', 'pass123', 'Shelter', 'Approved')
        """, (shelter_id,))

        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Display Adopter', 'display_adopter@test.org', '9876543210', '101 Adopter Rd', 'pass123', 'Adopter', 'Approved')
        """, (adopter_id,))

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, image, shelter_id)
            VALUES ('DisplayPet', 'Samoyed', '4 Years', 'Female', 'Yes', 'Fluffy white samoyed', 'Available', 'hero.jpg', ?)
        """, (shelter_id,))
        pet_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            # 1. Check /pets catalog shows '4 Years' with age icon as adopter
            with self.client.session_transaction() as sess:
                sess['user'] = 'Display Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res = self.client.get('/pets')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"DisplayPet", res.data)
            self.assertIn(b"4 Years", res.data)

            # 2. Check /pet_details/<id> shows '4 Years' as adopter
            res = self.client.get(f'/pet_details/{pet_id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"DisplayPet", res.data)
            self.assertIn(b"4 Years", res.data)

            # 3. Check /shelter-pets shows 'Age: 4 Years' as shelter
            with self.client.session_transaction() as sess:
                sess['user'] = 'Display Shelter'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            res = self.client.get('/shelter-pets')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"DisplayPet", res.data)
            self.assertIn(b"4 Years", res.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pets WHERE id = ?", (pet_id,))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (shelter_id, adopter_id))
            conn.commit()
            conn.close()

    def test_adoption_requests_ordering_and_sequential_numbering(self):
        shelter_id = 9555
        adopter_id = 9556
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Order Shelter', 'order@shelter.org', '9876543210', '123 Shelter Way', 'pass123', 'Shelter', 'Approved')
        """, (shelter_id,))

        cursor.execute("""
            INSERT OR REPLACE INTO users (id, fullname, email, phone, address, password, role, account_status)
            VALUES (?, 'Order Adopter', 'order_adopter@test.org', '9876543210', '456 Adopter Way', 'pass123', 'Adopter', 'Approved')
        """, (adopter_id,))

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, image, shelter_id)
            VALUES ('PetOne', 'Beagle', '1 Year', 'Male', 'Yes', 'Puppy one', 'Available', 'hero.jpg', ?)
        """, (shelter_id,))
        pet1_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO pets (name, breed, age, gender, vaccinated, description, status, image, shelter_id)
            VALUES ('PetTwo', 'Poodle', '2 Years', 'Female', 'Yes', 'Puppy two', 'Available', 'hero.jpg', ?)
        """, (shelter_id,))
        pet2_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method, transport_status)
            VALUES (?, 'Order Adopter', '9876543210', '456 Adopter Way', 'Approved', 'Paid', 500, 'Shelter Pickup', 'Scheduled')
        """, (pet1_id,))
        req1_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO adoptions (pet_id, adopter_name, phone, address, request_status, payment_status, payment_amount, transport_method, transport_status)
            VALUES (?, 'Order Adopter', '9876543210', '456 Adopter Way', 'Pending', 'Pending', 500, 'Home Delivery', 'Pending')
        """, (pet2_id,))
        req2_id = cursor.lastrowid

        conn.commit()
        conn.close()

        try:
            # 1. As shelter, test /shelter-requests: requests are ordered chronologically and numbered #1, #2
            with self.client.session_transaction() as sess:
                sess['user'] = 'Order Shelter'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            res = self.client.get('/shelter-requests')
            self.assertEqual(res.status_code, 200)
            html = res.data.decode('utf-8')
            # Verify #1 and #2 exist in rendered output
            self.assertIn("#1", html)
            self.assertIn("#2", html)
            # PetOne (req1) appears before PetTwo (req2) in chronological ascending order
            p1_pos = html.lower().find("petone")
            p2_pos = html.lower().find("pettwo")
            self.assertNotEqual(p1_pos, -1, "PetOne should be rendered in shelter requests")
            self.assertNotEqual(p2_pos, -1, "PetTwo should be rendered in shelter requests")
            self.assertTrue(p1_pos < p2_pos, "Requests must appear in chronological order (Request #1 first, #2 second)!")
            # Verify action buttons and modals are present
            self.assertIn(f"approveModal{req2_id}", html)
            self.assertIn(f"/approve/{req2_id}", html)
            self.assertIn(f"/reject/{req2_id}", html)

            # 2. Check /shelter-dashboard pending requests table
            res_dash = self.client.get('/shelter-dashboard')
            self.assertEqual(res_dash.status_code, 200)
            dash_html = res_dash.data.decode('utf-8')
            self.assertIn("#1", dash_html)
            self.assertIn(f"dashApproveModal{req2_id}", dash_html)

            # 3. Check /my-requests as adopter
            with self.client.session_transaction() as sess:
                sess['user'] = 'Order Adopter'
                sess['user_id'] = adopter_id
                sess['role'] = 'Adopter'

            res_reqs = self.client.get('/my-requests')
            self.assertEqual(res_reqs.status_code, 200)
            my_html = res_reqs.data.decode('utf-8')
            self.assertIn("Request #1", my_html)
            self.assertIn("Request #2", my_html)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adoptions WHERE id IN (?, ?)", (req1_id, req2_id))
            cursor.execute("DELETE FROM pets WHERE id IN (?, ?)", (pet1_id, pet2_id))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (shelter_id, adopter_id))
            conn.commit()
            conn.close()

    def test_shelter_profile_update_and_synchronization(self):
        """
        Verify complete shelter profile update:
        - Edit name, email, phone, address, and password.
        - Verify database row updates correctly.
        - Verify session['user'] updates immediately.
        - Verify that keeping the current email works and doesn't trigger false duplicate collision.
        - Verify case-insensitive duplicate collision prevention against other users.
        - Verify organization names with commas/parentheses (e.g. 'Paws, Care (HQ)') are accepted.
        - Verify past messages sent by this shelter have their sender name synchronized.
        """
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email IN ('original_shelter@test.com', 'other_shelter@test.com')")
        cursor.execute("""
            INSERT INTO users (fullname, email, phone, address, password, role, account_status)
            VALUES ('Original Shelter', 'original_shelter@test.com', '9876500001', '101 Original St', 'pass123', 'Shelter', 'Approved')
        """)
        shelter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (fullname, email, phone, address, password, role, account_status)
            VALUES ('Other Shelter', 'other_shelter@test.com', '9876500002', '102 Other St', 'pass123', 'Shelter', 'Approved')
        """)
        other_shelter_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO messages (conversation_id, sender_id, sender_type, message, sent_at, is_read, shelter_id, name)
            VALUES (99999, ?, 'Shelter', 'Hello adopter!', '2026-09-26 10:00:00', 1, ?, 'Original Shelter')
        """, (shelter_id, shelter_id))
        msg_id = cursor.lastrowid
        conn.commit()
        conn.close()

        try:
            with self.client.session_transaction() as sess:
                sess['user'] = 'Original Shelter'
                sess['user_id'] = shelter_id
                sess['role'] = 'Shelter'

            # 1. Update shelter with punctuation in name and same email (must succeed)
            res = self.client.post('/shelter-edit-profile', data={
                'fullname': 'Happy Paws, Inc. (Main)',
                'email': 'original_shelter@test.com',
                'phone': '9876500009',
                'address': '789 Updated Avenue, Suite 100',
                'new_password': 'newpassword456'
            }, follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Shelter profile updated successfully!", res.data)
            self.assertIn(b"Happy Paws, Inc. (Main)", res.data)

            # Verify database record
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("SELECT fullname, email, phone, address, password FROM users WHERE id = ?", (shelter_id,))
            row = cursor.fetchone()
            self.assertEqual(row[0], 'Happy Paws, Inc. (Main)')
            self.assertEqual(row[1], 'original_shelter@test.com')
            self.assertEqual(row[2], '9876500009')
            self.assertEqual(row[3], '789 Updated Avenue, Suite 100')
            self.assertEqual(row[4], 'newpassword456')

            # Verify message name synchronization
            cursor.execute("SELECT name FROM messages WHERE id = ?", (msg_id,))
            self.assertEqual(cursor.fetchone()[0], 'Happy Paws, Inc. (Main)')
            conn.close()

            # Verify session user updated
            with self.client.session_transaction() as sess:
                self.assertEqual(sess['user'], 'Happy Paws, Inc. (Main)')

            # 2. Case-insensitive collision rejection
            res_coll = self.client.post('/shelter-edit-profile', data={
                'fullname': 'Happy Paws, Inc. (Main)',
                'email': 'OTHER_SHELTER@TEST.COM',
                'phone': '9876500009',
                'address': '789 Updated Avenue, Suite 100',
                'new_password': ''
            }, follow_redirects=True)
            self.assertEqual(res_coll.status_code, 200)
            self.assertIn(b"already in use by another account", res_coll.data)

        finally:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (shelter_id, other_shelter_id))
            conn.commit()
            conn.close()

if __name__ == '__main__':
    unittest.main()


