import os
import sys
import json
import csv
from datetime import datetime, timedelta

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google import genai
from LLM_APIS import GEMINI_API_KEY
from Googlecalender import authenticate, schedule_meeting


def generate_task_plan(query):
    """
    Uses Gemini LLM to break down a query into a task plan.
    
    Args:
        query: The task or project description to break down
    
    Returns:
        List of dictionaries with 'day' and 'work' keys
    """
    prompt = f"""
You are a task planning assistant. Break down the following query into a structured task plan.

Query: {query}

Return ONLY a valid JSON array with the following structure:
[
    {{"day": "Day 1", "work": "Description of work to be completed"}},
    {{"day": "Day 2", "work": "Description of work to be completed"}},
    ...
]

Rules:
- Each task should be realistic and achievable in one day
- Be specific and actionable
- Return ONLY the JSON array, no additional text
- Use "Day 1", "Day 2", etc. format for the day column
"""
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
        )
        
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        # Parse JSON response
        task_plan = json.loads(response_text)
        
        # Validate structure
        if not isinstance(task_plan, list):
            raise ValueError("Response is not a list")
        
        for task in task_plan:
            if 'day' not in task or 'work' not in task:
                raise ValueError("Invalid task structure")
        
        return task_plan
    
    except json.JSONDecodeError as e:
        print(f" Error parsing JSON response: {e}")
        print(f"Response text: {response_text}")
        return None
    except Exception as e:
        print(f" Error generating task plan: {e}")
        return None


def save_task_plan_to_csv(task_plan, filename=None, query=None):
    """
    Saves the task plan to a CSV file in the 'personnel_schedules' folder.
    
    Args:
        task_plan: List of dictionaries with 'day' and 'work' keys
        filename: Optional custom filename (without extension)
        query: Optional query text to generate filename from
    
    Returns:
        Path to the saved CSV file
    """
    # Create personnel_schedules directory if it doesn't exist
    schedules_dir = "personnel_schedules"
    os.makedirs(schedules_dir, exist_ok=True)
    
    # Generate filename from query or timestamp if not provided
    if filename is None:
        if query:
            # Sanitize query to create a valid filename
            sanitized = "".join(c if c.isalnum() or c in (' ', '_', '-') else '' for c in query)
            sanitized = sanitized.strip().replace(' ', '_')[:50]  # Limit to 50 chars
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{sanitized}_{timestamp}"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"task_plan_{timestamp}"
    
    csv_path = os.path.join(schedules_dir, f"{filename}.csv")
    
    # Write to CSV
    try:
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['day', 'work']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for task in task_plan:
                writer.writerow({'day': task['day'], 'work': task['work']})
        
        print(f" Task plan saved to: {csv_path}")
        return csv_path
    
    except Exception as e:
        print(f" Error saving CSV: {e}")
        return None


def create_schedule_from_query(query, filename=None, add_calendar_event=True):
    """
    Main function that takes a query, generates a task plan using Gemini,
    saves it as a CSV file, and optionally creates a Google Calendar reminder.
    
    Args:
        query: The task or project description
        filename: Optional custom filename for the CSV
        add_calendar_event: Whether to add a completion reminder to Google Calendar (default: True)
    
    Returns:
        Dictionary with 'csv_path', 'total_days', and 'calendar_event_id' (if created)
    """
    print(f"📋 Processing query: {query}\n")
    
    # Generate task plan using Gemini
    print("🤖 Generating task plan with Gemini...")
    task_plan = generate_task_plan(query)
    
    if task_plan is None:
        print(" Failed to generate task plan")
        return None
    
    # Calculate total days
    total_days = len(task_plan)
    print(f" Generated {total_days} tasks\n")
    
    # Display the task plan
    print("📅 Task Plan:")
    print("-" * 60)
    for task in task_plan:
        print(f"{task['day']}: {task['work']}")
    print("-" * 60 + "\n")
    
    # Save to CSV
    csv_path = save_task_plan_to_csv(task_plan, filename, query)
    
    result = {
        'csv_path': csv_path,
        'total_days': total_days,
        'calendar_event_id': None
    }
    
    # Add Google Calendar event for completion date
    if add_calendar_event and csv_path:
        try:
            print(f"📆 Adding completion reminder to Google Calendar...")
            
            # Calculate completion date (today + total_days)
            today = datetime.now()
            completion_date = today + timedelta(days=total_days)
            completion_date_iso = completion_date.strftime("%Y-%m-%dT09:00:00")
            
            # Create calendar event
            service = authenticate()
            event_title = f"Project Completion: {query[:50]}..." if len(query) > 50 else f"Project Completion: {query}"
            event_id = schedule_meeting(service, event_title, completion_date_iso, duration_hours=1)
            
            if event_id:
                result['calendar_event_id'] = event_id
                print(f" Calendar reminder set for {completion_date.strftime('%Y-%m-%d')} ({total_days} days from now)\n")
            else:
                print(f"  Failed to create calendar event\n")
                
        except Exception as e:
            print(f"  Error creating calendar event: {e}\n")
    
    return result


# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Example usage
    example_query = "Build a 5 days schedule to practice OOPs?"
    
    result = create_schedule_from_query(
        query=example_query,
        add_calendar_event=True
    )
    
    if result and result['csv_path']:
        print(f"\n🎉 Success!")
        print(f"   📄 Schedule saved to: {result['csv_path']}")
        print(f"   📊 Total days: {result['total_days']}")
        if result['calendar_event_id']:
            print(f"   📆 Calendar event created: {result['calendar_event_id']}")
    else:
        print("\n Failed to create schedule")
