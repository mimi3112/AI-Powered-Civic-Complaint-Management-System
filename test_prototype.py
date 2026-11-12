import os
import io
import unittest
from app import create_app
from config import Config
from models import db
from models.user import User
from models.complaint import Complaint, StatusHistory

class TestConfig(Config):
    """Test configuration using an isolated in-memory or test SQLite database."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'test_uploads')

class PrototypeTestCase(unittest.TestCase):
    """Comprehensive test suite covering TEST 1 through TEST 23 plus full module tests."""

    @classmethod
    def setUpClass(cls):
        os.makedirs(TestConfig.UPLOAD_FOLDER, exist_ok=True)

    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_user(self, name, email, password, role):
        return self.client.post('/register', data={
            'name': name,
            'email': email,
            'password': password,
            'role': role
        }, follow_redirects=True)

    def login_user(self, email, password):
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=False)

    def submit_test_complaint(self, title='Test Complaint', description='Test Description', location='Sector 4, Main Market', category='Roads & Potholes', priority='High', image=None):
        data = {
            'title': title,
            'description': description,
            'location': location,
            'category': category,
            'priority': priority
        }
        if image:
            data['image'] = image
        return self.client.post('/citizen/submit-complaint', data=data, content_type='multipart/form-data' if image else None, follow_redirects=True)

    # -------------------------------------------------------------
    # TEST 1: Register Citizen
    # -------------------------------------------------------------
    def test_01_register_citizen(self):
        response = self.register_user('Ravi Citizen', 'citizen@test.com', 'password123', 'Citizen')
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='citizen@test.com').first()
        self.assertIsNotNone(user, "User should be created in SQLite database.")
        self.assertEqual(user.name, 'Ravi Citizen')
        self.assertEqual(user.role, 'Citizen')
        self.assertTrue(user.check_password('password123'), "Password hash must match.")
        print("\n[PASS] TEST 1: Register Citizen")

    # -------------------------------------------------------------
    # TEST 2: Register Municipal Officer
    # -------------------------------------------------------------
    def test_02_register_municipal_officer(self):
        response = self.register_user('Officer Sharma', 'officer@test.com', 'password123', 'Municipal Officer')
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='officer@test.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Officer Sharma')
        self.assertEqual(user.role, 'Municipal Officer')
        print("[PASS] TEST 2: Register Municipal Officer")

    # -------------------------------------------------------------
    # TEST 3: Register Administrator
    # -------------------------------------------------------------
    def test_03_register_administrator(self):
        response = self.register_user('Admin Verma', 'admin@test.com', 'password123', 'Administrator')
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email='admin@test.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Admin Verma')
        self.assertEqual(user.role, 'Administrator')
        print("[PASS] TEST 3: Register Administrator")

    # -------------------------------------------------------------
    # TEST 4: Try duplicate email registration
    # -------------------------------------------------------------
    def test_04_duplicate_email_registration(self):
        self.register_user('First Citizen', 'duplicate@test.com', 'password123', 'Citizen')
        count_before = User.query.filter_by(email='duplicate@test.com').count()
        self.assertEqual(count_before, 1)

        response = self.client.post('/register', data={
            'name': 'Second Citizen',
            'email': 'duplicate@test.com',
            'password': 'different_password',
            'role': 'Citizen'
        }, follow_redirects=True)

        self.assertIn(b'already exists', response.data)
        count_after = User.query.filter_by(email='duplicate@test.com').count()
        self.assertEqual(count_after, 1, "Duplicate email registration must be rejected.")
        print("[PASS] TEST 4: Try duplicate email registration")

    # -------------------------------------------------------------
    # TEST 5: Login with valid Citizen credentials
    # -------------------------------------------------------------
    def test_05_login_valid_credentials(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        response = self.login_user('citizen@test.com', 'secretpass')
        # Redirection to citizen dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('/citizen/dashboard', response.headers.get('Location', ''))
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('user_role'), 'Citizen')
            self.assertIsNotNone(sess.get('user_id'))
        print("[PASS] TEST 5: Login with valid Citizen credentials")

    # -------------------------------------------------------------
    # TEST 6: Login with invalid credentials
    # -------------------------------------------------------------
    def test_06_login_invalid_credentials(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        response = self.client.post('/login', data={
            'email': 'citizen@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)
        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('user_id'))
        print("[PASS] TEST 6: Login with invalid credentials")

    # -------------------------------------------------------------
    # TEST 7: Citizen reaches Citizen Dashboard
    # -------------------------------------------------------------
    def test_07_citizen_reaches_dashboard(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        self.login_user('citizen@test.com', 'secretpass')
        response = self.client.get('/citizen/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Citizen Dashboard', response.data)
        self.assertIn(b'Ravi Citizen', response.data)
        self.assertIn(b'Submit Complaint', response.data)
        self.assertIn(b'Track Complaints', response.data)
        print("[PASS] TEST 7: Citizen reaches Citizen Dashboard")

    # -------------------------------------------------------------
    # TEST 8, 9, 10, 11: Citizen submits complaint & DB check
    # -------------------------------------------------------------
    def test_08_to_11_citizen_submits_complaint_and_properties(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        self.login_user('citizen@test.com', 'secretpass')

        # TEST 8: Citizen submits complaint with all required fields
        response = self.submit_test_complaint(
            title='Broken Streetlight on 5th Avenue',
            description='Streetlight pole #42 has been non-functional for 3 days causing safety issues.',
            location='5th Avenue near Pole 42',
            category='Electricity & Streetlights',
            priority='High'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Complaint successfully submitted', response.data)

        # TEST 9: Complaint appears in SQLite
        complaints = Complaint.query.all()
        self.assertEqual(len(complaints), 1)
        c = complaints[0]

        # TEST 10: Complaint ID is generated
        self.assertIsNotNone(c.id)
        self.assertIsInstance(c.id, int)
        self.assertGreater(c.id, 0)

        # TEST 11: Complaint state is Complaint Submitted
        self.assertEqual(c.status, 'Complaint Submitted')
        self.assertEqual(c.location, '5th Avenue near Pole 42')
        self.assertEqual(c.category, 'Electricity & Streetlights')
        self.assertEqual(c.priority, 'High')

        # Check initial StatusHistory entry created
        history_entries = StatusHistory.query.filter_by(complaint_id=c.id).all()
        self.assertEqual(len(history_entries), 1)
        self.assertEqual(history_entries[0].status, 'Complaint Submitted')

        print("[PASS] TEST 8: Citizen submits complaint")
        print("[PASS] TEST 9: Complaint appears in SQLite")
        print(f"[PASS] TEST 10: Complaint ID is generated (ID: #{c.id})")
        print("[PASS] TEST 11: Complaint state is 'Complaint Submitted'")

    # -------------------------------------------------------------
    # TEST 12: Citizen can see their own complaint
    # -------------------------------------------------------------
    def test_12_citizen_can_see_own_complaint(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        self.login_user('citizen@test.com', 'secretpass')

        self.submit_test_complaint(
            title='Pothole on Main Road',
            description='Deep pothole dangerous for motorcyclists.',
            location='Main Road near City Bank',
            category='Roads & Potholes'
        )

        response = self.client.get('/citizen/track-complaints')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Pothole on Main Road', response.data)
        self.assertIn(b'Complaint Submitted', response.data)
        self.assertIn(b'Main Road near City Bank', response.data)
        print("[PASS] TEST 12: Citizen can see their own complaint")

    # -------------------------------------------------------------
    # TEST 13: Citizen cannot see another Citizen's complaint
    # -------------------------------------------------------------
    def test_13_citizen_cannot_see_another_citizens_complaint(self):
        # Register and submit complaint as Citizen 1
        self.register_user('Citizen One', 'user1@test.com', 'pass1', 'Citizen')
        self.login_user('user1@test.com', 'pass1')
        self.submit_test_complaint(
            title='Citizen One Secret Complaint',
            description='Water pipe leak near house 101',
            location='House 101, Lane 4',
            category='Water Supply & Drainage'
        )
        c1 = Complaint.query.filter_by(title='Citizen One Secret Complaint').first()
        self.assertIsNotNone(c1)

        # Log out Citizen 1
        self.client.get('/logout')

        # Register and log in as Citizen 2
        self.register_user('Citizen Two', 'user2@test.com', 'pass2', 'Citizen')
        self.login_user('user2@test.com', 'pass2')

        # Verify Citizen 2's tracking list does NOT show Citizen 1's complaint
        response = self.client.get('/citizen/track-complaints')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Citizen One Secret Complaint', response.data)

        # Verify Citizen 2 cannot access Citizen 1's complaint URL directly
        detail_response = self.client.get(f'/citizen/complaint/{c1.id}')
        self.assertEqual(detail_response.status_code, 403, "Must return HTTP 403 Forbidden.")
        print("[PASS] TEST 13: Citizen cannot see another Citizen's complaint")

    # -------------------------------------------------------------
    # TEST 14: Citizen cannot access Officer dashboard
    # -------------------------------------------------------------
    def test_14_citizen_cannot_access_officer_dashboard(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        self.login_user('citizen@test.com', 'secretpass')

        response = self.client.get('/officer/dashboard')
        self.assertEqual(response.status_code, 403)
        print("[PASS] TEST 14: Citizen cannot access Officer dashboard")

    # -------------------------------------------------------------
    # TEST 15: Citizen cannot access Administrator dashboard
    # -------------------------------------------------------------
    def test_15_citizen_cannot_access_admin_dashboard(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'secretpass', 'Citizen')
        self.login_user('citizen@test.com', 'secretpass')

        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 403)
        print("[PASS] TEST 15: Citizen cannot access Administrator dashboard")

    # -------------------------------------------------------------
    # TEST 16: Officer can access Officer dashboard
    # -------------------------------------------------------------
    def test_16_officer_can_access_officer_dashboard(self):
        self.register_user('Officer Sharma', 'officer@test.com', 'pass123', 'Municipal Officer')
        self.login_user('officer@test.com', 'pass123')

        response = self.client.get('/officer/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Municipal Officer Dashboard', response.data)
        self.assertIn(b'Officer Sharma', response.data)
        print("[PASS] TEST 16: Officer can access Officer dashboard")

    # -------------------------------------------------------------
    # TEST 17: Officer cannot access Administrator dashboard
    # -------------------------------------------------------------
    def test_17_officer_cannot_access_admin_dashboard(self):
        self.register_user('Officer Sharma', 'officer@test.com', 'pass123', 'Municipal Officer')
        self.login_user('officer@test.com', 'pass123')

        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 403)
        print("[PASS] TEST 17: Officer cannot access Administrator dashboard")

    # -------------------------------------------------------------
    # TEST 18, 19, 20: Administrator dashboard, user count, complaint count
    # -------------------------------------------------------------
    def test_18_to_20_admin_dashboard_and_counts(self):
        # Create users
        self.register_user('Citizen A', 'ca@test.com', 'pass', 'Citizen')
        self.register_user('Officer B', 'ob@test.com', 'pass', 'Municipal Officer')
        self.register_user('Admin C', 'ac@test.com', 'pass', 'Administrator')

        # Create complaints
        self.login_user('ca@test.com', 'pass')
        self.submit_test_complaint(title='Test Issue 1', description='Details 1', location='Loc 1')
        self.submit_test_complaint(title='Test Issue 2', description='Details 2', location='Loc 2')
        self.client.get('/logout')

        # Admin login
        self.login_user('ac@test.com', 'pass')

        # TEST 18: Administrator can access Administrator dashboard
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrator Dashboard', response.data)

        # TEST 19: Administrator sees basic user count (3 users created)
        self.assertIn(b'3', response.data)

        # TEST 20: Administrator sees basic complaint count (2 complaints created)
        self.assertIn(b'2', response.data)

        print("[PASS] TEST 18: Administrator can access Administrator dashboard")
        print("[PASS] TEST 19: Administrator sees basic user count")
        print("[PASS] TEST 20: Administrator sees basic complaint count")

    # -------------------------------------------------------------
    # TEST 21: Logout works
    # -------------------------------------------------------------
    def test_21_logout_works(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'pass', 'Citizen')
        self.login_user('citizen@test.com', 'pass')

        # Verify user is logged in
        with self.client.session_transaction() as sess:
            self.assertIsNotNone(sess.get('user_id'))

        # Logout
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'logged out', response.data)

        with self.client.session_transaction() as sess:
            self.assertIsNone(sess.get('user_id'))
        print("[PASS] TEST 21: Logout works")

    # -------------------------------------------------------------
    # TEST 22: Protected pages cannot be accessed after logout
    # -------------------------------------------------------------
    def test_22_protected_pages_blocked_after_logout(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'pass', 'Citizen')
        self.login_user('citizen@test.com', 'pass')
        self.client.get('/logout')

        # Attempt to access citizen dashboard
        resp1 = self.client.get('/citizen/dashboard', follow_redirects=False)
        self.assertEqual(resp1.status_code, 302)
        self.assertIn('/login', resp1.headers.get('Location', ''))

        # Attempt to access officer dashboard
        resp2 = self.client.get('/officer/dashboard', follow_redirects=False)
        self.assertEqual(resp2.status_code, 302)
        self.assertIn('/login', resp2.headers.get('Location', ''))

        # Attempt to access admin dashboard
        resp3 = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(resp3.status_code, 302)
        self.assertIn('/login', resp3.headers.get('Location', ''))

        print("[PASS] TEST 22: Protected pages cannot be accessed after logout")

    # -------------------------------------------------------------
    # TEST 23: Invalid image upload is rejected
    # -------------------------------------------------------------
    def test_23_invalid_image_upload_rejected(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'pass', 'Citizen')
        self.login_user('citizen@test.com', 'pass')

        # Try submitting an executable or text file disguised as an image
        fake_executable = (io.BytesIO(b'MZ executable payload'), 'malicious_file.exe')
        response = self.client.post('/citizen/submit-complaint', data={
            'title': 'Malicious File Complaint',
            'description': 'Attempting to upload .exe file',
            'location': 'Near Main Gate',
            'category': 'Other',
            'priority': 'Medium',
            'image': fake_executable
        }, content_type='multipart/form-data', follow_redirects=True)

        self.assertIn(b'Invalid file format', response.data)
        complaint = Complaint.query.filter_by(title='Malicious File Complaint').first()
        self.assertIsNone(complaint, "Complaint with invalid file format must not be stored.")
        print("[PASS] TEST 23: Invalid image upload is rejected")

    # -------------------------------------------------------------
    # ADDITIONAL TESTS: Location Validation & Search by ID
    # -------------------------------------------------------------
    def test_24_location_validation(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'pass', 'Citizen')
        self.login_user('citizen@test.com', 'pass')

        # Too short location (< 3 chars)
        response = self.submit_test_complaint(location='ab')
        self.assertIn(b'Location must be between 3 and 200 characters', response.data)

        # Missing location
        response2 = self.client.post('/citizen/submit-complaint', data={
            'title': 'No Location Title',
            'description': 'No Location Description',
            'category': 'Other',
            'priority': 'Medium'
        }, follow_redirects=True)
        self.assertIn(b'All fields', response2.data)
        print("[PASS] TEST 24: Location validation enforced")

    def test_25_search_and_history(self):
        self.register_user('Ravi Citizen', 'citizen@test.com', 'pass', 'Citizen')
        self.login_user('citizen@test.com', 'pass')

        self.submit_test_complaint(title='Water Pipe Burst', description='Flooding road', location='Sector 9 Park', category='Water Supply & Drainage')
        c = Complaint.query.filter_by(title='Water Pipe Burst').first()
        self.assertIsNotNone(c)

        # Search by Complaint ID
        resp = self.client.get(f'/citizen/track-complaints?q={c.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Water Pipe Burst', resp.data)

        # Detail page contains status history timeline
        resp_detail = self.client.get(f'/citizen/complaint/{c.id}')
        self.assertEqual(resp_detail.status_code, 200)
        self.assertIn(b'Status History & Audit Trail', resp_detail.data)
        self.assertIn(b'Complaint registered with supporting details', resp_detail.data)
        print("[PASS] TEST 25: Complaint ID search and status history timeline verified")

if __name__ == '__main__':
    unittest.main(verbosity=2)
