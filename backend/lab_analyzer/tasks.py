"""
Celery tasks for async lab report processing.
"""
import time
from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from .models import LabReport, AnalysisResult
from .ai_agents.parser import ParserAgent
from .ai_agents.reasoning import ReasoningAgent
from .ai_agents.safety import SafetyAgent


@shared_task(bind=True, max_retries=3)
def process_lab_report(self, report_id):
    """
    Main task to process a lab report through the AI pipeline.
    
    Pipeline:
    1. Parse PDF/Image → Extract text
    2. Reasoning Agent → Analyze with GPT-4
    3. Safety Agent → Validate critical values
    4. Save results → Create AnalysisResult
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
        
        # Step 2: Reasoning Agent - Analyze with GPT-4
        reasoning_agent = ReasoningAgent()
        patient_data = {
            'name': lab_report.patient.name,
            'age': lab_report.patient.age,
            'gender': lab_report.patient.gender,
            'is_pregnant': lab_report.patient.is_pregnant,
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
        validated_data['metadata'].update({
            'processed_at': timezone.now().isoformat(),
            'processing_time': round(processing_time, 2),
            'llm_model': 'gpt-4',
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
        
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
