import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_success(self, client, reset_activities):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data

    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        for name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball Team" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup actually adds the participant"""
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Basketball Team"]["participants"])
        
        # Sign up a new participant
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Check participant count increased
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Basketball Team"]["participants"])
        
        assert updated_count == initial_count + 1
        assert "newstudent@mergington.edu" in updated_response.json()["Basketball Team"]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        # Get an existing participant
        initial_response = client.get("/activities")
        existing_student = initial_response.json()["Basketball Team"]["participants"][0]
        
        # Try to sign up again
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": existing_student}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        student_email = "multiplesports@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": student_email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Tennis Club/signup",
            params={"email": student_email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities = client.get("/activities").json()
        assert student_email in activities["Basketball Team"]["participants"]
        assert student_email in activities["Tennis Club"]["participants"]


class TestUnregister:
    """Tests for the POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        # Get an existing participant
        initial_response = client.get("/activities")
        student = initial_response.json()["Basketball Team"]["participants"][0]
        
        # Unregister
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": student}
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes the participant"""
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Basketball Team"]["participants"])
        student = initial_response.json()["Basketball Team"]["participants"][0]
        
        # Unregister
        client.post(
            "/activities/Basketball Team/unregister",
            params={"email": student}
        )
        
        # Check participant count decreased
        updated_response = client.get("/activities")
        updated_count = len(updated_response.json()["Basketball Team"]["participants"])
        
        assert updated_count == initial_count - 1
        assert student not in updated_response.json()["Basketball Team"]["participants"]

    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/NonExistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_signed_up(self, client, reset_activities):
        """Test unregister for student who is not signed up"""
        response = client.post(
            "/activities/Basketball Team/unregister",
            params={"email": "notsignedup@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that a student can sign up again after unregistering"""
        student_email = "changingmind@mergington.edu"
        activity = "Tennis Club"
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": student_email}
        )
        
        # Unregister
        client.post(
            f"/activities/{activity}/unregister",
            params={"email": student_email}
        )
        
        # Sign up again
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student_email}
        )
        assert response.status_code == 200
        
        # Verify signed up
        activities = client.get("/activities").json()
        assert student_email in activities[activity]["participants"]


class TestRootEndpoint:
    """Tests for the GET / endpoint"""

    def test_root_redirect(self, client, reset_activities):
        """Test that root endpoint redirects to static HTML"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
