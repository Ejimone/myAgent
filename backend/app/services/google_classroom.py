from typing import Dict, List, Any, Optional
from datetime import datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.google_auth import GoogleAuthService


class GoogleClassroomService:
    """Service for interacting with Google Classroom API"""

    @staticmethod
    def create_classroom_service(access_token: str, refresh_token: Optional[str] = None, expiry: Optional[datetime] = None):
        """Create Google Classroom API service"""
        credentials = GoogleAuthService.create_credentials(
            access_token=access_token,
            refresh_token=refresh_token,
            expiry=expiry
        )
        
        return build('classroom', 'v1', credentials=credentials)

    def __init__(self, access_token: str, refresh_token: Optional[str] = None, expiry: Optional[datetime] = None):
        """Initialize the Google Classroom service"""
        self.service = self.create_classroom_service(access_token, refresh_token, expiry)
    
    def get_courses(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get all courses for the authenticated user"""
        try:
            # Call the Classroom API
            results = self.service.courses().list(pageSize=page_size).execute()
            courses = results.get('courses', [])
            
            return courses
        except HttpError as error:
            print(f"An error occurred fetching courses: {error}")
            return []
    
    def get_course(self, course_id: str) -> Dict[str, Any]:
        """Get specific course details"""
        try:
            course = self.service.courses().get(id=course_id).execute()
            return course
        except HttpError as error:
            print(f"An error occurred fetching course {course_id}: {error}")
            return {}
    
    def get_assignments(self, course_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get assignments for a specific course"""
        try:
            # Call the Classroom API for course work
            results = self.service.courses().courseWork().list(
                courseId=course_id,
                pageSize=page_size
            ).execute()
            
            assignments = results.get('courseWork', [])
            return assignments
        except HttpError as error:
            print(f"An error occurred fetching assignments for course {course_id}: {error}")
            return []
    
    def get_assignment(self, course_id: str, assignment_id: str) -> Dict[str, Any]:
        """Get specific assignment details"""
        try:
            assignment = self.service.courses().courseWork().get(
                courseId=course_id,
                id=assignment_id
            ).execute()
            
            return assignment
        except HttpError as error:
            print(f"An error occurred fetching assignment {assignment_id} from course {course_id}: {error}")
            return {}

    def get_materials(self, course_id: str, assignment_id: str) -> List[Dict[str, Any]]:
        """Get materials attached to a specific assignment"""
        try:
            # Get the assignment details which includes materials
            assignment = self.get_assignment(course_id, assignment_id)
            
            # Extract materials if they exist
            materials = assignment.get('materials', [])
            
            return materials
        except Exception as error:
            print(f"An error occurred fetching materials: {error}")
            return []

    def get_announcements(self, course_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get announcements for a specific course"""
        try:
            results = self.service.courses().announcements().list(
                courseId=course_id,
                pageSize=page_size
            ).execute()
            
            announcements = results.get('announcements', [])
            return announcements
        except HttpError as error:
            print(f"An error occurred fetching announcements for course {course_id}: {error}")
            return []

    def create_submission(self, course_id: str, coursework_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an assignment to Google Classroom"""
        try:
            # First, we need to create a "draft" submission
            student_submission = self.service.courses().courseWork().studentSubmissions().create(
                courseId=course_id,
                courseWorkId=coursework_id,
                body={}
            ).execute()
            
            submission_id = student_submission.get('id')
            
            # Attach file to submission
            attachment = {
                'addAttachments': [file_data]
            }
            
            # Update the submission with the attachment
            updated_submission = self.service.courses().courseWork().studentSubmissions().modifyAttachments(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=submission_id,
                body=attachment
            ).execute()
            
            # Turn in the submission
            final_submission = self.service.courses().courseWork().studentSubmissions().turnIn(
                courseId=course_id,
                courseWorkId=coursework_id,
                id=submission_id,
                body={}
            ).execute()
            
            return final_submission
        except HttpError as error:
            print(f"An error occurred creating submission: {error}")
            return {}