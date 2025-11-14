"""
Test suite for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original activities
    original_activities = {
        key: {
            "description": val["description"],
            "schedule": val["schedule"],
            "max_participants": val["max_participants"],
            "participants": val["participants"].copy()
        }
        for key, val in activities.items()
    }
    
    yield
    
    # Restore activities after test
    for key, val in activities.items():
        val["participants"] = original_activities[key]["participants"].copy()


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns status 200"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_json(self):
        """Test that GET /activities returns valid JSON"""
        response = client.get("/activities")
        assert response.headers["content-type"] == "application/json"

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activity data"""
        response = client.get("/activities")
        activities_data = response.json()
        
        # Should have all activities
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data
        assert "Gym Class" in activities_data
        assert "Basketball Team" in activities_data
        assert "Tennis Club" in activities_data
        assert "Art Studio" in activities_data
        assert "Drama Club" in activities_data
        assert "Debate Team" in activities_data
        assert "Science Club" in activities_data

    def test_get_activities_has_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities_data = response.json()
        
        for activity_name, activity_details in activities_data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_student(self, reset_activities):
        """Test signing up a valid student"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, reset_activities):
        """Test that signup actually adds the participant"""
        initial_count = len(activities["Chess Club"]["participants"])
        
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        new_count = len(activities["Chess Club"]["participants"])
        assert new_count == initial_count + 1
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_student(self, reset_activities):
        """Test that a student can't sign up twice for the same activity"""
        # First signup
        client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        
        # Try to signup again
        response = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_to_full_activity(self, reset_activities):
        """Test signing up to an activity that's at max capacity"""
        # Fill up an activity with fewer spots
        activity = activities["Tennis Club"]  # max 10 participants
        initial_spots = activity["max_participants"] - len(activity["participants"])
        
        # Fill remaining spots
        for i in range(initial_spots):
            response = client.post(
                f"/activities/Tennis%20Club/signup?email=student{i}@mergington.edu"
            )
            assert response.status_code == 200
        
        # Try to sign up when full - should still succeed (no capacity check in current implementation)
        response = client.post(
            "/activities/Tennis%20Club/signup?email=overfull@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, reset_activities):
        """Test unregistering a participant from an activity"""
        # First add a participant
        client.post(
            "/activities/Chess%20Club/signup?email=toremove@mergington.edu"
        )
        
        # Then remove them
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=toremove@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "toremove@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, reset_activities):
        """Test that unregister actually removes the participant"""
        # Add participant
        client.post(
            "/activities/Chess%20Club/signup?email=removetest@mergington.edu"
        )
        
        initial_count = len(activities["Chess Club"]["participants"])
        
        # Remove participant
        client.delete(
            "/activities/Chess%20Club/unregister?email=removetest@mergington.edu"
        )
        
        new_count = len(activities["Chess Club"]["participants"])
        assert new_count == initial_count - 1
        assert "removetest@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from an activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_not_registered_student(self, reset_activities):
        """Test unregistering a student who isn't registered"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]

    def test_unregister_original_participant(self, reset_activities):
        """Test unregistering one of the original participants"""
        # Get an original participant
        original_participant = activities["Chess Club"]["participants"][0]
        initial_count = len(activities["Chess Club"]["participants"])
        
        # Unregister them
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={original_participant}"
        )
        
        assert response.status_code == 200
        new_count = len(activities["Chess Club"]["participants"])
        assert new_count == initial_count - 1
        assert original_participant not in activities["Chess Club"]["participants"]


class TestRoot:
    """Tests for GET / endpoint"""

    def test_root_redirect(self):
        """Test that root path redirects to static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_and_unregister_flow(self, reset_activities):
        """Test complete signup and unregister flow"""
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        assert email in activities[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        assert email not in activities[activity]["participants"]

    def test_multiple_signups_and_unregisters(self, reset_activities):
        """Test multiple users signing up and unregistering"""
        activity = "Art Studio"
        emails = [
            "user1@mergington.edu",
            "user2@mergington.edu",
            "user3@mergington.edu"
        ]
        
        # Sign up multiple users
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        assert len(activities[activity]["participants"]) >= len(emails)
        
        # Unregister some users
        for email in emails[:2]:
            response = client.delete(
                f"/activities/{activity}/unregister?email={email}"
            )
            assert response.status_code == 200
            assert email not in activities[activity]["participants"]
        
        # Verify third user is still registered
        assert emails[2] in activities[activity]["participants"]
