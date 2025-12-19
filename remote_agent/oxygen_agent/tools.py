"""
Oxygen Learning Tools
Provides learning and development functions for the Oxygen agent.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

# In-memory learning database
LEARNING_DB = {
    "vishal": {
        "courses_enrolled": ["aws", "terraform"],
        "pending_exams": ["snowflake"],
        "completed_courses": ["docker"],
        "preferences": ["software engineering", "cloud architecture"],
        "exam_deadlines": {"snowflake": "2025-12-28"}
    },
    "happy": {
        "courses_enrolled": ["architecture", "soft skills"],
        "pending_exams": ["aws"],
        "completed_courses": ["python basics"],
        "preferences": ["system design", "leadership"],
        "exam_deadlines": {"aws": "2026-01-15"}
    },
    "alex": {
        "courses_enrolled": ["kubernetes", "python advanced", "devops"],
        "pending_exams": ["kubernetes", "azure"],
        "completed_courses": ["git", "linux", "docker"],
        "preferences": ["DevOps", "automation", "container orchestration"],
        "exam_deadlines": {"kubernetes": "2025-12-22", "azure": "2026-01-05"}
    }
}


def get_user_courses(username: str) -> Dict[str, Any]:
    """Get all courses for a user.

    Args:
        username: The username to look up

    Returns:
        Dictionary with enrolled and completed courses, or error if user not found
    """
    username_lower = username.lower()

    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found in the learning system",
            "available_users": list(LEARNING_DB.keys())
        }

    user_data = LEARNING_DB[username_lower]

    return {
        "success": True,
        "username": username_lower,
        "courses_enrolled": user_data["courses_enrolled"],
        "completed_courses": user_data["completed_courses"],
        "total_enrolled": len(user_data["courses_enrolled"]),
        "total_completed": len(user_data["completed_courses"]),
        "in_progress": len(user_data["courses_enrolled"])
    }


def get_pending_exams(username: str) -> Dict[str, Any]:
    """Get pending exams with deadlines for a user.

    Args:
        username: The username to look up

    Returns:
        Dictionary with pending exams and their deadlines, or error if user not found
    """
    username_lower = username.lower()

    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found in the learning system",
            "available_users": list(LEARNING_DB.keys())
        }

    user_data = LEARNING_DB[username_lower]
    pending_exams = user_data["pending_exams"]
    exam_deadlines = user_data["exam_deadlines"]

    # Build exam details with deadlines
    exams_with_deadlines = []
    for exam in pending_exams:
        deadline = exam_deadlines.get(exam, "No deadline set")

        # Calculate days until deadline if deadline exists
        days_until = None
        if deadline != "No deadline set":
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                today = datetime.now()
                delta = deadline_date - today
                days_until = delta.days
            except ValueError:
                days_until = None

        exams_with_deadlines.append({
            "exam": exam,
            "deadline": deadline,
            "days_until_deadline": days_until,
            "urgent": days_until is not None and days_until <= 7
        })

    # Sort by deadline (urgent first)
    exams_with_deadlines.sort(key=lambda x: (x["days_until_deadline"] is None, x["days_until_deadline"] or 999))

    return {
        "success": True,
        "username": username_lower,
        "pending_exams": exams_with_deadlines,
        "total_pending": len(pending_exams),
        "urgent_exams": sum(1 for e in exams_with_deadlines if e["urgent"])
    }


def get_user_preferences(username: str) -> Dict[str, Any]:
    """Get user's learning preferences.

    Args:
        username: The username to look up

    Returns:
        Dictionary with learning preferences, or error if user not found
    """
    username_lower = username.lower()

    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found in the learning system",
            "available_users": list(LEARNING_DB.keys())
        }

    user_data = LEARNING_DB[username_lower]

    return {
        "success": True,
        "username": username_lower,
        "preferences": user_data["preferences"],
        "total_preferences": len(user_data["preferences"])
    }


def get_learning_summary(username: str) -> Dict[str, Any]:
    """Get complete learning journey summary for a user.

    Args:
        username: The username to look up

    Returns:
        Complete summary with courses, exams, preferences, and progress metrics
    """
    username_lower = username.lower()

    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{username}' not found in the learning system",
            "available_users": list(LEARNING_DB.keys())
        }

    user_data = LEARNING_DB[username_lower]

    # Calculate completion rate
    total_courses = len(user_data["courses_enrolled"]) + len(user_data["completed_courses"])
    completed_count = len(user_data["completed_courses"])
    completion_rate = round((completed_count / total_courses * 100), 2) if total_courses > 0 else 0

    # Get exam details
    pending_exams = user_data["pending_exams"]
    exam_deadlines = user_data["exam_deadlines"]

    exams_with_deadlines = []
    urgent_count = 0
    for exam in pending_exams:
        deadline = exam_deadlines.get(exam, "No deadline set")

        days_until = None
        if deadline != "No deadline set":
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                today = datetime.now()
                delta = deadline_date - today
                days_until = delta.days
                if days_until <= 7:
                    urgent_count += 1
            except ValueError:
                pass

        exams_with_deadlines.append({
            "exam": exam,
            "deadline": deadline,
            "days_until_deadline": days_until
        })

    return {
        "success": True,
        "username": username_lower,
        "learning_summary": {
            "courses": {
                "enrolled": user_data["courses_enrolled"],
                "completed": user_data["completed_courses"],
                "total_enrolled": len(user_data["courses_enrolled"]),
                "total_completed": completed_count,
                "completion_rate": f"{completion_rate}%"
            },
            "exams": {
                "pending": exams_with_deadlines,
                "total_pending": len(pending_exams),
                "urgent_exams": urgent_count
            },
            "preferences": user_data["preferences"],
            "overall_progress": {
                "completion_rate": completion_rate,
                "status": "On Track" if completion_rate >= 50 else "Needs Attention",
                "active_learning_paths": len(user_data["courses_enrolled"]),
                "achievements": completed_count
            }
        }
    }
