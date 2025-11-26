"""
Response Normalizer - Standardizes LLM responses across different providers
Robust production version with comprehensive error handling, logging, and validation

This normalizer handles all known LLM response formats:
- OpenAI/Anthropic: Standard JSON with matched_skills, missing_skills, etc.
- Ollama (phi3): Nested in feedback.matching_skills
- Ollama (llama3.2): Various formats including required_skills (list/dict), requiredSkills (camelCase), experience dicts, overallFit
- Bedrock: Similar to OpenAI but may have different key names
"""

from typing import Dict, Any, List, Optional
import json
import re
from utils.logger import setup_logger

# Set up logger
logger = setup_logger("response_normalizer")


class CompatibilityAnalysisNormalizer:
    """Normalizes compatibility analysis responses from any LLM provider to a standard format"""
    
    # Canonical schema - this is what the application expects
    CANONICAL_SCHEMA = {
        "compatibility_score": float,  # 0-100
        "matched_skills": List[str],
        "missing_skills": List[str],
        "missing_qualifications": List[str],
        "strengths": List[Dict[str, str]],  # [{"area": "...", "description": "..."}]
        "suggestions": List[str]
    }
    
    @staticmethod
    def normalize(raw_response: Any) -> Dict[str, Any]:
        """
        Normalize any LLM response format to canonical schema
        
        Args:
            raw_response: Raw response from any LLM provider (dict, str, None, etc.)
            
        Returns:
            Normalized response matching canonical schema (always returns valid dict)
        """
        try:
            # Step 1: Pre-process input - handle strings, None, etc.
            processed_response = CompatibilityAnalysisNormalizer._preprocess_input(raw_response)
            
            if not processed_response or not isinstance(processed_response, dict):
                logger.warning(f"Invalid input type: {type(raw_response)}, returning empty normalized")
                if isinstance(raw_response, dict) and "error" in raw_response:
                    logger.error(f"Error in raw response: {raw_response.get('error')}")
                return CompatibilityAnalysisNormalizer._get_empty_normalized()
            
            logger.debug(f"Normalizing response with keys: {list(processed_response.keys())[:10]}")
            
            # Step 2: Extract each field with error handling
            normalized = {
                "compatibility_score": CompatibilityAnalysisNormalizer._safe_extract(
                    CompatibilityAnalysisNormalizer._extract_score,
                    processed_response,
                    default=0.0,
                    field_name="compatibility_score"
                ),
                "matched_skills": CompatibilityAnalysisNormalizer._safe_extract(
                    CompatibilityAnalysisNormalizer._extract_matched_skills,
                    processed_response,
                    default=[],
                    field_name="matched_skills"
                ),
                "missing_skills": CompatibilityAnalysisNormalizer._safe_extract(
                    CompatibilityAnalysisNormalizer._extract_missing_skills,
                    processed_response,
                    default=[],
                    field_name="missing_skills"
                ),
                "missing_qualifications": CompatibilityAnalysisNormalizer._safe_extract(
                    CompatibilityAnalysisNormalizer._extract_missing_qualifications,
                    processed_response,
                    default=[],
                    field_name="missing_qualifications"
                ),
                "strengths": CompatibilityAnalysisNormalizer._safe_extract(
                    CompatibilityAnalysisNormalizer._extract_strengths,
                    processed_response,
                    default=[],
                    field_name="strengths"
                ),
                "suggestions": CompatibilityAnalysisNormalizer._safe_extract(
                    CompatibilityAnalysisNormalizer._extract_suggestions,
                    processed_response,
                    default=[],
                    field_name="suggestions"
                )
            }
            
            # Step 3: Validate and fix types
            normalized = CompatibilityAnalysisNormalizer._validate_and_fix(normalized)
            
            logger.info(f"Normalization successful. Score: {normalized['compatibility_score']:.1f}, "
                       f"Matched skills: {len(normalized['matched_skills'])}, "
                       f"Missing skills: {len(normalized['missing_skills'])}, "
                       f"Suggestions: {len(normalized['suggestions'])}")
            
            return normalized
            
        except Exception as e:
            logger.error(f"Critical error in normalize(): {e}", exc_info=True)
            return CompatibilityAnalysisNormalizer._get_empty_normalized()
    
    @staticmethod
    def _preprocess_input(raw_response: Any) -> Optional[Dict[str, Any]]:
        """Pre-process input to handle strings, None, etc."""
        try:
            if raw_response is None:
                logger.debug("Input is None")
                return None
            
            # If it's a string, try to parse as JSON
            if isinstance(raw_response, str):
                raw_response = raw_response.strip()
                if not raw_response:
                    logger.debug("Input is empty string")
                    return None
                
                # Try parsing as JSON
                if (raw_response.startswith('{') or raw_response.startswith('[')):
                    try:
                        parsed = json.loads(raw_response)
                        if isinstance(parsed, dict):
                            logger.debug("Successfully parsed JSON string to dict")
                            return parsed
                        elif isinstance(parsed, list) and len(parsed) > 0:
                            # If it's a list, wrap it
                            logger.debug("Wrapping list in dict")
                            return {"data": parsed}
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON string: {e}")
                        return None
            
            # If it's already a dict, return it
            if isinstance(raw_response, dict):
                return raw_response
            
            # Unknown type
            logger.warning(f"Unknown input type: {type(raw_response)}")
            return None
            
        except Exception as e:
            logger.error(f"Error in _preprocess_input: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _safe_extract(extract_func, response: Dict[str, Any], default: Any, field_name: str = "") -> Any:
        """Safely extract data with error handling"""
        try:
            result = extract_func(response)
            if result is None:
                logger.debug(f"{field_name}: Extraction returned None, using default")
                return default
            return result
        except Exception as e:
            logger.warning(f"Error extracting {field_name} in {extract_func.__name__}: {e}")
            return default
    
    @staticmethod
    def _validate_and_fix(normalized: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix types to match canonical schema"""
        try:
            # Ensure compatibility_score is float 0-100
            score = normalized.get('compatibility_score', 0.0)
            try:
                score = float(score)
                score = max(0.0, min(100.0, score))
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid score value: {score}, defaulting to 0.0. Error: {e}")
                score = 0.0
            normalized['compatibility_score'] = score
            
            # Ensure matched_skills is List[str]
            matched = normalized.get('matched_skills', [])
            if not isinstance(matched, list):
                logger.warning(f"matched_skills is not a list: {type(matched)}, converting")
                matched = []
            normalized['matched_skills'] = [str(s).strip() for s in matched if s and str(s).strip()]
            
            # Ensure missing_skills is List[str]
            missing = normalized.get('missing_skills', [])
            if not isinstance(missing, list):
                logger.warning(f"missing_skills is not a list: {type(missing)}, converting")
                missing = []
            normalized['missing_skills'] = [str(s).strip() for s in missing if s and str(s).strip()]
            
            # Ensure missing_qualifications is List[str]
            quals = normalized.get('missing_qualifications', [])
            if not isinstance(quals, list):
                logger.warning(f"missing_qualifications is not a list: {type(quals)}, converting")
                quals = []
            normalized['missing_qualifications'] = [str(q).strip() for q in quals if q and str(q).strip()]
            
            # Ensure strengths is List[Dict[str, str]]
            strengths = normalized.get('strengths', [])
            if not isinstance(strengths, list):
                logger.warning(f"strengths is not a list: {type(strengths)}, converting")
                strengths = []
            fixed_strengths = []
            for s in strengths:
                try:
                    if isinstance(s, dict):
                        area = str(s.get('area', 'Strength')).strip()
                        desc = str(s.get('description', '')).strip()
                        if desc:  # Only add if description exists
                            fixed_strengths.append({"area": area, "description": desc})
                    elif isinstance(s, str) and s.strip():
                        fixed_strengths.append({"area": "Strength", "description": s.strip()})
                except Exception as e:
                    logger.warning(f"Error processing strength item: {e}")
                    continue
            normalized['strengths'] = fixed_strengths
            
            # Ensure suggestions is List[str]
            suggestions = normalized.get('suggestions', [])
            if not isinstance(suggestions, list):
                logger.warning(f"suggestions is not a list: {type(suggestions)}, converting")
                suggestions = []
            normalized['suggestions'] = [str(s).strip() for s in suggestions if s and str(s).strip()]
            
            return normalized
            
        except Exception as e:
            logger.error(f"Error in _validate_and_fix: {e}", exc_info=True)
            return CompatibilityAnalysisNormalizer._get_empty_normalized()
    
    @staticmethod
    def _get_empty_normalized() -> Dict[str, Any]:
        """Return empty normalized structure"""
        return {
            "compatibility_score": 0.0,
            "matched_skills": [],
            "missing_skills": [],
            "missing_qualifications": [],
            "strengths": [],
            "suggestions": []
        }
    
    @staticmethod
    def _extract_score(response: Dict[str, Any]) -> float:
        """Extract compatibility score from various formats and locations"""
        try:
            score = None
            
            # Try all possible key names (snake_case, camelCase, nested)
            possible_keys = [
                'compatibility_score', 'score', 'compatibility', 'match_score',
                'overall_score', 'fit_score'
            ]
            
            # Check direct keys first
            for key in possible_keys:
                if key in response:
                    score = response[key]
                    logger.debug(f"Found score in direct key '{key}': {score}")
                    break
            
            # Check nested in summary
            if score is None and 'summary' in response:
                try:
                    summary = response.get('summary', {})
                    if isinstance(summary, dict):
                        for key in possible_keys:
                            if key in summary:
                                score = summary[key]
                                logger.debug(f"Found score in summary.{key}: {score}")
                                break
                except Exception as e:
                    logger.debug(f"Error checking summary: {e}")
            
            # Check nested in feedback
            if score is None and 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict):
                        score = feedback.get('score') or feedback.get('compatibility_score')
                        if score is not None:
                            logger.debug(f"Found score in feedback: {score}")
                except Exception as e:
                    logger.debug(f"Error checking feedback: {e}")
            
            # Check nested in overallFit (camelCase)
            if score is None and 'overallFit' in response:
                try:
                    overall_fit = response.get('overallFit', {})
                    if isinstance(overall_fit, dict):
                        score = overall_fit.get('score') or overall_fit.get('fitScore')
                        if score is not None:
                            logger.debug(f"Found score in overallFit: {score}")
                except Exception as e:
                    logger.debug(f"Error checking overallFit: {e}")
            
            # Parse and normalize score value
            parsed_score = None
            if score is not None:
                try:
                    # Handle string formats
                    if isinstance(score, str):
                        # Remove % sign and whitespace
                        score_str = score.replace('%', '').strip()
                        # Handle fraction format like "7/10"
                        if '/' in score_str:
                            parts = score_str.split('/')
                            if len(parts) == 2:
                                parsed_score = (float(parts[0]) / float(parts[1])) * 100
                            else:
                                parsed_score = float(score_str)
                        else:
                            parsed_score = float(score_str)
                    else:
                        parsed_score = float(score)
                    
                    # Convert decimal (0.38) to percentage (38.0)
                    if 0 <= parsed_score <= 1 and parsed_score != 0:
                        parsed_score = parsed_score * 100
                    
                    # Clamp to 0-100 range
                    parsed_score = max(0.0, min(100.0, parsed_score))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse score '{score}': {e}")
                    parsed_score = None
            
            # If parsed score is None or 0, try alternative score keys
            if parsed_score is None or parsed_score == 0:
                # Try alternative score keys (some LLMs use different names)
                alternative_scores = [
                    'match_percentage', 'relevance_score', 'alignment_score', 
                    'overall_fit', 'fit_score', 'match_score'
                ]
                for alt_key in alternative_scores:
                    if alt_key in response:
                        try:
                            alt_score = response[alt_key]
                            if isinstance(alt_score, (int, float)):
                                alt_parsed = float(alt_score)
                                # If it's already a percentage (0-100), use it
                                if alt_parsed > 1:
                                    result = max(0.0, min(100.0, alt_parsed))
                                    logger.debug(f"Found score in alternative key '{alt_key}': {result}")
                                    return result
                                # If it's a decimal, convert
                                elif alt_parsed > 0:
                                    result = max(0.0, min(100.0, alt_parsed * 100))
                                    logger.debug(f"Found score in alternative key '{alt_key}' (converted): {result}")
                                    return result
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Error parsing alternative score '{alt_key}': {e}")
                            continue
            
            return parsed_score if parsed_score is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error in _extract_score: {e}", exc_info=True)
            return 0.0
    
    @staticmethod
    def _extract_matched_skills(response: Dict[str, Any]) -> List[str]:
        """Extract matched skills from various formats and locations"""
        try:
            skills = []
            
            # Strategy: Try all possible locations, collect all skills, then deduplicate
            
            # 1. Direct matched_skills key
            if 'matched_skills' in response:
                try:
                    raw_skills = response['matched_skills']
                    raw_skills = CompatibilityAnalysisNormalizer._parse_json_string(raw_skills)
                    skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(raw_skills))
                except Exception as e:
                    logger.debug(f"Error extracting from matched_skills: {e}")
            
            # 2. feedback.matching_skills or feedback.matched_skills (phi3 format)
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict):
                        for key in ['matching_skills', 'matched_skills', 'skills_match']:
                            if key in feedback:
                                try:
                                    raw_skills = CompatibilityAnalysisNormalizer._parse_json_string(feedback[key])
                                    skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(raw_skills))
                                except Exception as e:
                                    logger.debug(f"Error extracting from feedback.{key}: {e}")
                except Exception as e:
                    logger.debug(f"Error checking feedback: {e}")
            
            # 3. alignment.required_skills (llama3.2 format)
            if 'alignment' in response:
                try:
                    alignment = response.get('alignment', {})
                    if isinstance(alignment, dict) and 'required_skills' in alignment:
                        raw_skills = CompatibilityAnalysisNormalizer._parse_json_string(alignment['required_skills'])
                        if isinstance(raw_skills, list):
                            skills.extend([str(s) for s in raw_skills if s])
                except Exception as e:
                    logger.debug(f"Error checking alignment: {e}")
            
            # 4. required_skills - ONLY extract if it's a dict with boolean/score values (indicating matched skills)
            # DO NOT extract from required_skills if it's a simple list (that's the full list, not matched)
            if 'required_skills' in response:
                try:
                    required_skills = response.get('required_skills')
                    required_skills = CompatibilityAnalysisNormalizer._parse_json_string(required_skills)
                    
                    # Only treat as matched skills if it's a dict with boolean/score values
                    # This indicates which required skills are matched
                    if isinstance(required_skills, dict):
                        # Check for structured format FIRST: {'area': '...', 'description': [...]}
                        if 'description' in required_skills:
                            desc = required_skills['description']
                            if isinstance(desc, list):
                                skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(desc))
                            elif isinstance(desc, str):
                                skills.append(desc)
                        elif 'area' in required_skills and len(required_skills) == 1:
                            skills.append(str(required_skills['area']))
                        else:
                            # Standard dict format: {'Python': 0.83, 'JavaScript': 0.67} or {'Python': true}
                            # Only extract skills where value is truthy (indicating they're matched)
                            for skill_key, skill_value in required_skills.items():
                                if skill_value:
                                    skills.append(str(skill_key))
                    # If it's a list, DO NOT extract - that's the full required list, not matched
                    # Matched skills should come from matched_skills key, not required_skills list
                except Exception as e:
                    logger.debug(f"Error extracting from required_skills: {e}")
            
            # 5. requiredSkills (camelCase) - ONLY extract if it's a dict with boolean/score values
            # DO NOT extract from requiredSkills if it's a simple list (that's the full list, not matched)
            if 'requiredSkills' in response:
                 try:
                     required_skills = response.get('requiredSkills')
                     required_skills = CompatibilityAnalysisNormalizer._parse_json_string(required_skills)
                     
                     # Only treat as matched skills if it's a dict with boolean/score values
                     if isinstance(required_skills, dict):
                         if 'description' in required_skills:
                             desc = required_skills['description']
                             if isinstance(desc, list):
                                 skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(desc))
                             elif isinstance(desc, str):
                                 skills.append(desc)
                         elif 'area' in required_skills and len(required_skills) == 1:
                             skills.append(str(required_skills['area']))
                         else:
                             # Standard dict with scores or booleans: {'Python': 0.83, 'JavaScript': 0.67}
                             for skill_key, skill_value in required_skills.items():
                                 if skill_value:
                                     skills.append(str(skill_key))
                     # If it's a list, DO NOT extract - that's the full required list, not matched
                 except Exception as e:
                     logger.debug(f"Error extracting from requiredSkills: {e}")
            
            # 6. job_requirements_alignment.matching_skills
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict) and 'job_requirements_alignment' in feedback:
                        alignment = feedback.get('job_requirements_alignment', {})
                        if isinstance(alignment, dict) and 'matching_skills' in alignment:
                            raw_skills = CompatibilityAnalysisNormalizer._parse_json_string(alignment['matching_skills'])
                            skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(raw_skills))
                except Exception as e:
                    logger.debug(f"Error checking job_requirements_alignment: {e}")
            
            # 7. analysis.matched_skills (new format: list of dicts with 'name' key)
            if 'analysis' in response:
                try:
                    analysis = response.get('analysis', {})
                    if isinstance(analysis, dict):
                        matched_skills = analysis.get('matched_skills', [])
                        if isinstance(matched_skills, list):
                            for skill_item in matched_skills:
                                try:
                                    if isinstance(skill_item, dict):
                                        skill_name = skill_item.get('name') or skill_item.get('skill')
                                        if skill_name:
                                            skills.append(str(skill_name))
                                    elif isinstance(skill_item, str):
                                        skills.append(skill_item)
                                except Exception as e:
                                    logger.debug(f"Error processing skill_item: {e}")
                                    continue
                except Exception as e:
                    logger.debug(f"Error checking analysis: {e}")
            
            # Deduplicate and clean
            result = list(dict.fromkeys([s.strip() for s in skills if s and s.strip()]))
            logger.debug(f"Extracted {len(result)} matched skills")
            return result
            
        except Exception as e:
            logger.error(f"Error in _extract_matched_skills: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _extract_missing_skills(response: Dict[str, Any]) -> List[str]:
        """Extract missing skills from various formats"""
        try:
            skills = []
            
            # Direct key
            if 'missing_skills' in response:
                try:
                    skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(response['missing_skills']))
                except Exception as e:
                    logger.debug(f"Error extracting from missing_skills: {e}")
            
            # From feedback
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict):
                        for key in ['missing_skills', 'missing_required_skills', 'missing_skills_list']:
                            if key in feedback:
                                try:
                                    raw_skills = feedback.get(key, [])
                                    if raw_skills:
                                        skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(raw_skills))
                                except Exception as e:
                                    logger.debug(f"Error extracting from feedback.{key}: {e}")
                except Exception as e:
                    logger.debug(f"Error checking feedback: {e}")
            
            # From unmatched_skills (direct key)
            if 'unmatched_skills' in response:
                try:
                    unmatched = response.get('unmatched_skills', [])
                    if unmatched:
                        skills.extend(CompatibilityAnalysisNormalizer._normalize_skills_list(unmatched))
                except Exception as e:
                    logger.debug(f"Error extracting from unmatched_skills: {e}")
            
            # From areas_of_improvement
            if 'areas_of_improvement' in response:
                try:
                    areas = response.get('areas_of_improvement', [])
                    if isinstance(areas, list):
                        for area in areas:
                            try:
                                if isinstance(area, dict) and 'area' in area:
                                    skills.append(str(area['area']))
                            except Exception as e:
                                logger.debug(f"Error processing area: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error checking areas_of_improvement: {e}")
            
            # Calculate missing skills by comparing required_skills with matched_skills
            # Only if we haven't found any missing skills yet
            if not skills:
                try:
                    required_skills = []
                    matched_skills = []
                    
                    # Get required_skills from various locations
                    if 'required_skills' in response:
                        required_raw = response.get('required_skills', [])
                        required_skills = CompatibilityAnalysisNormalizer._normalize_skills_list(required_raw)
                    
                    # Also check feedback.required_skills
                    if 'feedback' in response:
                        feedback = response.get('feedback', {})
                        if isinstance(feedback, dict) and 'required_skills' in feedback:
                            required_raw = feedback.get('required_skills', [])
                            required_skills = CompatibilityAnalysisNormalizer._normalize_skills_list(required_raw)
                        elif isinstance(feedback, list):
                            # If feedback is a list, check first item for required_skills
                            for item in feedback:
                                if isinstance(item, dict) and 'required_skills' in item:
                                    required_raw = item.get('required_skills', [])
                                    required_skills = CompatibilityAnalysisNormalizer._normalize_skills_list(required_raw)
                                    break
                    
                    # Get matched_skills (already normalized from _extract_matched_skills)
                    # We need to call it here to get the matched skills
                    matched_skills = CompatibilityAnalysisNormalizer._extract_matched_skills(response)
                    
                    # Calculate missing: required - matched
                    if required_skills and matched_skills:
                        required_set = set(s.lower().strip() for s in required_skills if s)
                        matched_set = set(s.lower().strip() for s in matched_skills if s)
                        missing_set = required_set - matched_set
                        
                        # Convert back to original case from required_skills
                        for req_skill in required_skills:
                            if req_skill.lower().strip() in missing_set:
                                skills.append(req_skill)
                                missing_set.discard(req_skill.lower().strip())
                        
                        logger.debug(f"Calculated {len(skills)} missing skills from required_skills ({len(required_skills)}) - matched_skills ({len(matched_skills)})")
                except Exception as e:
                    logger.debug(f"Error calculating missing skills: {e}")
            
            # Deduplicate and clean
            result = list(dict.fromkeys([s.strip() for s in skills if s and s.strip()]))
            logger.debug(f"Extracted {len(result)} missing skills")
            return result
            
        except Exception as e:
            logger.error(f"Error in _extract_missing_skills: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _extract_missing_qualifications(response: Dict[str, Any]) -> List[str]:
        """Extract missing qualifications"""
        try:
            quals = []
            
            if 'missing_qualifications' in response:
                try:
                    raw_quals = response.get('missing_qualifications', [])
                    if isinstance(raw_quals, list):
                        quals = [str(q) for q in raw_quals if q]
                except Exception as e:
                    logger.debug(f"Error extracting missing_qualifications: {e}")
            
            # Also check job_description.required_skills if available (for comparison)
            if 'job_description' in response:
                try:
                    jd = response.get('job_description', {})
                    if isinstance(jd, dict) and 'job_requirements' in jd:
                        requirements = jd.get('job_requirements', [])
                        if isinstance(requirements, list):
                            for req in requirements:
                                try:
                                    if isinstance(req, str) and ('years' in req.lower() or 'required' in req.lower()):
                                        quals.append(req)
                                except Exception as e:
                                    logger.debug(f"Error processing requirement: {e}")
                                    continue
                except Exception as e:
                    logger.debug(f"Error checking job_description: {e}")
            
            result = [q.strip() for q in quals if q and q.strip()]
            logger.debug(f"Extracted {len(result)} missing qualifications")
            return result
            
        except Exception as e:
            logger.error(f"Error in _extract_missing_qualifications: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _extract_strengths(response: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract strengths and normalize to standard format"""
        try:
            strengths = []
            
            # 1. Direct strengths key
            raw_strengths = response.get('strengths', [])
            
            # 2. From nested locations
            if not raw_strengths and 'summary' in response:
                try:
                    summary = response.get('summary', {})
                    if isinstance(summary, dict):
                        raw_strengths = summary.get('strengths', [])
                except Exception as e:
                    logger.debug(f"Error checking summary: {e}")
            
            if not raw_strengths and 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict):
                        raw_strengths = feedback.get('strengths', [])
                except Exception as e:
                    logger.debug(f"Error checking feedback.strengths: {e}")
            
            # 3. Extract from feedback.experience_relevance, feedback.alignment_with_job_requirements (llama3.2 format)
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict):
                        # Check experience_relevance
                        if 'experience_relevance' in feedback:
                            try:
                                exp_rel = feedback.get('experience_relevance', {})
                                if isinstance(exp_rel, dict):
                                    reasoning = exp_rel.get('reasoning', '')
                                    if reasoning and isinstance(reasoning, str) and reasoning.strip():
                                        strengths.append({
                                            "area": "Experience Relevance",
                                            "description": reasoning
                                        })
                                    comments = exp_rel.get('comments', [])
                                    if isinstance(comments, list):
                                        for comment in comments:
                                            if isinstance(comment, str) and comment.strip():
                                                strengths.append({
                                                    "area": "Experience Relevance",
                                                    "description": comment
                                                })
                                    description = exp_rel.get('description', '')
                                    if description and isinstance(description, str) and description.strip():
                                        if any(word in description.lower() for word in ['relevant', 'aligns', 'highlights', 'good']):
                                            strengths.append({
                                                "area": "Experience Relevance",
                                                "description": description
                                            })
                            except Exception as e:
                                logger.debug(f"Error extracting experience_relevance: {e}")
                        
                        # Check alignment_with_job_requirements
                        if 'alignment_with_job_requirements' in feedback:
                            try:
                                alignment = feedback.get('alignment_with_job_requirements', {})
                                if isinstance(alignment, dict):
                                    reasoning = alignment.get('reasoning', '')
                                    if reasoning and isinstance(reasoning, str) and reasoning.strip():
                                        strengths.append({
                                            "area": "Job Alignment",
                                            "description": reasoning
                                        })
                                    comments = alignment.get('comments', [])
                                    if isinstance(comments, list):
                                        for comment in comments:
                                            if isinstance(comment, str) and comment.strip():
                                                strengths.append({
                                                    "area": "Job Alignment",
                                                    "description": comment
                                                })
                                    description = alignment.get('description', '')
                                    if description and isinstance(description, str) and description.strip():
                                        if any(word in description.lower() for word in ['alignment is good', 'good', 'strong', 'aligns']):
                                            strengths.append({
                                                "area": "Job Alignment",
                                                "description": description
                                            })
                            except Exception as e:
                                logger.debug(f"Error extracting alignment_with_job_requirements: {e}")
                        
                        # Check overall_fit
                        if 'overall_fit' in feedback:
                            try:
                                overall_fit = feedback.get('overall_fit', {})
                                if isinstance(overall_fit, dict):
                                    reasoning = overall_fit.get('reasoning', '')
                                    if reasoning and isinstance(reasoning, str) and reasoning.strip() and ('good' in reasoning.lower() or 'strong' in reasoning.lower()):
                                        strengths.append({
                                            "area": "Overall Fit",
                                            "description": reasoning
                                        })
                                    description = overall_fit.get('description', '')
                                    if description and isinstance(description, str) and description.strip():
                                        if any(word in description.lower() for word in ['highlights', 'aligns', 'relevant', 'good', 'strong', 'fit is good']):
                                            strengths.append({
                                                "area": "Overall Fit",
                                                "description": description
                                            })
                                    comments = overall_fit.get('comments', [])
                                    if isinstance(comments, list):
                                        for comment in comments:
                                            if isinstance(comment, str) and comment.strip():
                                                if any(word in comment.lower() for word in ['highlights', 'aligns', 'relevant', 'good', 'strong']):
                                                    strengths.append({
                                                        "area": "Overall Fit",
                                                        "description": comment
                                                    })
                            except Exception as e:
                                logger.debug(f"Error extracting overall_fit: {e}")
                except Exception as e:
                    logger.debug(f"Error checking feedback structure: {e}")
            
            # 4. Extract from experience_details (llama3.2 format)
            if 'experience_details' in response:
                try:
                    exp_details = response.get('experience_details', {})
                    if isinstance(exp_details, dict):
                        exp_points = exp_details.get('experience_points', [])
                        if isinstance(exp_points, list) and exp_points:
                            for point in exp_points:
                                if isinstance(point, str) and point.strip():
                                    strengths.append({
                                        "area": "Experience",
                                        "description": point
                                    })
                        reasoning = exp_details.get('reasoning', '')
                        if reasoning and isinstance(reasoning, str) and reasoning.strip():
                            strengths.append({
                                "area": "Experience Analysis",
                                "description": reasoning
                            })
                except Exception as e:
                    logger.debug(f"Error extracting experience_details: {e}")
            
            # 5. Extract from experience dict (llama3.2 format)
            if not raw_strengths and 'experience' in response:
                try:
                    experience = response.get('experience', {})
                    experience = CompatibilityAnalysisNormalizer._parse_json_string(experience)
                    
                    exp_items = []
                    
                    if isinstance(experience, dict):
                        for key, value in experience.items():
                            if isinstance(value, dict):
                                exp_item = CompatibilityAnalysisNormalizer._format_experience_item(key, value)
                                if exp_item:
                                    exp_items.append(exp_item)
                    elif isinstance(experience, list):
                        for item in experience:
                            if isinstance(item, dict):
                                company = item.get('company', '')
                                exp_item = CompatibilityAnalysisNormalizer._format_experience_item(company, item)
                                if exp_item:
                                    exp_items.append(exp_item)
                            elif isinstance(item, str):
                                exp_items.append({
                                    "area": "Experience",
                                    "description": item
                                })
                    
                    if exp_items:
                        raw_strengths = exp_items
                except Exception as e:
                    logger.debug(f"Error extracting experience: {e}")
            
            # Normalize to standard format
            if raw_strengths:
                for strength in raw_strengths:
                    try:
                        if isinstance(strength, dict):
                            normalized = {
                                "area": str(strength.get('area', 'Strength')),
                                "description": str(strength.get('description', ''))
                            }
                            if normalized['description']:
                                strengths.append(normalized)
                        elif isinstance(strength, str):
                            strengths.append({
                                "area": "Strength",
                                "description": strength
                            })
                    except Exception as e:
                        logger.debug(f"Error normalizing strength: {e}")
                        continue
            
            logger.debug(f"Extracted {len(strengths)} strengths")
            return strengths
            
        except Exception as e:
            logger.error(f"Error in _extract_strengths: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _format_experience_item(company_or_key: str, exp_dict: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Format a single experience item into a strength - handles all possible formats"""
        try:
            # Extract all possible fields (handle both snake_case and camelCase)
            job_title = (exp_dict.get('jobTitle') or 
                        exp_dict.get('job_title') or 
                        exp_dict.get('position') or 
                        company_or_key.replace('_', ' ').title())
            
            duration = exp_dict.get('duration', '')
            summary = exp_dict.get('summary', '')
            tasks = exp_dict.get('tasks', []) or exp_dict.get('responsibilities', [])
            company = exp_dict.get('company', company_or_key)
            
            # Handle start_date and end_date if present
            start_date = exp_dict.get('start_date') or exp_dict.get('startDate', '')
            end_date = exp_dict.get('end_date') or exp_dict.get('endDate', '')
            
            # Build comprehensive description
            parts = []
            if job_title:
                parts.append(job_title)
            if company and company != company_or_key:
                parts.append(f"at {company}")
            
            # Use duration if available, otherwise construct from dates
            if duration:
                parts.append(f"({duration})")
            elif start_date:
                if end_date:
                    parts.append(f"({start_date} - {end_date})")
                else:
                    parts.append(f"({start_date} - Present)")
            
            desc_parts = []
            if summary:
                desc_parts.append(summary)
            elif tasks:
                if isinstance(tasks, list):
                    desc_parts.append(', '.join(str(t) for t in tasks[:3]))
                else:
                    desc_parts.append(str(tasks))
            
            # Only create strength if we have meaningful data
            if parts or desc_parts:
                title_part = ' - '.join(parts) if parts else 'Experience'
                desc_part = ': '.join(desc_parts) if desc_parts else ''
                description = f"{title_part}{': ' + desc_part if desc_part else ''}"
                
                return {
                    "area": "Experience",
                    "description": description
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"Error formatting experience item: {e}")
            return None
    
    @staticmethod
    def _extract_suggestions(response: Dict[str, Any]) -> List[str]:
        """Extract suggestions from various formats"""
        try:
            suggestions = []
            
            # 1. Direct keys
            for key in ['suggestions', 'improvement_suggestions', 'recommendations']:
                if key in response:
                    try:
                        raw_suggestions = response.get(key, [])
                        if raw_suggestions:
                            for sug in raw_suggestions:
                                if isinstance(sug, str):
                                    suggestions.append(sug)
                                elif isinstance(sug, dict):
                                    text = sug.get('suggestion') or sug.get('recommendation') or sug.get('text') or str(sug)
                                    suggestions.append(str(text))
                    except Exception as e:
                        logger.debug(f"Error extracting from {key}: {e}")
            
            # 2. From feedback.weaknesses
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict) and 'weaknesses' in feedback:
                        weaknesses = feedback.get('weaknesses', [])
                        for weakness in weaknesses:
                            try:
                                if isinstance(weakness, dict):
                                    rec = weakness.get('recommendation') or weakness.get('suggestion')
                                    if rec:
                                        suggestions.append(str(rec))
                                elif isinstance(weakness, str):
                                    suggestions.append(weakness)
                            except Exception as e:
                                logger.debug(f"Error processing weakness: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error checking feedback.weaknesses: {e}")
            
            # 3. From areas_of_improvement
            if 'areas_of_improvement' in response:
                try:
                    areas = response.get('areas_of_improvement', [])
                    for area in areas:
                        try:
                            if isinstance(area, dict) and 'description' in area:
                                suggestions.append(str(area['description']))
                        except Exception as e:
                            logger.debug(f"Error processing area: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"Error checking areas_of_improvement: {e}")
            
            # 4. From overall_fit string (e.g., "7/10")
            if 'overall_fit' in response:
                try:
                    overall_fit = response.get('overall_fit', '')
                    if isinstance(overall_fit, str):
                        if '/' in overall_fit:
                            parts = overall_fit.split('/')
                            if len(parts) == 2:
                                score = (float(parts[0]) / float(parts[1])) * 100
                                if score < 70:
                                    suggestions.append(f"Overall fit is {overall_fit}. Consider highlighting more relevant experience and skills.")
                except (ValueError, TypeError):
                    pass
            
            # 5. From overallFit dict (camelCase)
            if 'overallFit' in response:
                try:
                    overall_fit = response.get('overallFit', {})
                    if isinstance(overall_fit, dict):
                        reasons_for_disfit = overall_fit.get('reasonsForDisfit', [])
                        if reasons_for_disfit:
                            for reason in reasons_for_disfit:
                                try:
                                    if isinstance(reason, str):
                                        suggestions.append(f"Address: {reason}")
                                    elif isinstance(reason, dict):
                                        text = reason.get('reason') or reason.get('description') or str(reason)
                                        suggestions.append(f"Address: {text}")
                                except Exception as e:
                                    logger.debug(f"Error processing disfit reason: {e}")
                                    continue
                        
                        if not suggestions:
                            reasons_for_fit = overall_fit.get('reasonsForFit', [])
                            if reasons_for_fit:
                                for reason in reasons_for_fit:
                                    try:
                                        if isinstance(reason, str):
                                            suggestions.append(f"Continue emphasizing: {reason}")
                                    except Exception as e:
                                        logger.debug(f"Error processing fit reason: {e}")
                                        continue
                except Exception as e:
                    logger.debug(f"Error checking overallFit: {e}")
            
            # 6. From alignment dict
            if 'alignment' in response:
                try:
                    alignment = response.get('alignment', {})
                    if isinstance(alignment, dict):
                        requires_alignment = alignment.get('requiresAlignment', False)
                        reasons = alignment.get('reasonsForAlignment', [])
                        discrepancies = alignment.get('discrepancies', [])
                        
                        if requires_alignment and reasons:
                            for reason in reasons:
                                if isinstance(reason, str):
                                    suggestions.append(f"Focus on: {reason}")
                        
                        if discrepancies:
                            for disc in discrepancies:
                                if isinstance(disc, str):
                                    suggestions.append(f"Address discrepancy: {disc}")
                except Exception as e:
                    logger.debug(f"Error checking alignment: {e}")
            
            # 7. From feedback nested structure (llama3.2 format)
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    if isinstance(feedback, dict):
                        for key, value in feedback.items():
                            if isinstance(value, dict):
                                try:
                                    reasoning = value.get('reasoning', '')
                                    if reasoning and isinstance(reasoning, str) and reasoning.strip():
                                        improvement_keywords = ['missing', 'lack', 'improve', 'consider', 'should', 'could', 'need', 'more specific', 'details missing', 'ambiguity', 'could be']
                                        if any(keyword in reasoning.lower() for keyword in improvement_keywords):
                                            suggestions.append(reasoning)
                                    
                                    comments = value.get('comments', [])
                                    if isinstance(comments, list):
                                        for comment in comments:
                                            if isinstance(comment, str) and comment.strip():
                                                improvement_keywords = ['missing', 'lack', 'improve', 'consider', 'should', 'could', 'need', 'more specific', 'details missing', 'ambiguity', 'could be', 'but', 'however', 'only mentions']
                                                if any(keyword in comment.lower() for keyword in improvement_keywords):
                                                    suggestions.append(comment)
                                    
                                    percentage_match = value.get('percentage_match') or value.get('relevance_score') or value.get('alignment_score') or value.get('fit_score')
                                    if isinstance(percentage_match, (int, float)):
                                        if 0 <= percentage_match <= 1:
                                            percentage_match = percentage_match * 100
                                        if percentage_match < 70:
                                            area_name = key.replace('_', ' ').title()
                                            suggestions.append(f"Improve {area_name}: Current match is {percentage_match:.1f}%. Consider highlighting more relevant experience.")
                                except Exception as e:
                                    logger.debug(f"Error processing feedback.{key}: {e}")
                                    continue
                except Exception as e:
                    logger.debug(f"Error checking feedback structure: {e}")
            
            # 8. From experience_details.reasoning
            if 'experience_details' in response:
                try:
                    exp_details = response.get('experience_details', {})
                    if isinstance(exp_details, dict):
                        reasoning = exp_details.get('reasoning', '')
                        if reasoning and isinstance(reasoning, str) and reasoning.strip():
                            improvement_keywords = ['missing', 'lack', 'improve', 'consider', 'should', 'could', 'need', 'details missing']
                            if any(keyword in reasoning.lower() for keyword in improvement_keywords):
                                suggestions.append(reasoning)
                except Exception as e:
                    logger.debug(f"Error checking experience_details: {e}")
            
            # 9. From actionable_feedback
            if 'actionable_feedback' in response:
                try:
                    actionable_feedback = response.get('actionable_feedback', [])
                    if isinstance(actionable_feedback, list):
                        for feedback_item in actionable_feedback:
                            try:
                                if isinstance(feedback_item, dict):
                                    feedback_text = feedback_item.get('feedback', '')
                                    suggested_action = feedback_item.get('suggested_action', '')
                                    
                                    if feedback_text and isinstance(feedback_text, str) and feedback_text.strip():
                                        suggestions.append(feedback_text)
                                    
                                    if suggested_action and isinstance(suggested_action, str) and suggested_action.strip():
                                        suggestions.append(suggested_action)
                                elif isinstance(feedback_item, str):
                                    suggestions.append(feedback_item)
                            except Exception as e:
                                logger.debug(f"Error processing actionable_feedback item: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error checking actionable_feedback: {e}")
            
            # 10. From actionable_recommendations
            if 'actionable_recommendations' in response:
                try:
                    recommendations = response.get('actionable_recommendations', [])
                    if isinstance(recommendations, list):
                        for rec in recommendations:
                            try:
                                if isinstance(rec, dict):
                                    desc = rec.get('description', '')
                                    if desc and isinstance(desc, str) and desc.strip():
                                        suggestions.append(desc)
                                elif isinstance(rec, str):
                                    suggestions.append(rec)
                            except Exception as e:
                                logger.debug(f"Error processing recommendation: {e}")
                                continue
                except Exception as e:
                    logger.debug(f"Error checking actionable_recommendations: {e}")
            
            # 11. From feedback.actionable_recommendations (nested)
            if 'feedback' in response:
                try:
                    feedback = response.get('feedback', {})
                    
                    # Handle feedback as a list (new format: [{'section': '...', 'actionable_recommendations': [...]}])
                    if isinstance(feedback, list):
                        for feedback_item in feedback:
                            try:
                                if isinstance(feedback_item, dict):
                                    # Extract actionable_recommendations from each item
                                    recommendations = feedback_item.get('actionable_recommendations', [])
                                    if isinstance(recommendations, list):
                                        for rec in recommendations:
                                            try:
                                                if isinstance(rec, str):
                                                    suggestions.append(rec)
                                                elif isinstance(rec, dict):
                                                    desc = rec.get('description', '')
                                                    if desc and isinstance(desc, str) and desc.strip():
                                                        suggestions.append(desc)
                                            except Exception as e:
                                                logger.debug(f"Error processing recommendation from list item: {e}")
                                                continue
                            except Exception as e:
                                logger.debug(f"Error processing feedback list item: {e}")
                                continue
                    
                    # Handle feedback as a dict (original format)
                    elif isinstance(feedback, dict):
                        if 'actionable_recommendations' in feedback:
                            recommendations = feedback.get('actionable_recommendations', [])
                            if isinstance(recommendations, list):
                                for rec in recommendations:
                                    try:
                                        if isinstance(rec, dict):
                                            desc = rec.get('description', '')
                                            if desc and isinstance(desc, str) and desc.strip():
                                                suggestions.append(desc)
                                        elif isinstance(rec, str):
                                            suggestions.append(rec)
                                    except Exception as e:
                                        logger.debug(f"Error processing nested recommendation: {e}")
                                        continue
                        
                        for key in ['experience_relevance', 'alignment_with_job_requirements', 'overall_fit']:
                            if key in feedback:
                                try:
                                    nested_obj = feedback.get(key, {})
                                    if isinstance(nested_obj, dict) and 'actionable_recommendations' in nested_obj:
                                        recommendations = nested_obj.get('actionable_recommendations', [])
                                        if isinstance(recommendations, list):
                                            for rec in recommendations:
                                                try:
                                                    if isinstance(rec, dict):
                                                        desc = rec.get('description', '')
                                                        if desc and isinstance(desc, str) and desc.strip():
                                                            suggestions.append(desc)
                                                    elif isinstance(rec, str):
                                                        suggestions.append(rec)
                                                except Exception as e:
                                                    logger.debug(f"Error processing nested recommendation in {key}: {e}")
                                                    continue
                                    
                                    description = nested_obj.get('description', '')
                                    if description and isinstance(description, str) and description.strip():
                                        improvement_keywords = ['unclear', 'could be', 'but', 'however', 'some', 'could', 'should', 'need', 'missing']
                                        if any(keyword in description.lower() for keyword in improvement_keywords):
                                            suggestions.append(description)
                                except Exception as e:
                                    logger.debug(f"Error checking {key}: {e}")
                                    continue
                except Exception as e:
                    logger.debug(f"Error checking nested feedback: {e}")
            
            # Deduplicate
            result = list(dict.fromkeys([s.strip() for s in suggestions if s and s.strip()]))
            logger.debug(f"Extracted {len(result)} suggestions")
            return result
            
        except Exception as e:
            logger.error(f"Error in _extract_suggestions: {e}", exc_info=True)
            return []
    
    @staticmethod
    def _parse_json_string(value: Any) -> Any:
        """Parse JSON-encoded strings (e.g., '["Python", "JavaScript"]' -> ['Python', 'JavaScript'])"""
        try:
            if isinstance(value, str):
                value = value.strip()
                if (value.startswith('[') and value.endswith(']')) or \
                   (value.startswith('{') and value.endswith('}')):
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.debug(f"Failed to parse JSON string: {e}")
                        return value
            return value
        except Exception as e:
            logger.debug(f"Error in _parse_json_string: {e}")
            return value
    
    @staticmethod
    def _normalize_skills_list(skills_list: Any) -> List[str]:
         """Normalize skills list from various formats to simple list of strings"""
         try:
             if not skills_list:
                 return []
             
             normalized = []
             
             if isinstance(skills_list, str):
                 return [skills_list.strip()] if skills_list.strip() else []
             
             if not isinstance(skills_list, (list, tuple)):
                 return [str(skills_list).strip()] if skills_list else []
             
             for item in skills_list:
                 try:
                     # Handle nested lists (e.g., [['Python'], ['JavaScript']])
                     if isinstance(item, (list, tuple)):
                         # Recursively normalize nested lists
                         nested_skills = CompatibilityAnalysisNormalizer._normalize_skills_list(item)
                         normalized.extend(nested_skills)
                         continue
                     
                     if isinstance(item, dict):
                         if 'description' in item:
                             desc = item['description']
                             if isinstance(desc, list):
                                 normalized.extend([str(s) for s in desc if s])
                             else:
                                 normalized.append(str(desc))
                         elif 'area' in item:
                             normalized.append(str(item['area']))
                         elif 'name' in item:
                             normalized.append(str(item['name']))
                         elif 'skill' in item:
                             normalized.append(str(item['skill']))
                         else:
                             for key, value in item.items():
                                 if isinstance(value, str) and value:
                                     normalized.append(value)
                                 elif isinstance(value, list):
                                     normalized.extend([str(v) for v in value if isinstance(v, str)])
                     elif isinstance(item, str):
                         normalized.append(item)
                     else:
                         normalized.append(str(item))
                 except Exception as e:
                     logger.debug(f"Error processing skill item: {e}")
                     continue
             
             # Remove duplicates and empty strings, preserve order
             result = list(dict.fromkeys([s.strip() for s in normalized if s and s.strip()]))
             return result
             
         except Exception as e:
             logger.error(f"Error in _normalize_skills_list: {e}", exc_info=True)
             return []
