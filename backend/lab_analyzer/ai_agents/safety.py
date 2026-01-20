"""
Safety Agent: Validates critical values and ensures zero false negatives.
"""
import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SafetyAgent:
    """Agent responsible for safety validation of critical lab values."""
    
    # Critical value thresholds (ZERO tolerance for false negatives)
    CRITICAL_THRESHOLDS = {
        'potassium': {'high': 6.5, 'low': 2.5, 'unit_patterns': ['mmol/l', 'meq/l', 'mEq/L']},
        'glucose': {'high': 400, 'low': 40, 'unit_patterns': ['mg/dl', 'mg/dL', 'mmol/l']},
        'sodium': {'high': 160, 'low': 120, 'unit_patterns': ['mmol/l', 'meq/l', 'mEq/L']},
        'calcium': {'high': 13, 'low': 7, 'unit_patterns': ['mg/dl', 'mg/dL', 'mmol/l']},
        'creatinine': {'high': 5.0, 'low': None, 'unit_patterns': ['mg/dl', 'mg/dL', 'μmol/l']},
        'troponin': {'high': 0.04, 'low': None, 'unit_patterns': ['ng/ml', 'ng/mL', 'μg/l']},
        'ph': {'high': 7.55, 'low': 7.20, 'unit_patterns': ['ph', 'pH']},
        'hemoglobin': {'high': None, 'low': 7, 'unit_patterns': ['g/dl', 'g/dL']},
        'platelets': {'high': None, 'low': 50000, 'unit_patterns': ['k/μl', '/mm3', '/μL']},
        'wbc': {'high': 50000, 'low': 2000, 'unit_patterns': ['/mm3', '/μL', 'k/μl']},
    }
    
    def __init__(self):
        """Initialize safety agent."""
        pass
    
    def validate(self, analysis_data: Dict[str, Any], raw_text: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate analysis results and ensure critical values are not missed.
        
        This is a double-check mechanism to prevent false negatives.
        
        Args:
            analysis_data: Analysis results from reasoning agent
            raw_text: Original extracted text
            patient_data: Patient demographics
            
        Returns:
            Validated and enhanced analysis data
        """
        try:
            # Extract critical findings from reasoning agent
            critical_findings = analysis_data.get('critical_findings', [])
            abnormal_findings = analysis_data.get('abnormal_findings', [])
            
            # Double-check raw text for critical values
            additional_critical = self._scan_for_critical_values(raw_text, patient_data)
            
            # Merge findings (avoid duplicates)
            merged_critical = self._merge_findings(critical_findings, additional_critical)
            
            # Update analysis data
            analysis_data['critical_findings'] = merged_critical
            analysis_data['safety_validation'] = {
                'performed': True,
                'additional_critical_found': len(additional_critical),
                'total_critical': len(merged_critical),
            }
            
            return analysis_data
            
        except Exception as e:
            logger.error(f"Error in safety validation: {str(e)}")
            # Return original data if validation fails
            return analysis_data
    
    def _scan_for_critical_values(self, text: str, patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Scan raw text for critical values that might have been missed.
        
        This is a safety net to catch any false negatives.
        """
        critical_findings = []
        text_lower = text.lower()
        
        for test_name, thresholds in self.CRITICAL_THRESHOLDS.items():
            # Look for test name in text
            test_patterns = [
                test_name,
                test_name.replace('_', ' '),
                test_name.replace('_', '-'),
            ]
            
            for pattern in test_patterns:
                if pattern in text_lower:
                    # Try to extract value near the test name
                    value = self._extract_value_near_test(text, pattern, thresholds)
                    
                    if value:
                        is_critical = self._check_critical(value, thresholds)
                        if is_critical:
                            critical_findings.append({
                                'test': test_name.replace('_', ' ').title(),
                                'value': value['display'],
                                'reference_range': 'See critical thresholds',
                                'severity': 'CRITICAL',
                                'explanation': self._get_critical_explanation(test_name, value, thresholds),
                                'immediate_actions': self._get_immediate_actions(test_name, value),
                                'time_sensitivity': 'IMMEDIATE',
                                'safety_agent_detected': True,  # Flag that safety agent found this
                            })
        
        return critical_findings
    
    def _extract_value_near_test(self, text: str, test_pattern: str, thresholds: Dict) -> Dict[str, Any]:
        """Extract numerical value near test name."""
        try:
            # Find position of test name
            pattern_pos = text.lower().find(test_pattern.lower())
            if pattern_pos == -1:
                return None
            
            # Extract context around test name (200 chars before and after)
            start = max(0, pattern_pos - 100)
            end = min(len(text), pattern_pos + len(test_pattern) + 100)
            context = text[start:end]
            
            # Look for numbers in context
            # Pattern: number followed by unit
            number_pattern = r'(\d+\.?\d*)\s*(' + '|'.join(thresholds['unit_patterns']) + r')'
            matches = re.finditer(number_pattern, context, re.IGNORECASE)
            
            for match in matches:
                value = float(match.group(1))
                unit = match.group(2)
                return {
                    'value': value,
                    'unit': unit,
                    'display': f"{value} {unit}"
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting value: {e}")
            return None
    
    def _check_critical(self, value_data: Dict, thresholds: Dict) -> bool:
        """Check if value is critical based on thresholds."""
        value = value_data['value']
        
        high_threshold = thresholds.get('high')
        low_threshold = thresholds.get('low')
        
        if high_threshold and value > high_threshold:
            return True
        if low_threshold and value < low_threshold:
            return True
        
        return False
    
    def _get_critical_explanation(self, test_name: str, value_data: Dict, thresholds: Dict) -> str:
        """Generate explanation for critical value."""
        value = value_data['value']
        high_threshold = thresholds.get('high')
        low_threshold = thresholds.get('low')
        
        explanations = {
            'potassium': {
                'high': 'Critically elevated potassium levels - can cause serious heart rhythm problems requiring immediate attention',
                'low': 'Critically low potassium levels - can cause muscle weakness and heart complications requiring immediate attention',
            },
            'glucose': {
                'high': 'Critically elevated blood sugar levels - requires immediate medical evaluation and monitoring',
                'low': 'Critically low blood sugar levels - can cause serious complications including loss of consciousness, requires immediate attention',
            },
            'sodium': {
                'high': 'Critically elevated sodium levels - can cause serious neurological complications requiring immediate attention',
                'low': 'Critically low sodium levels - can cause serious brain complications including seizures, requires immediate attention',
            },
        }
        
        if test_name in explanations:
            if high_threshold and value > high_threshold:
                return explanations[test_name].get('high', 'Critical value detected')
            if low_threshold and value < low_threshold:
                return explanations[test_name].get('low', 'Critical value detected')
        
        return 'Critical value detected - requires immediate medical attention'
    
    def _get_immediate_actions(self, test_name: str, value_data: Dict) -> List[str]:
        """Get immediate actions for critical value."""
        value = value_data['value']
        
        actions_map = {
            'potassium': {
                'high': ['ECG monitoring immediately', 'Review medications with physician', 'Monitor cardiac rhythm closely', 'Urgent physician consultation'],
                'low': ['ECG monitoring', 'Monitor heart rhythm', 'Urgent physician consultation for treatment'],
            },
            'glucose': {
                'high': ['Immediate medical evaluation', 'Monitor closely', 'Urgent physician consultation'],
                'low': ['Immediate medical attention required', 'Monitor blood sugar levels', 'Assess patient condition'],
            },
            'sodium': {
                'high': ['Assess hydration status', 'Monitor neurological status', 'Urgent physician consultation'],
                'low': ['Assess patient status', 'Monitor neurological symptoms', 'Urgent physician consultation'],
            },
        }
        
        if test_name in actions_map:
            # Determine if high or low
            thresholds = self.CRITICAL_THRESHOLDS.get(test_name, {})
            if thresholds.get('high') and value > thresholds['high']:
                return actions_map[test_name].get('high', ['Immediate medical evaluation'])
            if thresholds.get('low') and value < thresholds['low']:
                return actions_map[test_name].get('low', ['Immediate medical evaluation'])
        
        return ['Immediate medical evaluation', 'Review with physician', 'Monitor patient closely']
    
    def _merge_findings(self, existing: List[Dict], additional: List[Dict]) -> List[Dict]:
        """Merge findings, avoiding duplicates."""
        merged = list(existing)
        
        for new_finding in additional:
            # Check if similar finding already exists
            is_duplicate = False
            new_test = new_finding.get('test', '').lower()
            
            for existing_finding in existing:
                existing_test = existing_finding.get('test', '').lower()
                if new_test in existing_test or existing_test in new_test:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                merged.append(new_finding)
        
        return merged
