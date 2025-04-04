from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app.core.database import get_db
from app.models.schemas import Course, CourseCreate, Assignment, AssignmentCreate, Material, MaterialCreate
from app.models.models import User as UserModel, Course as CourseModel, Assignment as AssignmentModel, Material as MaterialModel
from app.services.google_classroom import GoogleClassroomService
from app.services.google_drive import GoogleDriveService
from app.routes.auth import get_current_user
from datetime import datetime


router = APIRouter(tags=["classroom"])


@router.get("/courses", response_model=List[Course])
async def get_courses(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all courses for the current user
    """
    # Ensure user has Google access token
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google authentication required"
        )
    
    # Initialize Google Classroom service
    classroom_service = GoogleClassroomService(
        access_token=current_user.google_access_token,
        refresh_token=current_user.google_refresh_token,
        expiry=current_user.token_expiry
    )
    
    # Fetch courses from Google Classroom API
    google_courses = classroom_service.get_courses()
    
    # Process and save courses to database
    db_courses = []
    for google_course in google_courses:
        # Check if course already exists in DB
        db_course = db.query(CourseModel).filter(
            CourseModel.google_course_id == google_course["id"],
            CourseModel.user_id == current_user.id
        ).first()
        
        if not db_course:
            # Create new course
            db_course = CourseModel(
                google_course_id=google_course["id"],
                name=google_course.get("name", "Unnamed Course"),
                section=google_course.get("section"),
                description=google_course.get("description"),
                room=google_course.get("room"),
                user_id=current_user.id
            )
            db.add(db_course)
            db.commit()
            db.refresh(db_course)
        else:
            # Update existing course
            db_course.name = google_course.get("name", db_course.name)
            db_course.section = google_course.get("section", db_course.section)
            db_course.description = google_course.get("description", db_course.description)
            db_course.room = google_course.get("room", db_course.room)
            db.commit()
            db.refresh(db_course)
        
        db_courses.append(db_course)
    
    return db_courses


@router.get("/courses/{course_id}", response_model=Course)
async def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get specific course details
    """
    # Fetch course from database
    db_course = db.query(CourseModel).filter(
        CourseModel.id == course_id,
        CourseModel.user_id == current_user.id
    ).first()
    
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return db_course


@router.get("/courses/{course_id}/assignments", response_model=List[Assignment])
async def get_assignments(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all assignments for a specific course
    """
    # Ensure user has Google access token
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google authentication required"
        )
    
    # Check if course exists in DB
    db_course = db.query(CourseModel).filter(
        CourseModel.id == course_id,
        CourseModel.user_id == current_user.id
    ).first()
    
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Initialize Google Classroom service
    classroom_service = GoogleClassroomService(
        access_token=current_user.google_access_token,
        refresh_token=current_user.google_refresh_token,
        expiry=current_user.token_expiry
    )
    
    # Initialize Google Drive service
    drive_service = GoogleDriveService(
        access_token=current_user.google_access_token,
        refresh_token=current_user.google_refresh_token,
        expiry=current_user.token_expiry
    )
    
    # Fetch assignments from Google Classroom API
    google_assignments = classroom_service.get_assignments(db_course.google_course_id)
    
    # Process and save assignments to database
    db_assignments = []
    for google_assignment in google_assignments:
        # Check if assignment already exists
        db_assignment = db.query(AssignmentModel).filter(
            AssignmentModel.google_assignment_id == google_assignment["id"],
            AssignmentModel.course_id == db_course.id
        ).first()
        
        # Parse due date if present
        due_date = None
        if "dueDate" in google_assignment and "dueTime" in google_assignment:
            due_info = google_assignment["dueDate"]
            time_info = google_assignment["dueTime"]
            try:
                due_date = datetime(
                    year=due_info.get("year", 1970),
                    month=due_info.get("month", 1),
                    day=due_info.get("day", 1),
                    hour=time_info.get("hours", 0),
                    minute=time_info.get("minutes", 0)
                )
            except ValueError:
                due_date = None
        
        if not db_assignment:
            # Create new assignment
            db_assignment = AssignmentModel(
                google_assignment_id=google_assignment["id"],
                title=google_assignment.get("title", "Untitled Assignment"),
                description=google_assignment.get("description", ""),
                due_date=due_date,
                course_id=db_course.id,
                user_id=current_user.id
            )
            db.add(db_assignment)
            db.commit()
            db.refresh(db_assignment)
        else:
            # Update existing assignment
            db_assignment.title = google_assignment.get("title", db_assignment.title)
            db_assignment.description = google_assignment.get("description", db_assignment.description)
            if due_date:
                db_assignment.due_date = due_date
            db.commit()
            db.refresh(db_assignment)
        
        # Process materials if present
        if "materials" in google_assignment:
            process_materials(
                db=db, 
                google_materials=google_assignment["materials"],
                assignment_id=db_assignment.id,
                classroom_service=classroom_service,
                drive_service=drive_service,
                course_id=db_course.google_course_id
            )
        
        db_assignments.append(db_assignment)
    
    return db_assignments


@router.get("/assignments/{assignment_id}", response_model=Assignment)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get specific assignment details
    """
    # Fetch assignment from database
    db_assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == assignment_id,
        AssignmentModel.user_id == current_user.id
    ).first()
    
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    return db_assignment


@router.get("/assignments/{assignment_id}/materials", response_model=List[Material])
async def get_materials(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get materials for a specific assignment
    """
    # Fetch assignment from database
    db_assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == assignment_id,
        AssignmentModel.user_id == current_user.id
    ).first()
    
    if not db_assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Fetch materials from database
    db_materials = db.query(MaterialModel).filter(
        MaterialModel.assignment_id == db_assignment.id
    ).all()
    
    return db_materials


# Helper function to process materials
def process_materials(
    db: Session, 
    google_materials: List[Dict], 
    assignment_id: int,
    classroom_service: GoogleClassroomService,
    drive_service: GoogleDriveService,
    course_id: str
):
    """Process and save materials from Google Classroom, downloading content from Drive"""
    for material in google_materials:
        # Determine material type and extract relevant data
        material_type = "unknown"
        url = None
        content = None
        title = "Untitled Material"
        google_material_id = None
        
        if "driveFile" in material:
            material_type = "drive_file"
            drive_file = material["driveFile"].get("driveFile", {})
            title = drive_file.get("title", "Drive File")
            url = drive_file.get("alternateLink")
            google_material_id = drive_file.get("id")
            
            # Attempt to download content from Google Drive
            if google_material_id:
                print(f"Attempting to download content for Drive file: {title} ({google_material_id})")
                downloaded_content_stream = drive_service.download_file(google_material_id)
                if downloaded_content_stream:
                    try:
                        # Assuming text content for now, adjust based on actual MIME types if needed
                        content = downloaded_content_stream.read().decode('utf-8')
                        print(f"Successfully downloaded content for: {title}")
                    except Exception as e:
                        print(f"Error decoding content for {title}: {e}")
                        content = "[Error decoding content]"
                    finally:
                        downloaded_content_stream.close()
                else:
                    print(f"Failed to download content for: {title}")
                    content = "[Content download failed]"
        
        elif "youtubeVideo" in material:
            material_type = "youtube"
            video = material["youtubeVideo"]
            title = video.get("title", "YouTube Video")
            url = video.get("alternateLink")
            google_material_id = video.get("id")
        
        elif "link" in material:
            material_type = "link"
            link = material["link"]
            title = link.get("title", "Link")
            url = link.get("url")
        
        elif "form" in material:
            material_type = "form"
            form = material["form"]
            title = form.get("title", "Form")
            url = form.get("formUrl")
            google_material_id = form.get("id")
        
        # Check if material already exists
        db_material = db.query(MaterialModel).filter(
            MaterialModel.google_material_id == google_material_id if google_material_id else None,
            MaterialModel.assignment_id == assignment_id,
            MaterialModel.url == url if url else None
        ).first()
        
        if not db_material:
            # Create new material
            db_material = MaterialModel(
                google_material_id=google_material_id,
                title=title,
                type=material_type,
                url=url,
                content=content,
                assignment_id=assignment_id
            )
            db.add(db_material)
            db.commit()
            db.refresh(db_material)
        else:
            # Update existing material
            db_material.title = title
            db_material.url = url
            db_material.type = material_type
            if content:
                db_material.content = content
            db.commit()
            db.refresh(db_material)