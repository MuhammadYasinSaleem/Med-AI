"""
Django views for Lab Report Analyzer.
"""
import json
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings

from .models import Patient, LabReport, AnalysisResult
from .forms import LabReportUploadForm
from .tasks import process_lab_report


def home(request):
    """Home page with upload form (Lab Report Analyzer)."""
    if request.method == 'POST':
        form = LabReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                lab_report = form.save()
                
                # Choose processing mode:
                # Option 1: Synchronous (simpler, no Celery/Redis needed) - RECOMMENDED FOR HACKATHON
                from .processing import process_lab_report_sync
                result = process_lab_report_sync(str(lab_report.id))
                
                if result['status'] == 'success':
                    messages.success(request, 'Lab report analyzed successfully!')
                    return redirect('lab_analyzer:results', report_id=lab_report.id)
                else:
                    messages.error(request, f'Analysis failed: {result.get("error", "Unknown error")}')
                    return redirect('lab_analyzer:status', report_id=lab_report.id)
                
                # Option 2: Async processing (requires Celery + Redis)
                # Uncomment below and comment out Option 1 above if you want async
                # from .tasks import process_lab_report
                # process_lab_report.delay(str(lab_report.id))
                # messages.success(request, 'Lab report uploaded successfully! Processing started.')
                # return redirect('lab_analyzer:status', report_id=lab_report.id)
            except Exception as e:
                messages.error(request, f'Error uploading file: {str(e)}')
    else:
        form = LabReportUploadForm()
    
    # Get recent reports for display
    recent_reports = LabReport.objects.select_related('patient').order_by('-uploaded_at')[:10]
    
    context = {
        'form': form,
        'recent_reports': recent_reports,
    }
    return render(request, 'upload.html', context)


@require_http_methods(["GET"])
def status(request, report_id):
    """Status page for checking processing status."""
    lab_report = get_object_or_404(
        LabReport.objects.select_related('patient'),
        id=report_id
    )
    
    # Check if analysis is complete
    has_analysis = hasattr(lab_report, 'analysis_result')
    
    context = {
        'lab_report': lab_report,
        'has_analysis': has_analysis,
        'status': lab_report.status,
    }
    
    # If HTMX request, return partial HTML
    if request.headers.get('HX-Request'):
        return render(request, 'partials/status_card.html', context)
    
    return render(request, 'status.html', context)


@require_http_methods(["GET"])
def results(request, report_id):
    """Results page displaying analysis findings."""
    lab_report = get_object_or_404(
        LabReport.objects.select_related('patient', 'analysis_result'),
        id=report_id
    )
    
    if not hasattr(lab_report, 'analysis_result'):
        messages.warning(request, 'Analysis not yet completed. Please wait.')
        return redirect('lab_analyzer:status', report_id=report_id)
    
    analysis = lab_report.analysis_result
    
    findings = analysis.findings
    humanistic_summary = findings.get('humanistic_summary', '')
    
    context = {
        'lab_report': lab_report,
        'analysis': analysis,
        'humanistic_summary': humanistic_summary,
        'critical_findings': analysis.get_critical_findings(),
        'abnormal_findings': analysis.get_abnormal_findings(),
        'normal_findings': analysis.get_normal_findings(),
        'soap_note': analysis.get_soap_note(),
        'metadata': analysis.get_metadata(),
    }
    
    return render(request, 'results.html', context)


# API endpoint for status polling (HTMX compatible)
@require_http_methods(["GET"])
def status_api(request, report_id):
    """API endpoint for status polling."""
    lab_report = get_object_or_404(LabReport, id=report_id)
    
    has_analysis = hasattr(lab_report, 'analysis_result')
    critical_count = 0
    if has_analysis:
        critical_count = lab_report.analysis_result.critical_flags
    
    return JsonResponse({
        'status': lab_report.status,
        'has_analysis': has_analysis,
        'critical_count': critical_count,
        'error_message': lab_report.error_message,
    })


# JSON API Endpoints for React Frontend
# ============================================

@csrf_exempt
@require_http_methods(["POST"])
def api_upload(request):
    """API endpoint for uploading lab reports (JSON response)."""
    try:
        form = LabReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            lab_report = form.save()
            
            # Process synchronously
            from .processing import process_lab_report_sync
            result = process_lab_report_sync(str(lab_report.id))
            
            if result['status'] == 'success':
                return JsonResponse({
                    'success': True,
                    'report_id': str(lab_report.id),
                    'status': 'completed',
                    'message': 'Lab report analyzed successfully'
                }, status=200)
            else:
                return JsonResponse({
                    'success': False,
                    'report_id': str(lab_report.id),
                    'status': 'failed',
                    'error': result.get('error', 'Unknown error')
                }, status=400)
        else:
            # Return form errors
            errors = {}
            for field, field_errors in form.errors.items():
                if hasattr(field_errors, 'as_data'):
                    errors[field] = [str(e) for e in field_errors]
                else:
                    errors[field] = [str(field_errors)] if not isinstance(field_errors, list) else [str(e) for e in field_errors]
            return JsonResponse({
                'success': False,
                'error': 'Validation failed',
                'errors': errors
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def api_results(request, report_id):
    """API endpoint for getting analysis results (JSON response)."""
    lab_report = get_object_or_404(
        LabReport.objects.select_related('patient', 'analysis_result'),
        id=report_id
    )
    
    if not hasattr(lab_report, 'analysis_result'):
        return JsonResponse({
            'success': False,
            'error': 'Analysis not yet completed'
        }, status=202)  # 202 Accepted - processing
    
    analysis = lab_report.analysis_result
    
    findings = analysis.findings
    humanistic_summary = findings.get('humanistic_summary', '')
    
    return JsonResponse({
        'success': True,
        'lab_report': {
            'id': str(lab_report.id),
            'patient': {
                'name': lab_report.patient.name,
                'age': lab_report.patient.age,
                'gender': lab_report.patient.get_gender_display(),
                'preferred_language': lab_report.patient.preferred_language,
            },
            'status': lab_report.status,
            'uploaded_at': lab_report.uploaded_at.isoformat(),
        },
        'humanistic_summary': humanistic_summary,
        'critical_findings': analysis.get_critical_findings(),
        'abnormal_findings': analysis.get_abnormal_findings(),
        'normal_findings': analysis.get_normal_findings(),
        'soap_note': analysis.get_soap_note(),
        'metadata': analysis.get_metadata(),
    })


@require_http_methods(["GET"])
def download_summary(request, report_id):
    """Download analysis summary as PDF file."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    except ImportError:
        messages.error(request, 'PDF generation library not installed. Please install reportlab.')
        return redirect('lab_analyzer:results', report_id=report_id)
    
    lab_report = get_object_or_404(
        LabReport.objects.select_related('patient', 'analysis_result'),
        id=report_id
    )
    
    if not hasattr(lab_report, 'analysis_result'):
        messages.error(request, 'Analysis not yet completed.')
        return redirect('lab_analyzer:status', report_id=report_id)
    
    analysis = lab_report.analysis_result
    critical_findings = analysis.get_critical_findings()
    abnormal_findings = analysis.get_abnormal_findings()
    normal_findings = analysis.get_normal_findings()
    soap_note = analysis.get_soap_note()
    
    # Get humanistic summary
    findings = analysis.findings
    humanistic_summary = findings.get('humanistic_summary', '')
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, 
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e293b'),
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    critical_style = ParagraphStyle(
        'CriticalStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#ef4444'),
        leading=14,
        spaceAfter=6
    )
    
    # Title
    story.append(Paragraph("LAB REPORT ANALYSIS SUMMARY", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Get patient language
    language = lab_report.patient.preferred_language
    language_names = {
        'en': 'English',
        'ur': 'Urdu (اردو)',
        'pa': 'Punjabi (ਪੰਜਾਬੀ)',
        'ps': 'Pashto (پښتو)',
        'sd': 'Sindhi (سنڌي)',
    }
    lang_display = language_names.get(language, 'English')
    
    # Patient Information
    patient_info = [
        ['Patient Name:', lab_report.patient.name],
        ['Age:', f"{lab_report.patient.age} years"],
        ['Gender:', lab_report.patient.get_gender_display()],
        ['Language:', lang_display],
        ['Report File:', lab_report.original_filename],
        ['Analyzed:', analysis.generated_at.strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    patient_table = Table(patient_info, colWidths=[2*inch, 4*inch])
    patient_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
    ]))
    story.append(patient_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Humanistic Summary
    if humanistic_summary:
        story.append(Paragraph("SUMMARY", heading_style))
        # For RTL languages, handle text direction
        # ReportLab handles Unicode automatically, but we can improve formatting
        summary_text = humanistic_summary.replace('\n', '<br/>')
        # Use Paragraph which handles Unicode and mixed scripts
        story.append(Paragraph(summary_text, normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Critical Findings
    if critical_findings:
        story.append(Paragraph(f"CRITICAL FINDINGS ({len(critical_findings)})", heading_style))
        for finding in critical_findings:
            test_name = finding.get('test', 'Unknown')
            value = finding.get('value', 'N/A')
            ref_range = finding.get('reference_range', 'N/A')
            explanation = finding.get('explanation', 'Critical value detected')
            
            # Handle multilingual text properly
            test_text = f"<b>{test_name}:</b> {value} (Range: {ref_range})"
            story.append(Paragraph(test_text, critical_style))
            story.append(Paragraph(explanation, normal_style))
            
            immediate_actions = finding.get('immediate_actions', [])
            if immediate_actions:
                actions_text = "Actions: " + ", ".join(immediate_actions)
                story.append(Paragraph(actions_text, normal_style))
            
            time_sensitivity = finding.get('time_sensitivity', '')
            if time_sensitivity:
                story.append(Paragraph(f"<b>Urgency:</b> {time_sensitivity}", normal_style))
            
            story.append(Spacer(1, 0.15*inch))
        story.append(Spacer(1, 0.2*inch))
    
    # Abnormal Findings
    if abnormal_findings:
        story.append(Paragraph(f"ABNORMAL FINDINGS ({len(abnormal_findings)})", heading_style))
        for finding in abnormal_findings:
            test_name = finding.get('test', 'Unknown')
            value = finding.get('value', 'N/A')
            severity = finding.get('severity', 'ABNORMAL')
            ref_range = finding.get('reference_range', 'N/A')
            explanation = finding.get('explanation', 'Abnormal value detected')
            
            # Handle multilingual text
            test_text = f"<b>{test_name}:</b> {value} ({severity}) - Range: {ref_range}"
            story.append(Paragraph(test_text, normal_style))
            story.append(Paragraph(explanation, normal_style))
            story.append(Spacer(1, 0.1*inch))
        story.append(Spacer(1, 0.2*inch))
    
    # Normal Findings
    if normal_findings:
        story.append(Paragraph(f"NORMAL FINDINGS: {len(normal_findings)} tests within normal range", heading_style))
        story.append(Spacer(1, 0.2*inch))
    
    # SOAP Note
    if soap_note:
        story.append(Paragraph("CLINICAL SUMMARY (SOAP)", heading_style))
        if soap_note.get('subjective'):
            story.append(Paragraph(f"<b>Subjective:</b> {soap_note['subjective']}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        if soap_note.get('objective'):
            story.append(Paragraph(f"<b>Objective:</b> {soap_note['objective']}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        if soap_note.get('assessment'):
            story.append(Paragraph(f"<b>Assessment:</b> {soap_note['assessment']}", normal_style))
            story.append(Spacer(1, 0.1*inch))
        if soap_note.get('plan'):
            story.append(Paragraph(f"<b>Plan:</b> {soap_note['plan']}", normal_style))
        story.append(Spacer(1, 0.2*inch))
    
    # Footer
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Processing Time: {analysis.processing_time:.2f}s", 
                          ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, 
                                        textColor=colors.HexColor('#64748b'), alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(pdf_content, content_type='application/pdf')
    filename = f"lab_report_summary_{lab_report.patient.name.replace(' ', '_')}_{lab_report.id.hex[:8]}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response
