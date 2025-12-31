# Security: User Access Control

## Overview

Agentic Jarvis implements **role-based access control (RBAC)** to ensure users can only access their own data. This prevents security breaches where one user could query another user's sensitive information.

## Security Model

### Regular Users (Non-Admin)
- **Access**: Can ONLY access their own data
- **Enforcement**: All queries are automatically rewritten to use the authenticated username
- **Protection**: Cannot query other users' data, even if explicitly requested

### Admin Users (role="admin")
- **Access**: Can access ANY user's data
- **Use Case**: System administration, debugging, cross-user support
- **Bypass**: Security rewriting does not apply to admin users

## Implementation Details

### Query Rewriting

The security is enforced at the orchestrator level via the `_inject_user_context()` method in `jarvis_agent/main_with_registry.py` (lines 532-603).

**How It Works:**

1. **User Context Injection**: Replaces pronouns ("my", "I", "me") with the authenticated username
2. **Access Control**: If user is NOT admin, replaces any other username in the query with the authenticated user's username
3. **Pattern Matching**: Uses regex to detect and replace usernames in various formats

**Example:**

```python
# User: happy (role: developer)
Original Query: "show vishal's tickets"
Rewritten Query: "show happy's tickets"
Result: Only happy's tickets are shown

# User: admin (role: admin)
Original Query: "show vishal's tickets"
Rewritten Query: "show vishal's tickets" (unchanged)
Result: Vishal's tickets are shown (admin privilege)
```

### Known Users List

The system maintains a list of known usernames to detect and replace:

```python
known_users = ["vishal", "happy", "alex", "sarah"]
```

**Important**: When adding new users to the system, they should be added to this list in `main_with_registry.py:560` to ensure proper security enforcement.

## User Roles

### Current Users

| Username | User ID | Role | Password | Access Level |
|----------|---------|------|----------|--------------|
| vishal | user_001 | developer | password123 | Own data only |
| happy | user_002 | developer | password123 | Own data only |
| alex | user_003 | devops | password123 | Own data only |
| sarah | user_004 | data_scientist | password123 | Own data only |
| admin | user_admin | admin | admin123 | All users' data |

### Role Definitions

- **developer**: Regular developer user with standard access
- **devops**: DevOps engineer with standard access
- **data_scientist**: Data scientist with standard access
- **admin**: System administrator with elevated privileges

**Note**: Currently, only the "admin" role has elevated privileges. All other roles are treated as regular users with restricted access.

## Testing Access Control

### Manual Testing

```bash
# Terminal 1: Start all services
./scripts/start_phase2.sh

# Terminal 2: Test access control
python /tmp/test_access_control.py
```

### Test Scenarios

1. **Regular User Cannot Access Other User's Data**
   ```bash
   # Login as happy
   curl -X POST http://localhost:9998/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "happy", "password": "password123"}'

   # Try to query vishal's tickets (will be rewritten to happy's)
   # Result: Only happy's tickets shown
   ```

2. **Admin Can Access Any User's Data**
   ```bash
   # Login as admin
   curl -X POST http://localhost:9998/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'

   # Query vishal's tickets (allowed for admin)
   # Result: Vishal's tickets shown
   ```

3. **Query Variations Are Handled**
   - "show vishal's tickets"
   - "what are happy's courses"
   - "tickets for alex"
   - "list sarah courses"

   All variations are properly detected and rewritten.

## Security Best Practices

### Do's

✓ Always authenticate users via JWT before processing queries
✓ Validate user roles from the JWT token
✓ Use the `_inject_user_context()` method for all user queries
✓ Log access attempts for audit trails
✓ Add new users to the `known_users` list when created

### Don'ts

✗ Never bypass the access control layer for convenience
✗ Don't expose raw agent endpoints without authentication
✗ Don't trust client-side username claims - always use JWT
✗ Don't add new roles without updating the access control logic
✗ Never hard-code admin credentials in production

## Logging and Auditing

Access control enforcement is logged at DEBUG level:

```
jarvis_agent.main_with_registry - DEBUG - User context injected with access control: 'show happy's tickets' (user: happy, role: developer)
```

For production, consider:
- Logging all access attempts at INFO level
- Tracking failed authorization attempts
- Alerting on suspicious query patterns
- Audit logs for admin access to sensitive data

## Future Enhancements

### Planned Features

1. **Fine-Grained Permissions**
   - Role-based permissions (e.g., "ticket_manager" can see all tickets)
   - Resource-level permissions (e.g., "can_view_finops_data")

2. **Team-Based Access**
   - Users can access their team members' data
   - Team hierarchies (managers can access team data)

3. **Audit Trail**
   - Full audit log of all data access
   - Admin access tracking
   - Suspicious activity detection

4. **Dynamic User List**
   - Automatically detect usernames from database
   - Remove need for hardcoded `known_users` list

## Troubleshooting

### User Can Access Other User's Data

**Symptom**: Regular user sees another user's data in response

**Possible Causes**:
1. User role is incorrectly set to "admin"
2. Query rewriting is not being applied
3. Username not in `known_users` list

**Solution**:
1. Verify user role in `auth/user_service.py`
2. Check logs for "User context injected with access control" message
3. Add missing username to `known_users` list in `main_with_registry.py:560`

### Admin Cannot Access Other User's Data

**Symptom**: Admin user cannot see other users' data

**Possible Causes**:
1. Admin role is not "admin" (case-sensitive)
2. Access control logic is incorrectly applied to admins

**Solution**:
1. Verify admin user has `"role": "admin"` in `auth/user_service.py`
2. Check that role comparison uses `.lower()` for case-insensitivity

### Query Not Being Rewritten

**Symptom**: Username in query is not being replaced

**Possible Causes**:
1. Username pattern doesn't match regex
2. Username not in `known_users` list
3. `_inject_user_context()` not being called

**Solution**:
1. Check query format matches expected patterns
2. Add username to `known_users` list
3. Verify `_inject_user_context()` is called in query handling flow

## References

- Implementation: `jarvis_agent/main_with_registry.py:532-603`
- User Database: `auth/user_service.py:11-47`
- Test Script: `/tmp/test_access_control.py`
- Quick Test Guide: `docs/QUICK_TEST_GUIDE.md`
