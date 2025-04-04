from typing import Dict, List, Any, Optional, Tuple
import re
import json

# NLP libraries
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except ImportError:
    # Fallback if spacy model is not installed
    nlp = None

class NLPProcessor:
    """Service for processing text with NLP techniques"""
    
    @staticmethod
    def extract_key_information(text: str) -> Dict[str, Any]:
        """Extract key information from text using NLP techniques"""
        if not text or not nlp:
            return {
                "keywords": [],
                "entities": {},
                "summary": ""
            }
        
        # Process text with spaCy
        doc = nlp(text)
        
        # Extract keywords (most common non-stop words)
        keywords = [token.text for token in doc if not token.is_stop and token.is_alpha]
        keyword_freq = {}
        for word in keywords:
            if word.lower() in keyword_freq:
                keyword_freq[word.lower()] += 1
            else:
                keyword_freq[word.lower()] = 1
        
        # Sort by frequency and get top 10
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Extract named entities
        entities = {}
        for ent in doc.ents:
            if ent.label_ not in entities:
                entities[ent.label_] = []
            entities[ent.label_].append(ent.text)
            
        # Generate a basic summary (first sentence and most important sentences based on keyword density)
        sentences = [sent.text.strip() for sent in doc.sents]
        summary = sentences[0] if sentences else ""
        
        # Calculate sentence importance based on keyword overlap
        if len(sentences) > 1:
            sentence_scores = []
            for sentence in sentences[1:]:  # Skip first sentence as it's already included
                score = sum(1 for word in nlp(sentence) if not word.is_stop and word.text.lower() in dict(top_keywords))
                sentence_scores.append((sentence, score))
            
            # Include up to 2 more important sentences
            top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)[:2]
            for sentence, _ in top_sentences:
                if sentence != summary:
                    summary += " " + sentence
        
        return {
            "keywords": [k for k, _ in top_keywords],
            "entities": entities,
            "summary": summary
        }
    
    @staticmethod
    def identify_requirements(text: str) -> Dict[str, Any]:
        """Identify assignment requirements from text"""
        if not text or not nlp:
            return {
                "due_date": None,
                "word_count": None,
                "format_requirements": [],
                "grading_criteria": []
            }
        
        # Process text with spaCy
        doc = nlp(text)
        
        # Look for due dates
        due_date_pattern = r"due\s+(?:on|by|before)?\s*(?:\w+day,?\s*)?((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s*\d{4})?)|(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
        due_date_matches = re.findall(due_date_pattern, text.lower())
        due_date = None
        if due_date_matches:
            due_date = ' '.join([x for x in due_date_matches[0] if x]).strip()
        
        # Look for word count requirements
        word_count_pattern = r"(\d+)(?:\s*-\s*\d+)?\s*words"
        word_count_matches = re.findall(word_count_pattern, text.lower())
        word_count = None
        if word_count_matches:
            word_count = word_count_matches[0]
        
        # Look for formatting requirements
        format_patterns = [
            r"([^.]*APA[^.]*\.)",
            r"([^.]*MLA[^.]*\.)",
            r"([^.]*Chicago[^.]*\.)",
            r"([^.]*double[- ]spaced[^.]*\.)",
            r"([^.]*font[^.]*\.)",
            r"([^.]*margin[^.]*\.)"
        ]
        
        format_requirements = []
        for pattern in format_patterns:
            matches = re.findall(pattern, text)
            format_requirements.extend(matches)
        
        # Look for grading criteria
        criteria_patterns = [
            r"grading criteria:([^.]+)",
            r"will be graded on:([^.]+)",
            r"(?:graded|evaluated) based on:([^.]+)",
            r"rubric:([^.]+)"
        ]
        
        grading_criteria = []
        for pattern in criteria_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            grading_criteria.extend([match.strip() for match in matches])
        
        return {
            "due_date": due_date,
            "word_count": word_count,
            "format_requirements": format_requirements,
            "grading_criteria": grading_criteria
        }
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        normalized = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        normalized = re.sub(r'[^\w\s.,;:!?()\'"-]', '', normalized)
        
        # Trim extra whitespace
        normalized = normalized.strip()
        
        return normalized
    
    @staticmethod
    def process_assignment_content(assignment_text: str, materials_text: List[str]) -> Dict[str, Any]:
        """Process assignment text and associated materials to build context"""
        assignment_info = NLPProcessor.extract_key_information(assignment_text)
        requirements = NLPProcessor.identify_requirements(assignment_text)
        
        # Process each material
        materials_analysis = []
        for i, material_text in enumerate(materials_text):
            material_info = NLPProcessor.extract_key_information(material_text)
            materials_analysis.append({
                "material_index": i,
                "analysis": material_info
            })
        
        # Combine all text for overall analysis
        all_text = assignment_text + " " + " ".join(materials_text)
        overall_analysis = NLPProcessor.extract_key_information(all_text)
        
        return {
            "assignment_analysis": assignment_info,
            "requirements": requirements,
            "materials_analysis": materials_analysis,
            "overall_analysis": overall_analysis
        }