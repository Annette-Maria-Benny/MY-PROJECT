"""
Document analyzer using Hugging Face transformers for project planning
"""
import streamlit as st
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import re
import nltk
from datetime import datetime, timedelta
import random

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

class DocumentAnalyzer:
    def __init__(self):
        self.setup_models()
    
    @st.cache_resource
    def setup_models(_self):
        """Initialize AI models for text analysis"""
        try:
            # Use a lightweight model for text summarization
            _self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
            
            # For task extraction, we'll use keyword-based approach combined with NLP
            _self.task_keywords = [
                'implement', 'develop', 'create', 'build', 'design', 'test', 'deploy', 
                'configure', 'setup', 'install', 'analyze', 'review', 'prepare',
                'execute', 'complete', 'finish', 'deliver', 'validate', 'verify'
            ]
            
            _self.phase_keywords = [
                'phase', 'stage', 'milestone', 'iteration', 'sprint', 'release',
                'planning', 'analysis', 'design', 'development', 'testing', 'deployment'
            ]
            
            return True
        except Exception as e:
            st.error(f"Error loading AI models: {str(e)}")
            return False
    
    def extract_project_info(self, text, project_name):
        """Extract project information from document text"""
        try:
            # Clean the text
            text = self._clean_text(text)
            
            # Extract basic project info
            project_info = {
                'name': project_name,
                'description': self._extract_description(text),
                'tasks': self._extract_tasks(text),
                'timeline': self._extract_timeline_info(text),
                'phases': self._extract_phases(text)
            }
            
            return project_info
        except Exception as e:
            st.error(f"Error analyzing document: {str(e)}")
            return None
    
    def _clean_text(self, text):
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.,!?;:\-()]', '', text)
        return text.strip()
    
    def _extract_description(self, text):
        """Extract project description using summarization"""
        try:
            # Limit text length for summarization
            max_length = 1000
            if len(text) > max_length:
                text = text[:max_length]
            
            # Generate summary
            summary = self.summarizer(text, max_length=150, min_length=50, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            # Fallback: return first few sentences
            sentences = nltk.sent_tokenize(text)
            return ' '.join(sentences[:3]) if sentences else "Project description not available"
    
    def _extract_tasks(self, text):
        """Extract potential tasks from text"""
        tasks = []
        sentences = nltk.sent_tokenize(text)
        
        for i, sentence in enumerate(sentences):
            sentence_lower = sentence.lower()
            
            # Look for sentences containing task keywords
            for keyword in self.task_keywords:
                if keyword in sentence_lower and len(sentence.split()) > 3:
                    # Extract task name (simplified)
                    task_name = self._generate_task_name(sentence, keyword)
                    if task_name and len(task_name) < 100:
                        tasks.append({
                            'name': task_name,
                            'description': sentence[:200],
                            'priority': self._estimate_priority(sentence),
                            'estimated_duration': self._estimate_duration(sentence)
                        })
                    break
        
        # If no tasks found, generate some default ones
        if not tasks:
            tasks = self._generate_default_tasks(text)
        
        return tasks[:15]  # Limit to 15 tasks
    
    def _generate_task_name(self, sentence, keyword):
        """Generate a clean task name from sentence"""
        # Find the part of sentence around the keyword
        words = sentence.split()
        keyword_index = -1
        
        for i, word in enumerate(words):
            if keyword.lower() in word.lower():
                keyword_index = i
                break
        
        if keyword_index == -1:
            return None
        
        # Extract task name (keyword + next few words)
        start_idx = max(0, keyword_index - 1)
        end_idx = min(len(words), keyword_index + 4)
        task_words = words[start_idx:end_idx]
        
        # Clean and format
        task_name = ' '.join(task_words)
        task_name = re.sub(r'[^\w\s]', ' ', task_name)
        task_name = ' '.join(task_name.split())  # Remove extra spaces
        
        return task_name.title() if task_name else None
    
    def _estimate_priority(self, sentence):
        """Estimate task priority based on keywords"""
        high_priority_words = ['critical', 'urgent', 'important', 'key', 'essential']
        sentence_lower = sentence.lower()
        
        for word in high_priority_words:
            if word in sentence_lower:
                return 'High'
        
        return random.choice(['Medium', 'Low'])
    
    def _estimate_duration(self, sentence):
        """Estimate task duration"""
        # Look for duration patterns in text
        duration_patterns = [
            r'(\d+)\s*(day|days)',
            r'(\d+)\s*(week|weeks)',
            r'(\d+)\s*(month|months)'
        ]
        
        for pattern in duration_patterns:
            matches = re.findall(pattern, sentence.lower())
            if matches:
                num, unit = matches[0]
                days = int(num)
                if 'week' in unit:
                    days *= 7
                elif 'month' in unit:
                    days *= 30
                return min(days, 30)  # Cap at 30 days
        
        # Default duration based on task complexity
        return random.randint(1, 10)
    
    def _extract_timeline_info(self, text):
        """Extract timeline information"""
        timeline = {}
        
        # Look for date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text.lower())
            dates.extend(matches)
        
        if dates:
            timeline['mentioned_dates'] = dates[:5]  # Keep first 5 dates
        
        # Look for duration mentions
        duration_matches = re.findall(r'(\d+)\s*(day|week|month)s?', text.lower())
        if duration_matches:
            timeline['durations'] = duration_matches[:3]
        
        return timeline
    
    def _extract_phases(self, text):
        """Extract project phases"""
        phases = []
        sentences = nltk.sent_tokenize(text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for keyword in self.phase_keywords:
                if keyword in sentence_lower:
                    phase_name = self._extract_phase_name(sentence, keyword)
                    if phase_name:
                        phases.append(phase_name)
                    break
        
        # Remove duplicates and limit
        phases = list(dict.fromkeys(phases))[:5]
        return phases
    
    def _extract_phase_name(self, sentence, keyword):
        """Extract phase name from sentence"""
        # Simple extraction around the keyword
        words = sentence.split()
        for i, word in enumerate(words):
            if keyword.lower() in word.lower():
                # Get surrounding words
                start = max(0, i-2)
                end = min(len(words), i+3)
                phase_words = words[start:end]
                phase_name = ' '.join(phase_words)
                # Clean
                phase_name = re.sub(r'[^\w\s]', ' ', phase_name)
                return ' '.join(phase_name.split()).title()
        return None
    
    def _generate_default_tasks(self, text):
        """Generate default tasks if none found"""
        default_tasks = [
            {'name': 'Project Planning', 'description': 'Plan project scope and timeline', 'priority': 'High', 'estimated_duration': 3},
            {'name': 'Requirements Analysis', 'description': 'Analyze project requirements', 'priority': 'High', 'estimated_duration': 5},
            {'name': 'System Design', 'description': 'Design system architecture', 'priority': 'Medium', 'estimated_duration': 7},
            {'name': 'Development Phase 1', 'description': 'Initial development phase', 'priority': 'High', 'estimated_duration': 10},
            {'name': 'Testing', 'description': 'Test system functionality', 'priority': 'High', 'estimated_duration': 5},
            {'name': 'Deployment', 'description': 'Deploy to production', 'priority': 'Medium', 'estimated_duration': 2}
        ]
        return default_tasks