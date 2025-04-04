from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.units import inch
import tempfile
import os
from typing import Dict, Optional

class PDFGenerator:
    """Service for generating PDF documents from text content"""

    @staticmethod
    def generate_pdf(content: str, metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Generate a PDF file from the given content and metadata.

        Args:
            content: The main text content for the PDF.
            metadata: Optional dictionary containing metadata like title, author, date.

        Returns:
            The file path to the generated PDF.
        """
        # Create a temporary file to store the PDF
        temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = temp_pdf.name
        temp_pdf.close() # Close the file handle, SimpleDocTemplate will open it

        doc = SimpleDocTemplate(pdf_path)
        styles = getSampleStyleSheet()
        story = []

        # Add metadata if provided
        if metadata:
            title = metadata.get("title", "Document")
            author = metadata.get("author", "OpenCoder User")
            date = metadata.get("date", "")
            course = metadata.get("course", "")

            # Title Style
            title_style = styles['h1']
            title_style.alignment = TA_CENTER
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 0.2*inch))

            # Metadata Style
            meta_style = styles['Normal']
            meta_style.alignment = TA_LEFT
            if author:
                story.append(Paragraph(f"Author: {author}", meta_style))
            if course:
                story.append(Paragraph(f"Course: {course}", meta_style))
            if date:
                story.append(Paragraph(f"Date: {date}", meta_style))
            story.append(Spacer(1, 0.3*inch))

        # Add main content
        # Split content into paragraphs based on double newlines
        body_style = styles['BodyText']
        paragraphs = content.split('\n\n')
        for para_text in paragraphs:
            if para_text.strip(): # Avoid adding empty paragraphs
                # Handle simple markdown-like headers (#, ##)
                if para_text.startswith('# '):
                    p = Paragraph(para_text[2:], styles['h1'])
                elif para_text.startswith('## '):
                    p = Paragraph(para_text[3:], styles['h2'])
                elif para_text.startswith('### '):
                    p = Paragraph(para_text[4:], styles['h3'])
                else:
                    p = Paragraph(para_text.replace('\n', '<br/>'), body_style)
                story.append(p)
                story.append(Spacer(1, 0.1*inch))

        # Build the PDF
        try:
            doc.build(story)
        except Exception as e:
            print(f"Error building PDF: {e}")
            # Clean up the temporary file if PDF generation fails
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            raise

        return pdf_path