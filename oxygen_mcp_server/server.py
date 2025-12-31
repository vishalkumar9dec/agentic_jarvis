"""
Oxygen MCP Server - Tool Definitions
Uses FastMCP library for Model Context Protocol.

Port: 8012 (NEW - parallel to existing 8002 A2A)
Protocol: MCP (Model Context Protocol)
Phase: 2B - With authentication for user-specific features

This server provides learning and development platform tools via MCP.
Public tools for viewing any user, authenticated tools for personal data.
"""

from fastmcp import FastMCP
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os

# Add project root to Python path for auth imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# =============================================================================
# In-Memory Learning Database (Mock Data - Same as Phase 1)
# =============================================================================
# In production, this would be replaced with a real LMS database connection

LEARNING_DB: Dict[str, Dict[str, Any]] = {
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

# =============================================================================
# FastMCP Server Instance
# =============================================================================

mcp = FastMCP("oxygen-server")


# ============================================================================
# Helper Function: Get Current Authenticated User
# ============================================================================

def get_current_user() -> Dict:
    """
    Get authenticated user from current request context.

    This helper extracts user claims from the authenticated request.
    Authentication middleware (added in app.py) populates request.user.

    Returns:
        Dict containing user claims:
            - username: User's username
            - user_id: Unique user identifier
            - role: User's role (admin, developer, user)

    Raises:
        ValueError: If called from unauthenticated context
    """
    from fastmcp.server.dependencies import get_http_request

    request = get_http_request()

    # Check if user is authenticated
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        raise ValueError("Authentication required")

    return request.user.identity


# =============================================================================
# PUBLIC TOOLS (No Authentication)
# =============================================================================
# These tools accept username as a parameter.
# Authenticated versions (get_my_*) will be added in Task 11.


@mcp.tool()
def get_user_courses(username: str) -> Dict[str, Any]:
    """Get all courses for a specific user.

    Retrieves enrolled and completed courses for a user in the
    learning and development platform.

    Args:
        username (str): The username to look up. Case-insensitive.

    Returns:
        Dict[str, Any]: Course information with fields:
            - success (bool): Whether lookup succeeded
            - username (str): Normalized username
            - courses_enrolled (List[str]): Currently enrolled courses
            - completed_courses (List[str]): Completed courses
            - total_enrolled (int): Count of enrolled courses
            - total_completed (int): Count of completed courses
            - in_progress (int): Count of courses in progress

        Or error dict if user not found:
            - success (bool): False
            - error (str): Error message
            - available_users (List[str]): Valid usernames

    Example:
        >>> result = get_user_courses("vishal")
        >>> result['courses_enrolled']
        ['aws', 'terraform']
        >>> result['total_completed']
        1
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


@mcp.tool()
def get_pending_exams(username: str) -> Dict[str, Any]:
    """Get pending exams with deadlines for a specific user.

    Retrieves all pending exams for a user, including deadlines,
    days remaining, and urgency flags.

    Args:
        username (str): The username to look up. Case-insensitive.

    Returns:
        Dict[str, Any]: Exam information with fields:
            - success (bool): Whether lookup succeeded
            - username (str): Normalized username
            - pending_exams (List[Dict]): Exam details (sorted by urgency):
                - exam (str): Exam name
                - deadline (str): Deadline date (YYYY-MM-DD)
                - days_until_deadline (int | None): Days remaining
                - urgent (bool): True if deadline <= 7 days
            - total_pending (int): Count of pending exams
            - urgent_exams (int): Count of urgent exams

        Or error dict if user not found.

    Example:
        >>> result = get_pending_exams("alex")
        >>> result['urgent_exams']
        1
        >>> result['pending_exams'][0]['urgent']
        True
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
    exams_with_deadlines.sort(
        key=lambda x: (x["days_until_deadline"] is None, x["days_until_deadline"] or 999)
    )

    return {
        "success": True,
        "username": username_lower,
        "pending_exams": exams_with_deadlines,
        "total_pending": len(pending_exams),
        "urgent_exams": sum(1 for e in exams_with_deadlines if e["urgent"])
    }


@mcp.tool()
def get_user_preferences(username: str) -> Dict[str, Any]:
    """Get learning preferences for a specific user.

    Retrieves the user's learning interests and preferences.

    Args:
        username (str): The username to look up. Case-insensitive.

    Returns:
        Dict[str, Any]: Preferences with fields:
            - success (bool): Whether lookup succeeded
            - username (str): Normalized username
            - preferences (List[str]): User's learning interests
            - total_preferences (int): Count of preferences

        Or error dict if user not found.

    Example:
        >>> result = get_user_preferences("vishal")
        >>> result['preferences']
        ['software engineering', 'cloud architecture']
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


@mcp.tool()
def get_learning_summary(username: str) -> Dict[str, Any]:
    """Get complete learning journey summary for a specific user.

    Provides comprehensive overview of user's learning progress,
    including courses, exams, preferences, and completion metrics.

    Args:
        username (str): The username to look up. Case-insensitive.

    Returns:
        Dict[str, Any]: Complete summary with fields:
            - success (bool): Whether lookup succeeded
            - username (str): Normalized username
            - learning_summary (Dict): Nested summary:
                - courses (Dict): Course information
                - exams (Dict): Exam information with urgency
                - preferences (List[str]): Learning interests
                - overall_progress (Dict): Progress metrics:
                    - completion_rate (float): % completed
                    - status (str): "On Track" or "Needs Attention"
                    - active_learning_paths (int): Enrolled courses
                    - achievements (int): Completed courses

        Or error dict if user not found.

    Example:
        >>> result = get_learning_summary("alex")
        >>> result['learning_summary']['overall_progress']['completion_rate']
        50.0
        >>> result['learning_summary']['overall_progress']['status']
        'On Track'
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


# =============================================================================
# AUTHENTICATED TOOLS (Task 12 - ADK ToolContext Pattern)
# =============================================================================
# These tools use ADK's ToolContext to access authentication state.
# Authentication is validated centrally by before_tool_callback in callbacks.py


@mcp.tool()
def get_my_courses() -> Dict[str, Any]:
    """Get all courses for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Returns course information for the currently authenticated user.

    Authentication is handled automatically by FastMCP middleware:
    1. Middleware extracts Bearer token from Authorization header
    2. Validates token using JWTTokenVerifier
    3. Returns 401 automatically if token is invalid/expired
    4. Injects authenticated user into request.user

    Returns:
        Dict[str, Any]: Course information for authenticated user.

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = get_my_courses()
        >>> result['courses_enrolled']
        ['aws', 'terraform']
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]

    # Get user's courses
    username_lower = current_user.lower()
    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{current_user}' not found in the learning system",
            "status": 404
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


@mcp.tool()
def get_my_exams() -> Dict[str, Any]:
    """Get pending exams for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Returns exam information with deadlines for the authenticated user.

    Authentication is handled automatically by FastMCP middleware.

    Returns:
        Dict[str, Any]: Exam information for authenticated user.

    Example (when authenticated as alex):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = get_my_exams()
        >>> result['total_pending']
        2
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]

    # Get user's exams
    username_lower = current_user.lower()
    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{current_user}' not found in the learning system",
            "status": 404
        }

    user_data = LEARNING_DB[username_lower]
    pending_exams = user_data["pending_exams"]
    exam_deadlines = user_data["exam_deadlines"]

    # Build exam details with deadline info
    exams_with_deadlines = []
    urgent_count = 0

    for exam in pending_exams:
        deadline = exam_deadlines.get(exam, "No deadline set")

        days_until = None
        is_urgent = False
        if deadline != "No deadline set":
            try:
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                today = datetime.now()
                delta = deadline_date - today
                days_until = delta.days
                if days_until <= 7:
                    is_urgent = True
                    urgent_count += 1
            except ValueError:
                pass

        exams_with_deadlines.append({
            "exam": exam,
            "deadline": deadline,
            "days_until_deadline": days_until,
            "is_urgent": is_urgent
        })

    return {
        "success": True,
        "username": username_lower,
        "pending_exams": exams_with_deadlines,
        "total_pending": len(pending_exams),
        "urgent_exams": urgent_count
    }


@mcp.tool()
def get_my_preferences() -> Dict[str, Any]:
    """Get learning preferences for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Returns learning interests and preferences for the authenticated user.

    Authentication is handled automatically by FastMCP middleware.

    Returns:
        Dict[str, Any]: Preferences for authenticated user.

    Example (when authenticated as vishal):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = get_my_preferences()
        >>> result['preferences']
        ['software engineering', 'cloud architecture']
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]

    # Get user's preferences
    username_lower = current_user.lower()
    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{current_user}' not found in the learning system",
            "status": 404
        }

    user_data = LEARNING_DB[username_lower]

    return {
        "success": True,
        "username": username_lower,
        "preferences": user_data["preferences"],
        "total_preferences": len(user_data["preferences"])
    }


@mcp.tool()
def get_my_learning_summary() -> Dict[str, Any]:
    """Get complete learning journey summary for the authenticated user.

    This tool requires authentication via HTTP Authorization header.
    Provides comprehensive overview of the authenticated user's learning progress.

    Authentication is handled automatically by FastMCP middleware.

    Returns:
        Dict[str, Any]: Complete learning summary for authenticated user.

    Example (when authenticated as alex):
        >>> # HTTP Request includes: Authorization: Bearer <valid_jwt>
        >>> result = get_my_learning_summary()
        >>> result['learning_summary']['overall_progress']['completion_rate']
        50.0
    """
    # Get authenticated user from middleware
    user = get_current_user()
    current_user = user["username"]

    # Get user's learning data
    username_lower = current_user.lower()
    if username_lower not in LEARNING_DB:
        return {
            "success": False,
            "error": f"User '{current_user}' not found in the learning system",
            "status": 404
        }

    user_data = LEARNING_DB[username_lower]

    # Calculate completion rate
    total_courses = len(user_data["courses_enrolled"]) + len(user_data["completed_courses"])
    completed_count = len(user_data["completed_courses"])
    completion_rate = round((completed_count / total_courses * 100), 2) if total_courses > 0 else 0

    # Get exam details with urgency
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
