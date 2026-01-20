"""
Reasoning Agent: Uses Google Gemini API to analyze lab values and generate clinical insights.
"""
import json
import logging
import os
from typing import Dict, Any, List
from django.conf import settings

logger = logging.getLogger(__name__)

# Global Gemini model instance (initialized once)
_gemini_model = None


class ReasoningAgent:
    """Agent responsible for AI-powered analysis of lab values using Gemini API."""
    
    def __init__(self):
        """Initialize reasoning agent with Google Gemini API."""
        global _gemini_model
        
        # Use settings with fallback to universal paid key
        universal_key = 'AIzaSyB8tF9bjsK1hNpzIG74uBOSIQKs77VGx9g'
        self.api_key = settings.GOOGLE_API_KEY or settings.GEMINI_API_KEY or universal_key
        
        if not self.api_key:
            logger.warning("Using fallback universal API key")
            self.api_key = universal_key
        
        # Initialize Gemini if not already initialized
        if _gemini_model is None:
            try:
                import google.generativeai as genai
                
                # Configure the API key
                genai.configure(api_key=self.api_key)
                
                # Use Gemini 2.5 Flash model
                model_name = 'gemini-2.5-flash'
                _gemini_model = genai.GenerativeModel(model_name)
                logger.info(f"Using Gemini model: {model_name}")
                
                logger.info("Gemini API initialized successfully")
            except ImportError:
                logger.error("google-generativeai not installed. Install with: pip install google-generativeai")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {str(e)}")
                raise
        
        self.model = _gemini_model
        self.current_language = 'en'  # Default language
    
    def analyze(self, extracted_text: str, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze lab report text and generate structured findings.
        
        Args:
            extracted_text: Raw text extracted from lab report
            patient_data: Patient demographics (name, age, gender, preferred_language)
            
        Returns:
            Structured analysis data with findings and SOAP note
        """
        # Store current language for use in prompts
        self.current_language = patient_data.get('preferred_language', 'en')
        
        try:
            # Step 1: Extract lab values
            extraction_prompt = self._get_extraction_prompt(extracted_text)
            extracted_values = self._call_llm(extraction_prompt, temperature=0.1, require_json=True)
            
            # Step 2: Analyze with patient context
            analysis_prompt = self._get_analysis_prompt(extracted_values, patient_data)
            analysis_result = self._call_llm(analysis_prompt, temperature=0.2, require_json=True)
            
            # Step 3: Generate humanistic summary
            summary_prompt = self._get_summary_prompt(analysis_result, patient_data)
            humanistic_summary = self._call_llm(summary_prompt, temperature=0.3, require_json=False)
            
            # Step 4: Generate SOAP note
            soap_prompt = self._get_soap_prompt(analysis_result, patient_data)
            soap_note = self._call_llm(soap_prompt, temperature=0.3, require_json=True)
            
            # Parse JSON responses
            try:
                # Log raw responses for debugging
                logger.debug(f"Extracted values response length: {len(extracted_values)}")
                logger.debug(f"Analysis result response length: {len(analysis_result)}")
                logger.debug(f"SOAP note response length: {len(soap_note)}")
                
                extracted_values_json = json.loads(extracted_values)
                analysis_json = json.loads(analysis_result)
                soap_json = json.loads(soap_note)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM JSON response: {e}")
                logger.error(f"Extracted values (first 500 chars): {extracted_values[:500]}")
                logger.error(f"Analysis result (first 500 chars): {analysis_result[:500]}")
                logger.error(f"SOAP note (first 500 chars): {soap_note[:500]}")
                # Fallback to structured format
                return self._create_fallback_response(extracted_text, patient_data)
            
            # Combine results
            return {
                'analysis_id': str(patient_data.get('name', 'unknown')).lower().replace(' ', '_'),
                'status': 'completed',
                'extracted_values': extracted_values_json,
                'humanistic_summary': humanistic_summary.strip(),
                'critical_findings': analysis_json.get('critical_findings', []),
                'abnormal_findings': analysis_json.get('abnormal_findings', []),
                'normal_findings': analysis_json.get('normal_findings', []),
                'clinical_summary': soap_json,
                'metadata': {
                    'llm_model': 'gemini-2.5-flash',
                    'patient_context_used': True,
                }
            }
            
        except Exception as e:
            logger.error(f"Error in reasoning agent: {str(e)}")
            return self._create_fallback_response(extracted_text, patient_data)
    
    def _call_llm(self, prompt: str, temperature: float = 0.2, require_json: bool = True) -> str:
        """Call Gemini API with prompt."""
        try:
            # Ensure prompt requests JSON if require_json is True
            if require_json and "json" not in prompt.lower():
                prompt = prompt + "\n\nReturn complete valid JSON only. No markdown, no extra text. NO disease names."
            
            # System instruction for medical analysis
            language_names = {'en': 'English', 'ur': 'Urdu', 'pa': 'Punjabi', 'ps': 'Pashto', 'sd': 'Sindhi'}
            lang_name = language_names.get(self.current_language, 'English')
            
            system_instruction = f"Medical AI assistant. Analyze lab reports. CRITICAL: NEVER mention disease names, conditions, or diagnoses. You are NOT a doctor. Only flag abnormal values and explain what they mean in general terms. NO disease names. Support multiple languages including {lang_name}. Return complete JSON. Keep responses brief and concise."
            
            # Combine system instruction with user prompt
            full_prompt = f"{system_instruction}\n\n{prompt}"
            
            # Generate response using Gemini
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': 8192,  # Increased for longer responses
            }
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Check if response was truncated
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = response.candidates[0].finish_reason if response.candidates else None
                if finish_reason == 'MAX_TOKENS':
                    logger.warning("Response was truncated due to token limit. Consider increasing max_output_tokens.")
            
            # Extract text from response
            if not response or not response.text:
                logger.error(f"Empty response from Gemini API. Response: {response}")
                raise ValueError("Empty response from Gemini API")
            
            response_text = response.text.strip()
            
            # Clean up the response - remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]  # Remove ```json
            elif response_text.startswith("```"):
                response_text = response_text[3:]   # Remove ```
            
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove closing ```
            
            response_text = response_text.strip()
            
            # Log the response for debugging (first 500 chars)
            # The custom SafeUnicodeStreamHandler will handle Unicode encoding errors gracefully
            log_text = response_text[:500]
            logger.debug(f"Gemini response (first 500 chars): {log_text}")
            logger.debug(f"Gemini response length: {len(response_text)} chars")
            
            # Validate it's JSON if required
            if require_json:
                try:
                    json.loads(response_text)  # Test if it's valid JSON
                except json.JSONDecodeError as e:
                    # Try to fix incomplete JSON by finding the last complete object
                    logger.warning(f"Initial JSON parse failed: {str(e)}")
                    logger.warning(f"Response length: {len(response_text)} chars")
                    logger.warning(f"Response (first 1000 chars): {response_text[:1000]}")
                    
                    # Try to fix incomplete JSON
                    original_text = response_text
                    
                    # Method 1: Try to close incomplete JSON structures
                    if response_text.count('{') > response_text.count('}'):
                        missing_braces = response_text.count('{') - response_text.count('}')
                        # Try to find where we can safely truncate
                        # Look for the last complete array/object
                        brace_count = 0
                        bracket_count = 0
                        last_valid_pos = -1
                        
                        for i in range(len(response_text) - 1, -1, -1):
                            if response_text[i] == '}':
                                brace_count += 1
                            elif response_text[i] == '{':
                                brace_count -= 1
                            elif response_text[i] == ']':
                                bracket_count += 1
                            elif response_text[i] == '[':
                                bracket_count -= 1
                            
                            if brace_count == 0 and bracket_count == 0 and i > 0:
                                # Found a complete structure
                                last_valid_pos = i
                                break
                        
                        if last_valid_pos > 0:
                            # Try truncating at the last valid position
                            test_text = response_text[:last_valid_pos + 1]
                            try:
                                json.loads(test_text)
                                response_text = test_text
                                logger.info(f"Fixed incomplete JSON by truncating at position {last_valid_pos}")
                            except:
                                pass
                    
                    # Method 2: If still invalid, try to manually close the JSON
                    if response_text != original_text:
                        try:
                            json.loads(response_text)
                        except:
                            # Try adding missing closing braces
                            missing_braces = response_text.count('{') - response_text.count('}')
                            missing_brackets = response_text.count('[') - response_text.count(']')
                            if missing_braces > 0 or missing_brackets > 0:
                                # Remove trailing incomplete content and close structures
                                # Find the last complete item in an array
                                if 'tests' in response_text or 'critical_findings' in response_text:
                                    # Try to close arrays and objects
                                    fixed_text = response_text.rstrip()
                                    # Remove any trailing incomplete content (like incomplete strings)
                                    # Find the last complete quote or comma
                                    last_comma = fixed_text.rfind(',')
                                    last_quote = max(fixed_text.rfind('"'), fixed_text.rfind("'"))
                                    if last_comma > last_quote:
                                        # Remove incomplete item after last comma
                                        fixed_text = fixed_text[:last_comma]
                                    
                                    # Close structures
                                    fixed_text += ']' * missing_brackets
                                    fixed_text += '}' * missing_braces
                                    
                                    try:
                                        json.loads(fixed_text)
                                        response_text = fixed_text
                                        logger.info("Fixed incomplete JSON by manually closing structures")
                                    except:
                                        pass
                    
                    # Final validation
                    try:
                        json.loads(response_text)
                    except json.JSONDecodeError as e2:
                        logger.error(f"Response is not valid JSON after fixes. Error: {str(e2)}")
                        logger.error(f"Response (full): {response_text}")
                        raise ValueError(f"Response is not valid JSON: {str(e2)}")
            
            return response_text
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise
    
    def _get_extraction_prompt(self, text: str) -> str:
        """Generate prompt for extracting lab values."""
        return f"""Extract lab test values. Return JSON only:
{{
  "tests": [
    {{"test_name": "Name", "value": "value", "unit": "unit", "reference_range": "range", "flag": "NORMAL/ABNORMAL/HIGH/LOW/CRITICAL"}}
  ]
}}

Text: {text[:3000]}

JSON only."""

    def _get_analysis_prompt(self, extracted_values: str, patient_data: Dict) -> str:
        """Generate prompt for analyzing lab values."""
        age = patient_data.get('age', 'unknown')
        gender = patient_data.get('gender', 'unknown')
        is_pregnant = patient_data.get('is_pregnant', False)
        language = patient_data.get('preferred_language', 'en')
        pregnancy_note = " (PREGNANT)" if is_pregnant else ""
        
        language_names = {
            'en': 'English',
            'ur': 'Urdu',
            'pa': 'Punjabi',
            'ps': 'Pashto',
            'sd': 'Sindhi',
        }
        lang_name = language_names.get(language, 'English')
        
        return f"""Analyze lab results. Patient: {age}yo {gender}{pregnancy_note}. Explanation language: {lang_name}.

CRITICAL RULES:
- NEVER mention disease names, conditions, or diagnoses
- You are NOT a doctor - do NOT diagnose
- Only flag if values are high/low/critical
- Use general terms: "elevated", "low", "needs attention", "monitoring required"
- NO disease names (diabetes, anemia, kidney disease, etc.)
- Critical thresholds: K+>6.5, Glucose>400, Na+<120
- **IMPORTANT**: Test names, values, units, and reference ranges MUST be in ENGLISH
- Only explanations should be in {lang_name} language

Values: {extracted_values[:2000]}

Return JSON:
{{
  "critical_findings": [{{"test": "Name in ENGLISH", "value": "val unit in ENGLISH", "reference_range": "range in ENGLISH", "severity": "CRITICAL", "explanation": "Brief explanation in {lang_name} (NO disease names)", "immediate_actions": ["action in {lang_name}"], "time_sensitivity": "IMMEDIATE"}}],
  "abnormal_findings": [{{"test": "Name in ENGLISH", "value": "val unit in ENGLISH", "reference_range": "range in ENGLISH", "severity": "HIGH/LOW", "explanation": "Brief in {lang_name} (NO disease names)"}}],
  "normal_findings": [{{"test": "Name in ENGLISH", "value": "val unit in ENGLISH", "reference_range": "range in ENGLISH", "status": "NORMAL"}}]
}}

Keep explanations brief (1 sentence max) in {lang_name}. Test names/values/ranges in ENGLISH. NO disease names. JSON only."""

    def _get_summary_prompt(self, analysis_result: str, patient_data: Dict) -> str:
        """Generate prompt for humanistic summary."""
        age = patient_data.get('age', 'unknown')
        gender = patient_data.get('gender', 'unknown')
        language = patient_data.get('preferred_language', 'en')
        
        language_names = {
            'en': 'English',
            'ur': 'Urdu',
            'pa': 'Punjabi',
            'ps': 'Pashto',
            'sd': 'Sindhi',
        }
        lang_name = language_names.get(language, 'English')
        
        return f"""Write a natural, conversational 2-3 sentence summary as if you're a healthcare professional explaining lab results to a patient. Patient: {age}yo {gender}. Explanation language: {lang_name}.

Findings: {analysis_result[:800]}

CRITICAL RULES:
- Write summary in {lang_name} language
- **IMPORTANT**: Do NOT translate test names, values, or medical terms - keep them in ENGLISH
- Write like a human would speak - natural, caring, conversational
- NO JSON format, NO bullet points, NO structured format
- NO disease names, conditions, or diagnoses
- You are NOT a doctor - do NOT diagnose
- Use natural language: "elevated levels", "low values", "needs monitoring"
- Write flowing sentences, not structured data
- For Urdu/Punjabi/Pashto/Sindhi: Use appropriate script and natural phrasing, but keep test names in English

Examples of good natural style (English):
- "The lab results show mostly normal values, which is reassuring. There are a few slightly elevated markers that we should keep an eye on, but nothing that requires immediate concern."
- "Overall, your lab work looks good. Most values are within normal ranges. There's one value that's a bit high and may need follow-up with your doctor."

Write 2-3 natural, flowing sentences in {lang_name} as if speaking to the patient. Keep test names in ENGLISH. NO JSON, NO bullets, NO structured format. Just natural conversation in {lang_name}.

Summary:"""

    def _get_soap_prompt(self, analysis_result: str, patient_data: Dict) -> str:
        """Generate prompt for SOAP note."""
        # SOAP notes are always in English for healthcare professionals
        return f"""Create brief SOAP summary in ENGLISH. Patient: {patient_data.get('name', 'Unknown')}, {patient_data.get('age', 'N/A')}yo {patient_data.get('gender', 'N/A')}.

Findings: {analysis_result[:1500]}

CRITICAL RULES:
- NEVER mention disease names, conditions, or diagnoses
- You are NOT a doctor - do NOT diagnose
- Use general terms only: "elevated levels", "low values", "needs monitoring"
- NO disease names in any section
- **IMPORTANT**: Write ALL sections in ENGLISH - this is for healthcare professionals
- Keep test names, values, and medical terms in ENGLISH

Return JSON:
{{
  "subjective": "Brief context in ENGLISH (1 sentence, NO disease names)",
  "objective": "Key findings in ENGLISH (critical/abnormal, NO disease names)",
  "assessment": "Brief assessment in ENGLISH, NO diagnosis, NO disease names",
  "plan": "Next steps in ENGLISH (brief, NO disease names)"
}}

Keep each section to 1-2 sentences max in ENGLISH. NO disease names. JSON only."""

    def _create_fallback_response(self, text: str, patient_data: Dict) -> Dict[str, Any]:
        """Create fallback response if LLM fails."""
        return {
            'analysis_id': 'fallback',
            'status': 'completed',
            'critical_findings': [],
            'abnormal_findings': [],
            'normal_findings': [],
            'humanistic_summary': 'Unable to process lab report analysis at this time. Please retry or contact support.',
            'clinical_summary': {
                'subjective': 'Lab report analysis',
                'objective': 'Unable to process - LLM service unavailable',
                'assessment': 'Processing error',
                'plan': 'Please retry or contact support'
            },
            'metadata': {
                'llm_model': 'fallback',
                'error': 'LLM processing failed'
            }
        }
