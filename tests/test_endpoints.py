import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from app import activities


class TestRootEndpoint:
    """Tests for GET /"""
    
    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Test Activity" in data
    
    def test_get_activities_includes_correct_fields(self, client):
        """Test that each activity has all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_includes_participants(self, client):
        """Test that participants are included in activity data"""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        
        # Test Activity should have 0 participants
        assert len(data["Test Activity"]["participants"]) == 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup"""
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup adds a student to an activity"""
        response = client.post(
            "/activities/Test%20Activity/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Test Activity"]["participants"]
    
    def test_signup_to_existing_activity(self, client):
        """Test signup to an activity with existing participants"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newplayer@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newplayer@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert len(activities_data["Chess Club"]["participants"]) == 3
    
    def test_signup_returns_success_message(self, client):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Programming Class" in data["message"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister"""
    
    def test_unregister_removes_participant_from_activity(self, client):
        """Test that unregister removes a student from an activity"""
        # First, verify the participant is there
        activities_before = client.get("/activities").json()
        assert "michael@mergington.edu" in activities_before["Chess Club"]["participants"]
        
        # Unregister the participant
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify the participant was removed
        activities_after = client.get("/activities").json()
        assert "michael@mergington.edu" not in activities_after["Chess Club"]["participants"]
        assert len(activities_after["Chess Club"]["participants"]) == 1
    
    def test_unregister_returns_success_message(self, client):
        """Test that unregister returns a success message"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=daniel@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "daniel@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_unregister_from_activity_with_multiple_participants(self, client):
        """Test unregistering from an activity with multiple participants"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Other participant should still be registered
        activities_data = client.get("/activities").json()
        assert "daniel@mergington.edu" in activities_data["Chess Club"]["participants"]
        assert len(activities_data["Chess Club"]["participants"]) == 1
