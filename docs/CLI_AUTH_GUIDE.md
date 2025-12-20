# CLI Authentication Guide

## Overview

The Jarvis CLI now requires authentication before use. Users must login with valid credentials to access the interactive chat interface.

## Starting the CLI

```bash
python main.py
```

## Login Flow

### Step 1: Service Health Check
The CLI automatically checks if all required services are running:
- Tickets Toolbox Server (port 5001)
- FinOps Toolbox Server (port 5002)
- Oxygen A2A Agent (port 8002)
- Auth Service (port 9998)

If any service is not running, you'll see an error with instructions to start services.

### Step 2: Authentication

You'll be prompted to login:

```
🔐 Please login to continue
------------------------------------------------------------

Demo accounts available:
  • vishal / password123 (developer)
  • alex / password123 (devops)
  • sarah / password123 (data_scientist)

Username: vishal
Password: ********
```

**Demo Credentials:**
- **vishal** / password123 (Developer)
- **alex** / password123 (DevOps Engineer)
- **sarah** / password123 (Data Scientist)

### Step 3: Login Success

After successful authentication:

```
✅ Login successful!
   Welcome, vishal (developer)

============================================================
Logged in as: vishal (developer)
============================================================

Capabilities:
  • IT Tickets Management (via TicketsAgent)
  • Cloud Cost Analytics (via FinOpsAgent)
  • Learning & Development (via OxygenAgent)

Type 'exit' or 'quit' to end the session.

============================================================

Initializing Jarvis agent...
✅ Jarvis agent initialized successfully!
   Session ID: cli-session-vishal
   User context: vishal
   User-specific tools enabled
```

## Features

### Authentication
- **Maximum Attempts:** 3 login attempts before exit
- **Secure Password Input:** Password hidden with `getpass`
- **Token Management:** JWT token stored for session
- **User Context:** Authenticated user context passed to all agents

### User-Specific Tools

When authenticated, Jarvis automatically uses user-specific tools:

**Tickets:**
- "Show my tickets" → Uses `get_my_tickets` (returns only your tickets)
- "Create a ticket" → Uses `create_my_ticket` (creates ticket for you)

**Learning (Oxygen):**
- "What are my courses?" → Uses `get_my_courses` (your courses only)
- "Show my exams" → Uses `get_my_exams` (your exams only)
- "My learning summary" → Uses `get_my_learning_summary` (your data)

**FinOps:**
- Cloud costs are organization-wide (no user filtering)

## Example Session

```bash
$ python main.py

============================================================
🤖 Agentic Jarvis - Your Intelligent Assistant
============================================================

🔍 Checking service health...
✅ All services are healthy!

🔐 Please login to continue
------------------------------------------------------------

Demo accounts available:
  • vishal / password123 (developer)
  • alex / password123 (devops)
  • sarah / password123 (data_scientist)

Username: vishal
Password:

✅ Login successful!
   Welcome, vishal (developer)

============================================================
Logged in as: vishal (developer)
============================================================

Capabilities:
  • IT Tickets Management (via TicketsAgent)
  • Cloud Cost Analytics (via FinOpsAgent)
  • Learning & Development (via OxygenAgent)

Type 'exit' or 'quit' to end the session.

============================================================

Initializing Jarvis agent...
✅ Jarvis agent initialized successfully!
   Session ID: cli-session-vishal
   User context: vishal
   User-specific tools enabled


👤 You: What are my tickets?

🤖 Jarvis: You have 2 tickets:

1. **Ticket #12301** - Create AI Key
   - Status: Pending
   - Created: 2025-01-10

2. **Ticket #12303** - Update Budget
   - Status: In Progress
   - Created: 2025-01-11


👤 You: What courses am I taking?

🤖 Jarvis: You are currently enrolled in 2 courses:

1. **AWS** - Amazon Web Services
2. **Terraform** - Infrastructure as Code

You have completed 1 course:
- **Docker** - Container Platform

Your completion rate is 33.33%. You have 1 pending exam:
- **Snowflake** (Deadline: December 28, 2025)


👤 You: exit

👋 Goodbye! Thanks for using Jarvis.
```

## Error Handling

### Auth Service Not Running

```
❌ Cannot connect to auth service at http://localhost:9998

Please start the auth service:
  python auth/auth_server.py

❌ Authentication failed. Exiting...
```

**Solution:** Start the auth service on port 9998

### Invalid Credentials

```
Username: wronguser
Password:

❌ Invalid username or password
   2 attempts remaining
```

**Solution:** Use valid demo credentials

### Maximum Attempts Exceeded

```
❌ Invalid username or password
   0 attempts remaining

❌ Maximum login attempts (3) exceeded
❌ Authentication failed. Exiting...
```

**Solution:** Restart the CLI with correct credentials

### Services Not Running

```
⚠️  Error: Some services are not running!

Please start all services first:
  ./scripts/restart_all.sh

Then verify with:
  ./scripts/check_services.sh
```

**Solution:** Start all required services

## Security Features

### Password Protection
- Passwords are hidden during input using `getpass`
- Passwords are never displayed or logged
- Failed attempts are tracked and limited

### JWT Token
- Token expires after 24 hours
- Token is stored only in memory (not persisted)
- Token is lost when CLI exits

### Session Isolation
- Each user gets their own session ID
- User data is filtered by authenticated user
- Sessions are isolated by user_id

## Testing Different Users

To test with different users, exit the CLI and restart:

```bash
# Test as vishal
python main.py
# Login: vishal / password123
# exit

# Test as alex
python main.py
# Login: alex / password123
# exit

# Test as sarah
python main.py
# Login: sarah / password123
# exit
```

Each user will see only their own:
- Tickets (get_my_tickets)
- Courses (get_my_courses)
- Exams (get_my_exams)
- Learning data (get_my_learning_summary)

## Environment Variables

The CLI uses these environment variables (optional):

```bash
AUTH_SERVICE_URL=http://localhost:9998  # Auth service URL
```

If not set, defaults to `http://localhost:9998`

## Troubleshooting

**Q: I forgot my password**
A: Use demo credentials from the list shown at login

**Q: Login takes too long**
A: Check if auth service is running and responsive

**Q: "User-specific tools" not working**
A: Verify that toolbox servers and Oxygen agent are running

**Q: Can I skip authentication?**
A: No, authentication is required. Use the Dev UI (http://localhost:9999/dev-ui) for unauthenticated access

## Next Steps

After successful CLI authentication, you can:
1. Ask about your tickets: "Show my tickets"
2. Create new tickets: "Create a ticket for GitLab access"
3. Check learning progress: "What are my courses?"
4. View exams: "Do I have any pending exams?"
5. Get cost data: "What are our cloud costs?" (organization-wide)

For web-based interface with authentication, see `web_ui/` (Task 24).
