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
        # Arrange
        # No setup needed for this simple test
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for GET /activities"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        # Arrange
        # Test data is provided by the reset_activities fixture
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Test Activity" in data
    
    def test_get_activities_includes_correct_fields(self, client):
        """Test that each activity has all required fields"""
        # Arrange
        # Test data is provided by the reset_activities fixture
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
    
    def test_get_activities_includes_participants(self, client):
        """Test that participants are included in activity data"""
        # Arrange
        # Test data is provided by the reset_activities fixture
        # Chess Club has 2 participants, Test Activity has 0
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert len(data["Test Activity"]["participants"]) == 0


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup"""
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup adds a student to an activity"""
        # Arrange
        student_email = "newstudent@mergington.edu"
        activity_name = "Test Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={student_email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in data["message"]
        
        # Verify the student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert student_email in activities_data[activity_name]["participants"]
    
    def test_signup_to_existing_activity(self, client):
        """Test signup to an activity with existing participants"""
        # Arrange
        student_email = "newplayer@mergington.edu"
        activity_name = "Chess Club"
        initial_participant_count = 2
        
        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={student_email}"
        )
        
        # Assert
        assert response.status_code == 200
        
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert student_email in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == initial_participant_count + 1
    
    def test_signup_returns_success_message(self, client):
        """Test that signup returns a success message"""
        # Arrange
        student_email = "test@mergington.edu"
        activity_name = "Programming Class"
        
        # Act
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={student_email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert student_email in data["message"]
        assert activity_name in data["message"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister"""
    
    def test_unregister_removes_participant_from_activity(self, client):
        """Test that unregister removes a student from an activity"""
        # Arrange
        student_email = "michael@mergington.edu"
        activity_name = "Chess Club"
        activities_before = client.get("/activities").json()
        initial_participant_count = len(activities_before[activity_name]["participants"])
        assert student_email in activities_before[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/unregister?email={student_email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in data["message"]
        
        activities_after = client.get("/activities").json()
        assert student_email not in activities_after[activity_name]["participants"]
        assert len(activities_after[activity_name]["participants"]) == initial_participant_count - 1
    
    def test_unregister_returns_success_message(self, client):
        """Test that unregister returns a success message"""
        # Arrange
        student_email = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/unregister?email={student_email}"
        )
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert "message" in data
        assert student_email in data["message"]
        assert activity_name in data["message"]
    
    def test_unregister_from_activity_with_multiple_participants(self, client):
        """Test unregistering from an activity with multiple participants"""
        # Arrange
        student_to_remove = "michael@mergington.edu"
        other_student = "daniel@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name.replace(' ', '%20')}/unregister?email={student_to_remove}"
        )
        activities_data = client.get("/activities").json()
        
        # Assert
        assert response.status_code == 200
        assert other_student in activities_data[activity_name]["participants"]
        assert student_to_remove not in activities_data[activity_name]["participants"]
        assert len(activities_data[activity_name]["participants"]) == 1
