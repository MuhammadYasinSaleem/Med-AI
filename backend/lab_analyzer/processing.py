"""
Synchronous processing function (no Celery needed).
Use this for simpler setup without Redis/Celery.
"""
import time
from django.utils import timezone

from .models import LabReport, AnalysisResult
from .ai_agents.parser import ParserAgent
from .ai_agents.reasoning import ReasoningAgent
from .ai_agents.safety import SafetyAgent


def process_lab_report_sync(report_id):
    """
    Synchronous version of lab report processing.
    No Celery/Redis needed - processes immediately.
    
    Use this for hackathon/demo when you don't want to set up Celery.
    
    Args:
        report_id: UUID string of the LabReport
        
    Returns:
        dict with status and results
    """
    start_time = time.time()
    
    try:
        # Get lab report
        lab_report = LabReport.objects.get(id=report_id)
        lab_report.mark_processing()
        
        # Step 1: Parse the document
        parser = ParserAgent()
        extracted_text = parser.parse(lab_report.file.path, lab_report.get_file_extension())
        
        if not extracted_text or len(extracted_text.strip()) < 50:
            raise ValueError("Failed to extract sufficient text from document")
        
        # Step 2: Reasoning Agent - Analyze with Gemini
        reasoning_agent = ReasoningAgent()
        patient_data = {
            'name': lab_report.patient.name,
            'age': lab_report.patient.age,
            'gender': lab_report.patient.gender,
            'is_pregnant': lab_report.patient.is_pregnant,
            'preferred_language': lab_report.patient.preferred_language,
        }
        
        analysis_data = reasoning_agent.analyze(extracted_text, patient_data)
        
        # Step 3: Safety Agent - Validate and double-check critical values
        safety_agent = SafetyAgent()
        validated_data = safety_agent.validate(analysis_data, extracted_text, patient_data)
        
        # Step 4: Save results
        processing_time = time.time() - start_time
        
        # Create or update analysis result
        analysis_result, created = AnalysisResult.objects.update_or_create(
            lab_report=lab_report,
            defaults={
                'findings': validated_data,
                'clinical_summary': validated_data.get('clinical_summary', {}).get('objective', ''),
                'critical_flags': len(validated_data.get('critical_findings', [])),
                'has_critical': len(validated_data.get('critical_findings', [])) > 0,
                'processing_time': processing_time,
            }
        )
        
        # Update metadata
        validated_data['metadata'] = validated_data.get('metadata', {})
        from django.conf import settings
        validated_data['metadata'].update({
            'processed_at': timezone.now().isoformat(),
            'processing_time': round(processing_time, 2),
            'llm_model': validated_data.get('metadata', {}).get('llm_model', 'Gemini'),
            'safety_checks_passed': True,
        })
        analysis_result.findings = validated_data
        analysis_result.save()
        
        # Mark report as completed
        lab_report.mark_completed()
        
        return {
            'status': 'success',
            'report_id': str(report_id),
            'processing_time': processing_time,
            'critical_count': analysis_result.critical_flags,
        }
        
    except LabReport.DoesNotExist:
        return {
            'status': 'error',
            'error': f'Lab report {report_id} not found'
        }
    
    except Exception as exc:
        # Mark report as failed
        try:
            lab_report = LabReport.objects.get(id=report_id)
            lab_report.mark_failed(str(exc))
        except:
            pass
        
        return {
            'status': 'error',
            'error': str(exc)
        }
