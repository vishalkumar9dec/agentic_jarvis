"""
Oxygen Agent Service - Self-contained A2A service

Port: 8082
Agent Card: http://localhost:8082/.well-known/agent-card.json

This is a complete, self-contained agent service that includes:
- Agent definition (LlmAgent)
- Tools/business logic (learning & development)
- Data layer (in-memory database)
- A2A server exposure
"""

import os
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from datetime import datetime, timedelta
from typing import Dict, List

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# In-memory learning database
LEARNING_DATA = {
    "vishal": {
        "courses_enrolled": ["Python Advanced", "Cloud Architecture", "Machine Learning"],
        "completed_courses": ["Python Basics"],
        "pending_exams": [
            {"exam": "Python Advanced Final", "deadline": "2025-01-15"},
            {"exam": "Cloud Architecture Cert", "deadline": "2025-01-20"}
        ],
        "preferences": ["programming", "cloud", "ai"]
    },
    "happy": {
        "courses_enrolled": ["Data Science", "SQL Mastery"],
        "completed_courses": ["Excel Basics", "Statistics 101"],
        "pending_exams": [
            {"exam": "Data Science Midterm", "deadline": "2025-01-12"}
        ],
        "preferences": ["data", "analytics", "visualization"]
    },
    "alex": {
        "courses_enrolled": ["DevOps Fundamentals", "Kubernetes"],
        "completed_courses": [],
        "pending_exams": [
            {"exam": "DevOps Quiz", "deadline": "2025-01-18"}
        ],
        "preferences": ["devops", "automation", "infrastructure"]
    }
}

# =============================================================================
# Tool Functions (Business Logic)
# =============================================================================

def get_user_courses(username: str) -> Dict:
    """Get courses for a specific user.

    Args:
        username: The username to get courses for

    Returns:
        User's enrolled and completed courses
    """
    if username not in LEARNING_DATA:
        return {"error": f"User '{username}' not found. Available users: vishal, happy, alex"}

    data = LEARNING_DATA[username]
    return {
        "username": username,
        "enrolled": data["courses_enrolled"],
        "completed": data["completed_courses"],
        "total_enrolled": len(data["courses_enrolled"]),
        "total_completed": len(data["completed_courses"])
    }


def get_pending_exams(username: str) -> Dict:
    """Get pending exams with deadlines for a user.

    Args:
        username: The username to get exams for

    Returns:
        List of pending exams with deadlines and urgency flags
    """
    if username not in LEARNING_DATA:
        return {"error": f"User '{username}' not found. Available users: vishal, happy, alex"}

    exams = LEARNING_DATA[username]["pending_exams"].copy()

    # Add days remaining and urgency flag
    for exam in exams:
        deadline = datetime.fromisoformat(exam["deadline"])
        days_remaining = (deadline - datetime.now()).days
        exam["days_remaining"] = days_remaining
        exam["urgent"] = days_remaining <= 7

    # Sort by deadline (most urgent first)
    exams.sort(key=lambda x: x["days_remaining"])

    return {
        "username": username,
        "pending_exams": exams,
        "total_pending": len(exams),
        "urgent_count": sum(1 for e in exams if e["urgent"])
    }


def get_user_preferences(username: str) -> Dict:
    """Get learning preferences for a user.

    Args:
        username: The username to get preferences for

    Returns:
        User's learning preferences
    """
    if username not in LEARNING_DATA:
        return {"error": f"User '{username}' not found. Available users: vishal, happy, alex"}

    return {
        "username": username,
        "preferences": LEARNING_DATA[username]["preferences"]
    }


def get_learning_summary(username: str) -> Dict:
    """Get complete learning summary for a user.

    Args:
        username: The username to get summary for

    Returns:
        Complete learning journey with stats
    """
    if username not in LEARNING_DATA:
        return {"error": f"User '{username}' not found. Available users: vishal, happy, alex"}

    data = LEARNING_DATA[username]
    total_courses = len(data["courses_enrolled"]) + len(data["completed_courses"])
    completion_rate = (len(data["completed_courses"]) / total_courses * 100) if total_courses > 0 else 0

    # Get exam info
    exams = data["pending_exams"].copy()
    for exam in exams:
        deadline = datetime.fromisoformat(exam["deadline"])
        days_remaining = (deadline - datetime.now()).days
        exam["days_remaining"] = days_remaining
        exam["urgent"] = days_remaining <= 7

    return {
        "username": username,
        "courses": {
            "enrolled": data["courses_enrolled"],
            "completed": data["completed_courses"]
        },
        "exams": {
            "pending": exams,
            "total_pending": len(exams),
            "urgent_count": sum(1 for e in exams if e["urgent"])
        },
        "preferences": data["preferences"],
        "stats": {
            "total_courses": total_courses,
            "completion_rate": round(completion_rate, 2),
            "status": "On Track" if completion_rate >= 50 else "Needs Attention"
        }
    }


# =============================================================================
# Agent Setup
# =============================================================================

# Create agent with tools
oxygen_agent = LlmAgent(
    name="OxygenAgent",
    model="gemini-2.5-flash",
    description="Learning and development platform agent",
    instruction="""You are Oxygen, a learning and development assistant. Your role is to:

**Course Management:**
- Help users track their enrolled courses and completed courses
- Provide information about active learning paths
- Show course progress and completion rates

**Exam Tracking:**
- Remind users about pending exams and deadlines
- Highlight urgent exams (within 7 days)
- Provide deadline information clearly with days remaining

**Learning Preferences:**
- Track user learning preferences and interests
- Help align courses with user preferences
- Provide personalized learning recommendations

**Progress Monitoring:**
- Calculate and explain completion rates
- Track overall learning progress
- Identify users who need attention vs those on track

**Available Tools:**
- get_user_courses: Get courses for a specific user (by username)
- get_pending_exams: Get pending exams with deadlines (by username)
- get_user_preferences: Get learning preferences (by username)
- get_learning_summary: Complete learning journey (by username)

**Communication Style:**
Always be encouraging and supportive in your responses:
- Celebrate achievements and completed courses
- Provide gentle reminders about upcoming deadlines
- Offer motivation for users who need attention
- Be clear and specific about dates and deadlines

**When showing exam deadlines:**
- Clearly state the date
- Mention days remaining
- Flag urgent exams prominently (≤7 days)
- Sort by urgency (most urgent first)

**When discussing progress:**
- Use percentages for completion rates
- Explain what "On Track" (≥50%) or "Needs Attention" (<50%) means
- Highlight achievements (completed courses)
- Encourage continued learning

**Available Users:** vishal, happy, alex

**Example Queries:**
- "Show courses for vishal"
- "What exams does alex have pending?"
- "Show learning summary for happy"
- "What are vishal's learning preferences?"
""",
    tools=[get_user_courses, get_pending_exams, get_user_preferences, get_learning_summary]
)

# =============================================================================
# A2A Server
# =============================================================================

# Expose agent via A2A protocol (at module level for uvicorn)
a2a_app = to_a2a(
    oxygen_agent,
    port=8082,
    host="0.0.0.0"
)

if __name__ == "__main__":
    print("=" * 80)
    print("✅ Oxygen Agent Service Started")
    print("=" * 80)
    print(f"Port:        8082")
    print(f"Agent Card:  http://localhost:8082/.well-known/agent-card.json")
    print(f"Health:      http://localhost:8082/health")
    print(f"Invoke:      http://localhost:8082/invoke")
    print("=" * 80)
    print("")
    print("Service is ready to handle requests via A2A protocol")
    print("Press Ctrl+C to stop")
    print("")
