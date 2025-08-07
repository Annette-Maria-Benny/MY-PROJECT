"""
Project planner that generates structured project plans from analyzed document data
"""
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class ProjectPlanner:
    def __init__(self):
        self.task_modes = ['Auto Scheduled', 'Manually Scheduled']
        self.default_start_date = datetime.now().date()
    
    def generate_project_plan(self, project_info):
        """Generate a structured project plan from analyzed project information"""
        try:
            tasks = project_info.get('tasks', [])
            project_name = project_info.get('name', 'Untitled Project')
            
            # Create project plan data
            plan_data = []
            current_date = self.default_start_date
            
            for i, task in enumerate(tasks):
                # Calculate task details
                task_id = i + 1
                duration = task.get('estimated_duration', 5)
                start_date = current_date
                finish_date = start_date + timedelta(days=duration)
                
                # Determine predecessors (simple dependency logic)
                predecessors = self._calculate_predecessors(task_id, i, tasks)
                
                # Determine outline level
                outline_level = self._determine_outline_level(task['name'])
                
                # Create task row
                task_row = {
                    'ID': task_id,
                    'Name': task['name'],
                    'Active': 'Yes',
                    'Task Mode': 'Auto Scheduled',
                    'Duration': f"{duration} days",
                    'Start': start_date.strftime('%a %m/%d/%y'),
                    'Finish': finish_date.strftime('%a %m/%d/%y'),
                    'Predecessors': predecessors,
                    'Outline Level': outline_level,
                    'Notes': self._generate_task_notes(task)
                }
                
                plan_data.append(task_row)
                
                # Update current date for next task (with some overlap)
                current_date = start_date + timedelta(days=max(1, duration // 2))
            
            # Convert to DataFrame
            df = pd.DataFrame(plan_data)
            
            # Add summary row at the beginning
            summary_row = self._create_summary_row(project_name, df)
            df = pd.concat([summary_row, df], ignore_index=True)
            df['ID'] = range(1, len(df) + 1)
            
            return df
            
        except Exception as e:
            st.error(f"Error generating project plan: {str(e)}")
            return self._create_default_plan()
    
    def _calculate_predecessors(self, task_id, task_index, tasks):
        """Calculate task predecessors based on simple dependency logic"""
        if task_index == 0:
            return ""  # First task has no predecessors
        
        # Simple logic: some tasks depend on previous task
        dependency_chance = 0.6  # 60% chance of dependency
        
        if task_index > 0 and hash(tasks[task_index]['name']) % 10 < 6:
            return str(task_id - 1)
        
        return ""
    
    def _determine_outline_level(self, task_name):
        """Determine outline level based on task name"""
        task_lower = task_name.lower()
        
        # Level 1: Main phases
        if any(word in task_lower for word in ['phase', 'stage', 'planning', 'design', 'development', 'testing', 'deployment']):
            return 1
        
        # Level 2: Sub-tasks
        if any(word in task_lower for word in ['setup', 'configure', 'create', 'implement']):
            return 2
        
        # Level 3: Detailed tasks
        if any(word in task_lower for word in ['review', 'validate', 'test', 'document']):
            return 3
        
        return 2  # Default level
    
    def _generate_task_notes(self, task):
        """Generate notes for a task"""
        priority = task.get('priority', 'Medium')
        description = task.get('description', '')
        
        # Truncate description if too long
        if len(description) > 100:
            description = description[:97] + "..."
        
        notes = f"Priority: {priority}. {description}"
        return notes
    
    def _create_summary_row(self, project_name, df):
        """Create a summary row for the entire project"""
        if df.empty:
            return pd.DataFrame()
        
        # Calculate project totals
        total_duration = sum([int(d.split()[0]) for d in df['Duration'] if 'days' in d])
        start_dates = [datetime.strptime(d, '%a %m/%d/%y') for d in df['Start']]
        finish_dates = [datetime.strptime(d, '%a %m/%d/%y') for d in df['Finish']]
        
        project_start = min(start_dates).strftime('%a %m/%d/%y')
        project_finish = max(finish_dates).strftime('%a %m/%d/%y')
        
        summary_data = {
            'ID': [0],
            'Name': [project_name],
            'Active': ['Yes'],
            'Task Mode': ['Auto Scheduled'],
            'Duration': [f"{total_duration} days"],
            'Start': [project_start],
            'Finish': [project_finish],
            'Predecessors': [''],
            'Outline Level': [0],
            'Notes': ['This roadmap is intended to guide the project execution.']
        }
        
        return pd.DataFrame(summary_data)
    
    def _create_default_plan(self):
        """Create a default project plan if generation fails"""
        default_data = [
            {
                'ID': 1,
                'Name': 'Sample Project',
                'Active': 'Yes',
                'Task Mode': 'Auto Scheduled',
                'Duration': '30 days',
                'Start': self.default_start_date.strftime('%a %m/%d/%y'),
                'Finish': (self.default_start_date + timedelta(days=30)).strftime('%a %m/%d/%y'),
                'Predecessors': '',
                'Outline Level': 1,
                'Notes': 'Default project plan generated'
            },
            {
                'ID': 2,
                'Name': 'Planning Phase',
                'Active': 'Yes',
                'Task Mode': 'Auto Scheduled',
                'Duration': '5 days',
                'Start': self.default_start_date.strftime('%a %m/%d/%y'),
                'Finish': (self.default_start_date + timedelta(days=5)).strftime('%a %m/%d/%y'),
                'Predecessors': '',
                'Outline Level': 2,
                'Notes': 'Project planning and requirements gathering'
            }
        ]
        
        return pd.DataFrame(default_data)
    
    def update_plan_dates(self, df, new_start_date):
        """Update all dates in the plan based on a new start date"""
        try:
            if df.empty:
                return df
            
            # Calculate the difference from current start
            current_start = datetime.strptime(df.iloc[0]['Start'], '%a %m/%d/%y').date()
            date_diff = new_start_date - current_start
            
            # Update all dates
            for index, row in df.iterrows():
                old_start = datetime.strptime(row['Start'], '%a %m/%d/%y').date()
                old_finish = datetime.strptime(row['Finish'], '%a %m/%d/%y').date()
                
                new_start = old_start + date_diff
                new_finish = old_finish + date_diff
                
                df.at[index, 'Start'] = new_start.strftime('%a %m/%d/%y')
                df.at[index, 'Finish'] = new_finish.strftime('%a %m/%d/%y')
            
            return df
        except Exception as e:
            st.error(f"Error updating dates: {str(e)}")
            return df
    
    def validate_plan(self, df):
        """Validate the generated project plan"""
        issues = []
        
        if df.empty:
            issues.append("Project plan is empty")
            return issues
        
        # Check required columns
        required_cols = ['ID', 'Name', 'Duration', 'Start', 'Finish']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing columns: {missing_cols}")
        
        # Check for empty task names
        if df['Name'].isna().any():
            issues.append("Some tasks have empty names")
        
        # Check date formats
        try:
            for date_col in ['Start', 'Finish']:
                if date_col in df.columns:
                    df[date_col].apply(lambda x: datetime.strptime(x, '%a %m/%d/%y'))
        except ValueError:
            issues.append("Invalid date format detected")
        
        return issues