from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import os
import tempfile
from datetime import datetime

from app.core.database import get_db
from app.models.schemas import Draft, DraftCreate, DraftUpdate, GenerationRequest, GenerationResponse, Assignment
from app.models.models import User as UserModel, Assignment as AssignmentModel, Draft as DraftModel, Material as MaterialModel
from app.services.ai_generator import AIGenerationService
from app.services.nlp_processor import NLPProcessor
from app.services.pdf_generator import PDFGenerator
from app.services.google_classroom import GoogleClassroomService
from app.services.google_drive import GoogleDriveService
from app.routes.auth import get_current_user


router = APIRouter(tags=["assignments"])


@router.post("/drafts", response_model=Draft)
async def create_draft(
    *,
    db: Session = Depends(get_db),
    draft_in: DraftCreate,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Manually create a draft for an assignment
    """
    # Check if assignment exists and belongs to the user
    assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == draft_in.assignment_id,
        AssignmentModel.user_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Create new draft
    db_draft = DraftModel(
        content=draft_in.content,
        status=draft_in.status,
        feedback=draft_in.feedback,
        user_id=current_user.id,
        assignment_id=draft_in.assignment_id
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    
    return db_draft


@router.get("/assignments/{assignment_id}/drafts", response_model=List[Draft])
async def get_drafts(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get all drafts for a specific assignment
    """
    # Check if assignment exists and belongs to the user
    assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == assignment_id,
        AssignmentModel.user_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Get all drafts for the assignment
    drafts = db.query(DraftModel).filter(
        DraftModel.assignment_id == assignment_id,
        DraftModel.user_id == current_user.id
    ).all()
    
    return drafts


@router.get("/drafts/{draft_id}", response_model=Draft)
async def get_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get specific draft details
    """
    # Fetch draft from database
    draft = db.query(DraftModel).filter(
        DraftModel.id == draft_id,
        DraftModel.user_id == current_user.id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    return draft


@router.put("/drafts/{draft_id}", response_model=Draft)
async def update_draft(
    draft_id: int,
    draft_in: DraftUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Update a draft
    """
    # Fetch draft from database
    draft = db.query(DraftModel).filter(
        DraftModel.id == draft_id,
        DraftModel.user_id == current_user.id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Update draft
    draft.content = draft_in.content
    draft.status = draft_in.status
    draft.feedback = draft_in.feedback
    if draft_in.submission_date:
        draft.submission_date = draft_in.submission_date
    
    db.commit()
    db.refresh(draft)
    
    return draft


@router.post("/assignments/{assignment_id}/generate", response_model=Draft)
async def generate_assignment_draft(
    assignment_id: int,
    generation_request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Generate a draft for an assignment using AI
    """
    # Check if assignment exists and belongs to the user
    assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == assignment_id,
        AssignmentModel.user_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Get materials for the assignment
    materials = db.query(MaterialModel).filter(
        MaterialModel.assignment_id == assignment_id
    ).all()
    
    # Process assignment description and materials with NLP
    materials_text = [m.content for m in materials if m.content]
    assignment_context = {
        "title": assignment.title,
        "description": assignment.description,
        "materials": [{"summary": m.processed_content or m.content or f"Material: {m.title}"} for m in materials],
    }
    
    # Add processed context if available
    if assignment.description:
        processed_context = NLPProcessor.process_assignment_content(
            assignment_text=assignment.description,
            materials_text=materials_text
        )
        assignment_context["requirements"] = processed_context.get("requirements", {})
    
    # Generate content with AI (this happens in background)
    # Create a placeholder draft
    db_draft = DraftModel(
        content="Generating content...",
        status="generating",
        user_id=current_user.id,
        assignment_id=assignment_id
    )
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    
    # Schedule the generation task in the background
    background_tasks.add_task(
        generate_draft_content,
        db=db,
        draft_id=db_draft.id,
        assignment_context=assignment_context,
        parameters=generation_request.parameters
    )
    
    return db_draft


@router.post("/drafts/{draft_id}/export-pdf")
async def export_draft_to_pdf(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Export a draft to PDF
    """
    # Fetch draft from database
    draft = db.query(DraftModel).filter(
        DraftModel.id == draft_id,
        DraftModel.user_id == current_user.id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Get assignment details
    assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == draft.assignment_id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Generate PDF
    pdf_metadata = {
        "title": assignment.title,
        "author": current_user.full_name,
        "date": datetime.now().strftime("%B %d, %Y")
    }
    
    # Generate PDF file
    pdf_path = PDFGenerator.generate_pdf(
        content=draft.content,
        metadata=pdf_metadata
    )
    
    # Return the PDF file
    return FileResponse(
        path=pdf_path,
        filename=f"{assignment.title.replace(' ', '_')}.pdf",
        media_type="application/pdf"
    )


@router.post("/drafts/{draft_id}/submit")
async def submit_draft_to_classroom(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Submit a draft to Google Classroom by uploading PDF to Drive first.
    """
    # Fetch draft from database
    draft = db.query(DraftModel).filter(
        DraftModel.id == draft_id,
        DraftModel.user_id == current_user.id
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    if draft.status == 'submitted':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Draft already submitted"
        )

    # Get assignment and course details
    assignment = db.query(AssignmentModel).filter(
        AssignmentModel.id == draft.assignment_id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Associated assignment not found")
    course = assignment.course
    if not course:
         raise HTTPException(status_code=404, detail="Associated course not found")
    
    # Ensure user has Google access token
    if not current_user.google_access_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Google authentication required for submission"
        )
    
    pdf_path = None
    try:
        # 1. Generate PDF file
        pdf_metadata = {
            "title": assignment.title,
            "author": current_user.full_name,
            "course": course.name,
            "date": datetime.now().strftime("%B %d, %Y")
        }
        pdf_path = PDFGenerator.generate_pdf(
            content=draft.content,
            metadata=pdf_metadata
        )
        pdf_filename = f"{assignment.title.replace(' ', '_')}_submission.pdf"

        # 2. Initialize Google Drive Service
        drive_service = GoogleDriveService(
            access_token=current_user.google_access_token,
            refresh_token=current_user.google_refresh_token,
            expiry=current_user.token_expiry
        )

        # 3. (Optional) Find or create a submission folder in Drive
        submission_folder_name = "OpenCoder Submissions"
        folder_id = drive_service.find_or_create_folder(submission_folder_name)
        if not folder_id:
            print("Warning: Could not find or create Drive folder. Uploading to root.")

        # 4. Upload PDF to Google Drive
        print(f"Uploading PDF '{pdf_filename}' to Google Drive...")
        uploaded_file = drive_service.upload_file(
            file_path=pdf_path,
            file_name=pdf_filename,
            mime_type='application/pdf',
            folder_id=folder_id
        )
        
        if not uploaded_file or 'id' not in uploaded_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload PDF to Google Drive"
            )
        
        drive_file_id = uploaded_file['id']
        print(f"PDF uploaded successfully to Drive. File ID: {drive_file_id}")

        # 5. Initialize Google Classroom Service
        classroom_service = GoogleClassroomService(
            access_token=current_user.google_access_token,
            refresh_token=current_user.google_refresh_token,
            expiry=current_user.token_expiry
        )

        # 6. Prepare attachment data for Classroom submission
        attachment_data = {
            'driveFile': {
                'id': drive_file_id
            }
        }

        # 7. Submit to Google Classroom
        print(f"Submitting assignment {assignment.google_assignment_id} to course {course.google_course_id}...")
        submission_result = classroom_service.create_submission(
            course_id=course.google_course_id,
            coursework_id=assignment.google_assignment_id,
            file_data=attachment_data
        )

        if not submission_result or 'id' not in submission_result:
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit assignment to Google Classroom"
            )

        print(f"Submission successful. Classroom Submission ID: {submission_result['id']}")

        # 8. Update draft status in DB
        draft.status = "submitted"
        draft.submission_date = datetime.utcnow()
        db.commit()
        db.refresh(draft)
        
        # Return success response
        return {
            "status": "success",
            "message": "Draft submitted successfully to Google Classroom",
            "submission_date": draft.submission_date,
            "classroom_submission_id": submission_result['id'],
            "drive_file_id": drive_file_id
        }

    except Exception as e:
        # Log the error for debugging
        print(f"Error during submission process for draft {draft_id}: {e}")
        # Re-raise as HTTPException for FastAPI to handle
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during submission: {str(e)}"
        )
    finally:
        # 9. Clean up the temporary PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Cleaned up temporary PDF file: {pdf_path}")
            except OSError as e:
                print(f"Error removing temporary PDF file {pdf_path}: {e}")


# Background task to generate draft content
async def generate_draft_content(
    db: Session,
    draft_id: int,
    assignment_context: Dict[str, Any],
    parameters: Optional[Dict[str, Any]] = None
):
    """Background task to generate draft content"""
    try:
        # Generate content with AI
        generation_result = await AIGenerationService.generate_assignment_solution(
            assignment_context=assignment_context,
            parameters=parameters
        )
        
        # Update the draft with the generated content
        draft = db.query(DraftModel).filter(DraftModel.id == draft_id).first()
        if draft:
            draft.content = generation_result["content"]
            draft.status = "draft"  # Change from "generating" to "draft"
            db.commit()
    
    except Exception as e:
        # Update the draft with error message
        draft = db.query(DraftModel).filter(DraftModel.id == draft_id).first()
        if draft:
            draft.content = f"Error generating content: {str(e)}"
            draft.status = "error"
            db.commit()