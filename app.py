"""
AI-Based Project Planner - Main Streamlit Application
A simple tool to generate project plans from documents using AI
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# Import our custom modules
from utils import extract_document_text, clean_text, validate_project_data
from document_analyzer import DocumentAnalyzer
from project_planner import ProjectPlanner

# Page configuration
st.set_page_config(
    page_title="AI Project Planner",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'project_plan' not in st.session_state:
    st.session_state.project_plan = None
if 'project_info' not in st.session_state:
    st.session_state.project_info = None
if 'analyzer' not in st.session_state:
    st.session_state.analyzer = None
if 'planner' not in st.session_state:
    st.session_state.planner = None

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize AI components"""
    analyzer = DocumentAnalyzer()
    planner = ProjectPlanner()
    return analyzer, planner

def main():
    """Main application function"""
    # Header
    st.title("🤖 AI-Based Project Planner")
    st.markdown("Upload your project document and let AI generate a comprehensive project plan!")
    
    # Initialize components
    if st.session_state.analyzer is None or st.session_state.planner is None:
        with st.spinner("Initializing AI models..."):
            st.session_state.analyzer, st.session_state.planner = initialize_components()
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("📝 Project Setup")
        
        # Project name input
        project_name = st.text_input(
            "Project Name",
            placeholder="Enter your project name...",
            help="Give your project a descriptive name"
        )
        
        # Project start date
        start_date = st.date_input(
            "Project Start Date",
            value=date.today(),
            help="When do you want the project to start?"
        )
        
        # File upload
        st.subheader("📄 Upload Document")
        uploaded_file = st.file_uploader(
            "Choose a project document",
            type=['pdf', 'docx', 'txt'],
            help="Upload a PDF, DOCX, or TXT file containing project details"
        )
        
        # Generate button
        generate_button = st.button(
            "🚀 Generate Project Plan",
            type="primary",
            disabled=not (project_name and uploaded_file),
            help="Click to analyze document and generate project plan"
        )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if generate_button and project_name and uploaded_file:
            generate_project_plan(project_name, uploaded_file, start_date)
        
        # Display project plan
        display_project_plan()
    
    with col2:
        # Display project information
        display_project_info()
        
        # Display project statistics
        display_project_stats()

def generate_project_plan(project_name, uploaded_file, start_date):
    """Generate project plan from uploaded document"""
    try:
        # Extract text from document
        with st.spinner("📖 Extracting text from document..."):
            document_text = extract_document_text(uploaded_file)
            
        if not document_text.strip():
            st.error("Could not extract text from the document. Please check the file format.")
            return
        
        # Clean text
        cleaned_text = clean_text(document_text)
        st.success(f"✅ Extracted {len(cleaned_text.split())} words from document")
        
        # Analyze document
        with st.spinner("🧠 Analyzing document with AI..."):
            project_info = st.session_state.analyzer.extract_project_info(cleaned_text, project_name)
            
        if not project_info:
            st.error("Could not analyze the document. Please try a different file.")
            return
        
        st.session_state.project_info = project_info
        st.success(f"✅ Found {len(project_info['tasks'])} potential tasks")
        
        # Generate project plan
        with st.spinner("📋 Generating project plan..."):
            project_plan = st.session_state.planner.generate_project_plan(project_info)
            
        if project_plan is not None and not project_plan.empty:
            # Update dates based on user's start date
            project_plan = st.session_state.planner.update_plan_dates(project_plan, start_date)
            st.session_state.project_plan = project_plan
            st.success("✅ Project plan generated successfully!")
        else:
            st.error("Could not generate project plan. Please try again.")
            
    except Exception as e:
        st.error(f"Error generating project plan: {str(e)}")

def display_project_plan():
    """Display the generated project plan"""
    if st.session_state.project_plan is not None:
        st.header("📊 Generated Project Plan")
        
        # Display editable dataframe
        edited_df = st.data_editor(
            st.session_state.project_plan,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "ID": st.column_config.NumberColumn("ID", width="small"),
                "Name": st.column_config.TextColumn("Task Name", width="medium"),
                "Active": st.column_config.SelectboxColumn("Active", options=["Yes", "No"], width="small"),
                "Task Mode": st.column_config.SelectboxColumn("Mode", options=["Auto Scheduled", "Manually Scheduled"]),
                "Duration": st.column_config.TextColumn("Duration", width="small"),
                "Start": st.column_config.TextColumn("Start Date", width="small"),
                "Finish": st.column_config.TextColumn("Finish Date", width="small"),
                "Predecessors": st.column_config.TextColumn("Predecessors", width="small"),
                "Outline Level": st.column_config.NumberColumn("Level", width="small"),
                "Notes": st.column_config.TextColumn("Notes", width="large")
            },
            key="project_plan_editor"
        )
        
        # Update session state with edited data
        st.session_state.project_plan = edited_df
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Save as CSV"):
                save_project_plan_csv(edited_df)
        
        with col2:
            if st.button("📈 Show Timeline"):
                display_project_timeline(edited_df)
        
        with col3:
            if st.button("🔄 Regenerate"):
                if st.session_state.project_info:
                    with st.spinner("Regenerating project plan..."):
                        new_plan = st.session_state.planner.generate_project_plan(st.session_state.project_info)
                        st.session_state.project_plan = new_plan
                        st.rerun()
        
        with col4:
            if st.button("🗑️ Clear Plan"):
                st.session_state.project_plan = None
                st.session_state.project_info = None
                st.rerun()
    
    else:
        # Instructions when no plan is generated
        st.header("📋 Project Plan")
        st.info("""
        👆 **Get Started:**
        1. Enter your project name in the sidebar
        2. Upload a project document (PDF, DOCX, or TXT)
        3. Click "Generate Project Plan"
        
        The AI will analyze your document and create a structured project plan with tasks, timelines, and dependencies.
        """)

def display_project_info():
    """Display extracted project information"""
    if st.session_state.project_info:
        st.subheader("📋 Project Information")
        
        project_info = st.session_state.project_info
        
        # Project description
        with st.expander("📝 Project Description", expanded=True):
            st.write(project_info.get('description', 'No description available'))
        
        # Detected phases
        phases = project_info.get('phases', [])
        if phases:
            with st.expander("🎯 Detected Phases"):
                for i, phase in enumerate(phases, 1):
                    st.write(f"{i}. {phase}")
        
        # Timeline information
        timeline = project_info.get('timeline', {})
        if timeline:
            with st.expander("⏰ Timeline Information"):
                if 'mentioned_dates' in timeline:
                    st.write("**Mentioned Dates:**")
                    for date_str in timeline['mentioned_dates']:
                        st.write(f"• {date_str}")
                
                if 'durations' in timeline:
                    st.write("**Duration Mentions:**")
                    for duration in timeline['durations']:
                        st.write(f"• {duration[0]} {duration[1]}(s)")

def display_project_stats():
    """Display project statistics"""
    if st.session_state.project_plan is not None and not st.session_state.project_plan.empty:
        st.subheader("📊 Project Statistics")
        
        df = st.session_state.project_plan
        
        # Calculate stats
        total_tasks = len(df) - 1  # Exclude summary row
        active_tasks = len(df[df['Active'] == 'Yes']) - 1
        
        # Duration calculation
        durations = []
        for duration_str in df['Duration']:
            if 'days' in str(duration_str):
                try:
                    days = int(duration_str.split()[0])
                    durations.append(days)
                except:
                    pass
        
        total_duration = sum(durations) if durations else 0
        avg_duration = round(total_duration / len(durations), 1) if durations else 0
        
        # Display metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Tasks", total_tasks)
            st.metric("Active Tasks", active_tasks)
        
        with col2:
            st.metric("Total Duration", f"{total_duration} days")
            st.metric("Avg Task Duration", f"{avg_duration} days")
        
        # Outline level distribution
        if 'Outline Level' in df.columns:
            level_counts = df['Outline Level'].value_counts().sort_index()
            
            st.write("**Task Levels:**")
            for level, count in level_counts.items():
                if level > 0:  # Skip summary row
                    st.write(f"Level {level}: {count} tasks")

def display_project_timeline(df):
    """Display project timeline visualization"""
    st.subheader("📈 Project Timeline")
    
    try:
        # Prepare data for timeline
        timeline_data = []
        
        for _, row in df.iterrows():
            if row['ID'] == 0:  # Skip summary row for timeline
                continue
                
            try:
                start_date = datetime.strptime(row['Start'], '%a %m/%d/%y')
                finish_date = datetime.strptime(row['Finish'], '%a %m/%d/%y')
                
                timeline_data.append({
                    'Task': row['Name'],
                    'Start': start_date,
                    'Finish': finish_date,
                    'Duration': (finish_date - start_date).days,
                    'Level': row.get('Outline Level', 1)
                })
            except:
                continue
        
        if timeline_data:
            # Create Gantt chart
            fig = px.timeline(
                timeline_data,
                x_start="Start",
                x_end="Finish",
                y="Task",
                color="Level",
                title="Project Timeline (Gantt Chart)",
                height=max(400, len(timeline_data) * 30)
            )
            
            fig.update_yaxes(autorange="reversed")  # Tasks from top to bottom
            fig.update_layout(xaxis_title="Date", yaxis_title="Tasks")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Duration distribution
            durations = [item['Duration'] for item in timeline_data]
            if durations:
                fig2 = px.histogram(
                    x=durations,
                    nbins=10,
                    title="Task Duration Distribution",
                    labels={'x': 'Duration (days)', 'y': 'Number of Tasks'}
                )
                st.plotly_chart(fig2, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating timeline: {str(e)}")

def save_project_plan_csv(df):
    """Save project plan as CSV"""
    try:
        # Convert dataframe to CSV
        csv_buffer = BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_plan_{timestamp}.csv"
        
        # Download button
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            help="Download the project plan as a CSV file"
        )
        
        st.success("✅ Project plan ready for download!")
        
    except Exception as e:
        st.error(f"Error creating CSV: {str(e)}")

def display_help():
    """Display help information"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("❓ Help & Tips")
    
    with st.sidebar.expander("📖 How to Use"):
        st.markdown("""
        **Step 1:** Enter a descriptive project name
        
        **Step 2:** Upload your project document:
        - PDF files with project details
        - Word documents (.docx)
        - Plain text files (.txt)
        
        **Step 3:** Click "Generate Project Plan"
        
        **Step 4:** Review and edit the generated plan
        
        **Step 5:** Save or export your plan
        """)
    
    with st.sidebar.expander("💡 Tips for Better Results"):
        st.markdown("""
        - Include clear task descriptions in your document
        - Mention timelines and deadlines
        - Use action words (implement, develop, test, etc.)
        - Structure your document with clear sections
        - Include project phases or milestones
        """)
    
    with st.sidebar.expander("🔧 Supported File Types"):
        st.markdown("""
        - **PDF:** Text-based PDFs work best
        - **DOCX:** Microsoft Word documents
        - **TXT:** Plain text files
        
        Note: Scanned PDFs may not work well
        """)

# Run the app
if __name__ == "__main__":
    # Display help in sidebar
    display_help()
    
    # Run main app
    main()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🤖 **AI Project Planner** | Built with Streamlit and Hugging Face Transformers | "
        "Upload your documents and let AI create structured project plans!"
    )
