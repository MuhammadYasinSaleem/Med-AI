"""
Unified Orchestrator for MedAI System
Coordinates workflows across Lab Analyzer, Interview/Triage, and Medication Interaction modules.
"""
from typing import Dict, Any, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WorkflowType(Enum):
    """Types of workflows the orchestrator can handle."""
    TRIAGE_ONLY = "triage_only"
    LAB_ANALYSIS_ONLY = "lab_analysis_only"
    MEDICATION_CHECK_ONLY = "medication_check_only"
    INTERVIEW_ONLY = "interview_only"
    COMPREHENSIVE_CARE = "comprehensive_care"  # Full patient journey
    TRIAGE_TO_LAB = "triage_to_lab"  # Triage → Lab analysis
    TRIAGE_TO_MEDICATION = "triage_to_medication"  # Triage → Medication check
    LAB_TO_MEDICATION = "lab_to_medication"  # Lab → Medication check
    INTERVIEW_TO_LAB = "interview_to_lab"  # Interview → Lab analysis


class Orchestrator:
    """
    Unified Orchestrator for coordinating all MedAI modules.
    
    Responsibilities:
    - Route requests to appropriate modules
    - Coordinate multi-step workflows
    - Manage state across modules
    - Provide intelligent workflow suggestions
    """
    
    def __init__(self):
        """Initialize the orchestrator with module handlers."""
        # Lazy imports to avoid circular dependencies
        self._triage_orchestrator = None
        self._symptom_extractor = None
        self._lab_processor = None
        self._medication_agent = None
        
    @property
    def triage_orchestrator(self):
        """Lazy load triage orchestrator."""
        if self._triage_orchestrator is None:
            from interviews.orchestrator import Orchestrator as TriageOrchestrator
            self._triage_orchestrator = TriageOrchestrator()
        return self._triage_orchestrator
    
    @property
    def symptom_extractor(self):
        """Lazy load symptom extractor."""
        if self._symptom_extractor is None:
            from interviews.symptom_extractor import SymptomExtractor
            self._symptom_extractor = SymptomExtractor()
        return self._symptom_extractor
    
    def handle_triage(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        Route triage request to interview module.
        
        Args:
            symptoms: List of extracted symptoms
            
        Returns:
            Triage result with level and message
        """
        return self.triage_orchestrator.handle_triage(symptoms)
    
    def suggest_workflow(self, context: Dict[str, Any]) -> WorkflowType:
        """
        Intelligently suggest the best workflow based on context.
        
        Args:
            context: Dictionary containing:
                - symptoms: List of symptoms (optional)
                - has_lab_report: Boolean (optional)
                - has_medications: Boolean (optional)
                - triage_level: TriageLevel (optional)
                - patient_age: int (optional)
                
        Returns:
            Suggested WorkflowType
        """
        symptoms = context.get("symptoms", [])
        has_lab_report = context.get("has_lab_report", False)
        has_medications = context.get("has_medications", False)
        triage_level = context.get("triage_level")
        
        # If triage indicates urgent/immediate, suggest comprehensive care
        if triage_level and triage_level in ["IMMEDIATE", "VERY_URGENT"]:
            return WorkflowType.COMPREHENSIVE_CARE
        
        # If symptoms present and lab report available
        if symptoms and has_lab_report:
            return WorkflowType.TRIAGE_TO_LAB
        
        # If symptoms present and medications available
        if symptoms and has_medications:
            return WorkflowType.TRIAGE_TO_MEDICATION
        
        # If lab report available and medications available
        if has_lab_report and has_medications:
            return WorkflowType.LAB_TO_MEDICATION
        
        # Default based on available data
        if symptoms:
            return WorkflowType.TRIAGE_ONLY
        elif has_lab_report:
            return WorkflowType.LAB_ANALYSIS_ONLY
        elif has_medications:
            return WorkflowType.MEDICATION_CHECK_ONLY
        
        return WorkflowType.INTERVIEW_ONLY
    
    def execute_workflow(
        self,
        workflow_type: WorkflowType,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow.
        
        Args:
            workflow_type: Type of workflow to execute
            data: Input data for the workflow
            
        Returns:
            Results from workflow execution
        """
        results = {
            "workflow_type": workflow_type.value,
            "steps": [],
            "final_result": None,
            "recommendations": []
        }
        
        try:
            if workflow_type == WorkflowType.TRIAGE_ONLY:
                symptoms = data.get("symptoms", [])
                if not symptoms and "text" in data:
                    symptoms = self.symptom_extractor.extract(data["text"])
                
                triage_result = self.handle_triage(symptoms)
                results["steps"].append({
                    "step": "triage",
                    "result": triage_result
                })
                results["final_result"] = triage_result
                
                # Add recommendations based on triage level
                triage_level = triage_result.get("triage", "STANDARD")
                if triage_level in ["IMMEDIATE", "VERY_URGENT"]:
                    results["recommendations"].append(
                        "Consider lab analysis for comprehensive assessment"
                    )
                    results["recommendations"].append(
                        "Review current medications for potential interactions"
                    )
            
            elif workflow_type == WorkflowType.TRIAGE_TO_LAB:
                # Step 1: Triage
                symptoms = data.get("symptoms", [])
                if not symptoms and "text" in data:
                    symptoms = self.symptom_extractor.extract(data["text"])
                
                triage_result = self.handle_triage(symptoms)
                results["steps"].append({
                    "step": "triage",
                    "result": triage_result
                })
                
                # Step 2: Lab Analysis (if lab report provided)
                if "lab_report_id" in data:
                    lab_result = self._process_lab_analysis(data["lab_report_id"])
                    results["steps"].append({
                        "step": "lab_analysis",
                        "result": lab_result
                    })
                    
                    # Combine results
                    results["final_result"] = {
                        "triage": triage_result,
                        "lab_analysis": lab_result,
                        "combined_assessment": self._combine_assessments(
                            triage_result, lab_result
                        )
                    }
            
            elif workflow_type == WorkflowType.TRIAGE_TO_MEDICATION:
                # Step 1: Triage
                symptoms = data.get("symptoms", [])
                if not symptoms and "text" in data:
                    symptoms = self.symptom_extractor.extract(data["text"])
                
                triage_result = self.handle_triage(symptoms)
                results["steps"].append({
                    "step": "triage",
                    "result": triage_result
                })
                
                # Step 2: Medication Check
                if "medications" in data:
                    med_result = self._check_medications(
                        data["medications"],
                        data.get("patient_age"),
                        data.get("conditions", [])
                    )
                    results["steps"].append({
                        "step": "medication_check",
                        "result": med_result
                    })
                    
                    results["final_result"] = {
                        "triage": triage_result,
                        "medication_interactions": med_result,
                        "combined_assessment": self._combine_triage_medication(
                            triage_result, med_result
                        )
                    }
            
            elif workflow_type == WorkflowType.COMPREHENSIVE_CARE:
                # Full workflow: Triage → Lab → Medication
                symptoms = data.get("symptoms", [])
                if not symptoms and "text" in data:
                    symptoms = self.symptom_extractor.extract(data["text"])
                
                # Triage
                triage_result = self.handle_triage(symptoms)
                results["steps"].append({
                    "step": "triage",
                    "result": triage_result
                })
                
                # Lab Analysis (if available)
                if "lab_report_id" in data:
                    lab_result = self._process_lab_analysis(data["lab_report_id"])
                    results["steps"].append({
                        "step": "lab_analysis",
                        "result": lab_result
                    })
                
                # Medication Check (if available)
                if "medications" in data:
                    med_result = self._check_medications(
                        data["medications"],
                        data.get("patient_age"),
                        data.get("conditions", [])
                    )
                    results["steps"].append({
                        "step": "medication_check",
                        "result": med_result
                    })
                
                # Combine all results
                results["final_result"] = {
                    "triage": triage_result,
                    "lab_analysis": results["steps"][1]["result"] if len(results["steps"]) > 1 else None,
                    "medication_interactions": results["steps"][-1]["result"] if len(results["steps"]) > 2 else None,
                    "comprehensive_assessment": self._generate_comprehensive_assessment(results["steps"])
                }
            
            else:
                results["error"] = f"Workflow type {workflow_type.value} not yet implemented"
        
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_type.value}: {str(e)}")
            results["error"] = str(e)
        
        return results
    
    def _process_lab_analysis(self, report_id: str) -> Dict[str, Any]:
        """Process lab report analysis."""
        try:
            from lab_analyzer.models import LabReport, AnalysisResult
            from lab_analyzer.processing import process_lab_report_sync
            
            result = process_lab_report_sync(report_id)
            
            if result.get("status") == "success":
                lab_report = LabReport.objects.get(id=report_id)
                analysis = AnalysisResult.objects.filter(lab_report=lab_report).first()
                
                return {
                    "status": "success",
                    "critical_findings": analysis.critical_findings if analysis else [],
                    "abnormal_findings": analysis.abnormal_findings if analysis else [],
                    "summary": analysis.get_humanistic_summary() if analysis else None
                }
            else:
                return {
                    "status": "failed",
                    "error": result.get("error", "Unknown error")
                }
        except Exception as e:
            logger.error(f"Error processing lab analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _check_medications(
        self,
        medications: List[Dict[str, Any]],
        patient_age: Optional[int] = None,
        conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Check medication interactions."""
        try:
            from medication_interaction.agent import medication_interaction_agent
            
            patient_data = {
                "age": patient_age or 0,
                "conditions": conditions or []
            }
            
            result = medication_interaction_agent(patient_data, medications)
            
            return {
                "status": "success",
                "severity": result.get("severity", "MINOR"),
                "findings": result.get("findings", []),
                "interaction_graph": result.get("interaction_graph", {})
            }
        except Exception as e:
            logger.error(f"Error checking medications: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _combine_assessments(
        self,
        triage_result: Dict[str, Any],
        lab_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine triage and lab results into unified assessment."""
        triage_level = triage_result.get("triage", "STANDARD")
        critical_findings = lab_result.get("critical_findings", [])
        
        # If triage is urgent and lab shows critical values, escalate
        if triage_level in ["IMMEDIATE", "VERY_URGENT"] and critical_findings:
            return {
                "urgency": "CRITICAL",
                "message": "Urgent triage combined with critical lab values requires immediate attention",
                "recommendations": [
                    "Immediate medical evaluation required",
                    "Consider medication review",
                    "Monitor closely"
                ]
            }
        
        return {
            "urgency": triage_level,
            "message": "Combined assessment complete",
            "recommendations": []
        }
    
    def _combine_triage_medication(
        self,
        triage_result: Dict[str, Any],
        med_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine triage and medication interaction results."""
        triage_level = triage_result.get("triage", "STANDARD")
        med_severity = med_result.get("severity", "MINOR")
        
        # If both triage and medications indicate problems
        if triage_level in ["IMMEDIATE", "VERY_URGENT"] and med_severity in ["CONTRAINDICATED", "MAJOR"]:
            return {
                "urgency": "CRITICAL",
                "message": "Urgent symptoms combined with serious medication interactions",
                "recommendations": [
                    "Immediate medical evaluation required",
                    "Review medication regimen urgently",
                    "Consider discontinuing problematic medications"
                ]
            }
        
        return {
            "urgency": triage_level,
            "message": "Combined assessment complete",
            "recommendations": []
        }
    
    def _generate_comprehensive_assessment(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive assessment from all workflow steps."""
        assessment = {
            "overall_urgency": "STANDARD",
            "key_findings": [],
            "recommendations": [],
            "next_steps": []
        }
        
        # Extract key information from each step
        for step_data in steps:
            step_name = step_data.get("step")
            step_result = step_data.get("result", {})
            
            if step_name == "triage":
                triage_level = step_result.get("triage", "STANDARD")
                assessment["overall_urgency"] = triage_level
                assessment["key_findings"].append(f"Triage Level: {triage_level}")
            
            elif step_name == "lab_analysis":
                critical = step_result.get("critical_findings", [])
                if critical:
                    assessment["overall_urgency"] = "IMMEDIATE"
                    assessment["key_findings"].append(f"Critical lab values detected: {len(critical)}")
            
            elif step_name == "medication_check":
                severity = step_result.get("severity", "MINOR")
                if severity in ["CONTRAINDICATED", "MAJOR"]:
                    assessment["key_findings"].append(f"Serious medication interactions: {severity}")
                    if assessment["overall_urgency"] == "STANDARD":
                        assessment["overall_urgency"] = "URGENT"
        
        # Generate recommendations
        if assessment["overall_urgency"] in ["IMMEDIATE", "VERY_URGENT"]:
            assessment["recommendations"].append("Immediate medical evaluation required")
            assessment["next_steps"].append("Contact emergency services if needed")
        
        return assessment


# Global orchestrator instance
orchestrator = Orchestrator()
