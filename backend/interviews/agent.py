import google.generativeai as genai
from django.conf import settings
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from django.core.files.base import ContentFile
from io import BytesIO
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

# Configure Gemini API key with fallback system
try:
    # Try settings first, then fallback to universal paid key
    api_key = (
        getattr(settings, 'GEMINI_API_KEY', None) 
        or getattr(settings, 'GOOGLE_API_KEY', None)
        or 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'  # Universal paid key fallback
    )
    if api_key:
        genai.configure(api_key=api_key)
    else:
        logger.warning("GEMINI_API_KEY not found, using fallback")
        genai.configure(api_key='AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g')
except Exception as e:
    logger.error(f"Failed to configure Gemini API: {e}")
    # Final fallback
    try:
        genai.configure(api_key='AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g')
    except:
        pass

# Predefined Questions
PREDEFINED_QUESTIONS = {
    "English": [
        "What is your age?",
        "Can you describe your main problem or illness?",
        "What symptoms are you experiencing?",
        "How long have you been experiencing these symptoms?"
    ],
    "Roman Urdu": [
        "Aap ki umar kya hai?",
        "Apni bemaari ya sab se bara masla bataen?",
        "Aap ko kaunse symptoms mehsoos ho rahe hain?",
        "Ye symptoms aap ko kitne din/mahine se hain?"
    ],
    "Urdu": [
        "آپ کی عمر کیا ہے؟",
        "اپنی بیماری یا سب سے بڑا مسئلہ بیان کریں؟",
        "آپ کو کون سی علامات محسوس ہو رہی ہیں؟",
        "یہ علامات آپ کو کتنے دن/مہینے سے ہیں؟"
    ]
}


def initial_greeting(language="English"):
    # Define fallback greetings
    fallback_greetings = {
        "English": "Hi, how are you?",
        "Roman Urdu": "Helo, kese ho ap",
        "Urdu": "ہیلو، آپ کیسے ہیں؟"
    }

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            f"Greet the patient in {language} in exactly ONE sentence. "
            "Do NOT provide translations, alternatives, or explanations. "
            "Reply only with the greeting sentence."
        )
        response = model.generate_content(prompt)
        greeting = response.text.strip()
        
        # If LLM gives empty response, use fallback
        if not greeting:
            greeting = fallback_greetings.get(language, fallback_greetings["English"])
    
    except Exception as e:
        # In case of API failure, use fallback
        greeting = fallback_greetings.get(language, fallback_greetings["English"])
    
    return greeting


def generate_next_question(responses, language="English"):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = (
            f"You are assisting in a medical interview.\n\n"
            f"Conversation so far ({language}):\n"
            f"{responses}\n\n"
            "Rules:\n"
            "- Ask ONLY ONE specific follow-up question.\n"
            "- Do NOT ask general or vague questions.\n"
            "- Do NOT repeat previously asked question intent.\n"
            "- Focus on missing clinical details only.\n"
            "- If enough information is present, reply EXACTLY with: INTERVIEW_COMPLETE\n\n"
            "Output:\n"
            "- Either ONE clear question (one sentence)\n"
            "- OR the exact word: INTERVIEW_COMPLETE"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating next question: {e}")
        # Fallback question
        fallback_questions = {
            "English": "Can you provide more details about your symptoms?",
            "Roman Urdu": "Aap symptoms ke bare mein aur details de sakte hain?",
            "Urdu": "کیا آپ اپنی علامات کے بارے میں مزید تفصیلات دے سکتے ہیں؟"
        }
        return fallback_questions.get(language, fallback_questions["English"])


def reasoning_agent_gemini(responses, language="English"):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = (
            f"You are a clinical documentation assistant.\n"
            f"Patient interview answers ({language}): {responses}\n\n"
            "Generate a detailed SOAP note using this structure:\n\n"
            "SUBJECTIVE:\n"
            "- Patient-reported symptoms and history\n\n"
            "OBJECTIVE:\n"
            "- Expected physical exam findings\n"
            "- Vital signs if relevant (state if unavailable)\n\n"
            "ASSESSMENT:\n"
            "- Primary diagnosis\n"
            "- Differential diagnosis if applicable\n\n"
            "PLAN:\n"
            "- Tests\n"
            "- Medications\n"
            "- Patient advice\n"
            "- Follow-up instructions\n\n"
            "Rules:\n"
            "- Use clear bullet points\n"
            "- Be clinically realistic\n"
            "- 250–400 words\n"
            "- No markdown symbols"
        )

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating SOAP note: {e}")
        # Return a basic fallback SOAP note
        return f"""SUBJECTIVE:
- Patient reported: {', '.join(responses[:3]) if responses else 'No information provided'}

OBJECTIVE:
- Physical examination not performed (telemedicine consultation)
- Vital signs: Not available

ASSESSMENT:
- Clinical assessment pending further evaluation

PLAN:
- Further clinical evaluation recommended
- Patient to monitor symptoms
- Follow-up as needed"""


def should_stop_interview(responses, language="English"):
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = (
            f"Answers ({language}): {responses}\n"
            "Is the information sufficient to write a complete SOAP note including Subjective, Objective, Assessment, and Plan? Reply only YES or NO."
        )

        response = model.generate_content(prompt)
        return response.text.strip().upper().startswith("YES")
    except Exception as e:
        logger.error(f"Error checking if interview should stop: {e}")
        # Fallback: stop if we have at least 3 responses
        return len(responses) >= 3


def generate_pdf(soap_text):
    """Generate a professional PDF document from SOAP note text"""
    buffer = BytesIO()
    
    # Create document with proper margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(8.5*inch, 11*inch),
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Get base styles
    styles = getSampleStyleSheet()
    
    # Define custom professional styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#5f6368'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica'
    )
    
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a73e8'),
        spaceBefore=20,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        borderWidth=0,
        borderColor=colors.HexColor('#4285f4'),
        borderPadding=5
    )
    
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#202124'),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        fontName='Helvetica',
        leading=14
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=content_style,
        leftIndent=20,
        bulletIndent=10
    )
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#9aa0a6'),
        spaceBefore=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique'
    )
    
    # Build content
    content = []
    
    # Header
    content.append(Paragraph("MedAI Clinical Summary", title_style))
    content.append(Paragraph("Patient Interview & SOAP Note Documentation", subtitle_style))
    content.append(Spacer(1, 0.2*inch))
    
    # Date and time
    current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    date_para = Paragraph(f"<b>Date:</b> {current_date}", content_style)
    content.append(date_para)
    content.append(Spacer(1, 0.3*inch))
    
    # Parse SOAP note sections
    soap_sections = parse_soap_note(soap_text)
    
    # If no sections found, display as general content
    if not any(soap_sections.values()):
        # Fallback: display entire text as content
        general_header_data = [["📄 CLINICAL SUMMARY"]]
        general_table = Table(general_header_data, colWidths=[7*inch])
        general_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ]))
        content.append(general_table)
        content.append(Spacer(1, 0.15*inch))
        
        # Add all text as content
        lines = soap_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                content.append(Spacer(1, 0.1*inch))
                continue
            
            if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                clean_line = re.sub(r'^[-•*]\s*', '', line)
                para = Paragraph(f"• {clean_line}", bullet_style)
            else:
                para = Paragraph(line, content_style)
            
            content.append(para)
            content.append(Spacer(1, 0.08*inch))
    else:
        # Section colors mapping
        section_colors = {
            'SUBJECTIVE': colors.HexColor('#4285f4'),
            'OBJECTIVE': colors.HexColor('#34a853'),
            'ASSESSMENT': colors.HexColor('#ea4335'),
            'PLAN': colors.HexColor('#fbbc04')
        }
        
        section_icons = {
            'SUBJECTIVE': '📋',
            'OBJECTIVE': '🔬',
            'ASSESSMENT': '💡',
            'PLAN': '📝'
        }
        
        # Add each section
        for section_name in ['SUBJECTIVE', 'OBJECTIVE', 'ASSESSMENT', 'PLAN']:
            if section_name in soap_sections:
                # Section header with colored background
                section_color = section_colors.get(section_name, colors.HexColor('#1a73e8'))
                icon = section_icons.get(section_name, '•')
                
                # Create section header table for colored background
                section_header_data = [[f"{icon} {section_name}"]]
                section_table = Table(section_header_data, colWidths=[7*inch])
                section_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), section_color),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ]))
                content.append(section_table)
                content.append(Spacer(1, 0.15*inch))
                
                # Section content
                section_text = soap_sections[section_name]
                
                # Process content - handle bullet points and paragraphs
                lines = section_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if not line:
                        content.append(Spacer(1, 0.1*inch))
                        continue
                    
                    # Check if it's a bullet point
                    if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                        # Remove bullet and format
                        clean_line = re.sub(r'^[-•*]\s*', '', line)
                        para = Paragraph(f"• {clean_line}", bullet_style)
                    else:
                        para = Paragraph(line, content_style)
                    
                    content.append(para)
                    content.append(Spacer(1, 0.08*inch))
                
                content.append(Spacer(1, 0.2*inch))
    
    # Footer with disclaimer
    content.append(Spacer(1, 0.3*inch))
    footer_text = (
        "This document is generated by MedAI Clinical Documentation System. "
        "This is a preliminary assessment and should be reviewed by a licensed healthcare professional. "
        "For medical emergencies, please contact emergency services immediately."
    )
    content.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer


def parse_soap_note(soap_text):
    """Parse SOAP note text into structured sections"""
    sections = {
        'SUBJECTIVE': '',
        'OBJECTIVE': '',
        'ASSESSMENT': '',
        'PLAN': ''
    }
    
    # Try to extract sections using various patterns
    current_section = None
    lines = soap_text.split('\n')
    
    for line in lines:
        line_upper = line.upper().strip()
        
        # Check if this line is a section header
        if 'SUBJECTIVE' in line_upper and len(line_upper) < 20:
            current_section = 'SUBJECTIVE'
            continue
        elif 'OBJECTIVE' in line_upper and len(line_upper) < 20:
            current_section = 'OBJECTIVE'
            continue
        elif 'ASSESSMENT' in line_upper and len(line_upper) < 20:
            current_section = 'ASSESSMENT'
            continue
        elif 'PLAN' in line_upper and len(line_upper) < 20:
            current_section = 'PLAN'
            continue
        
        # Add content to current section
        if current_section:
            if sections[current_section]:
                sections[current_section] += '\n' + line
            else:
                sections[current_section] = line
    
    # If no sections found, try alternative parsing
    if not any(sections.values()):
        # Try to split by common patterns
        text_upper = soap_text.upper()
        if 'SUBJECTIVE' in text_upper:
            parts = re.split(r'SUBJECTIVE[:\s]*', soap_text, flags=re.IGNORECASE)
            if len(parts) > 1:
                remaining = parts[1]
                if 'OBJECTIVE' in remaining.upper():
                    obj_parts = re.split(r'OBJECTIVE[:\s]*', remaining, flags=re.IGNORECASE)
                    sections['SUBJECTIVE'] = obj_parts[0].strip()
                    if len(obj_parts) > 1:
                        remaining = obj_parts[1]
                        if 'ASSESSMENT' in remaining.upper():
                            ass_parts = re.split(r'ASSESSMENT[:\s]*', remaining, flags=re.IGNORECASE)
                            sections['OBJECTIVE'] = ass_parts[0].strip()
                            if len(ass_parts) > 1:
                                remaining = ass_parts[1]
                                if 'PLAN' in remaining.upper():
                                    plan_parts = re.split(r'PLAN[:\s]*', remaining, flags=re.IGNORECASE)
                                    sections['ASSESSMENT'] = plan_parts[0].strip()
                                    if len(plan_parts) > 1:
                                        sections['PLAN'] = plan_parts[1].strip()
    
    # Clean up sections - remove empty ones
    return {k: v.strip() for k, v in sections.items() if v.strip()}