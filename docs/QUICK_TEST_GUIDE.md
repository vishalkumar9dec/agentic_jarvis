# Quick Test Guide - Pure A2A (5 Minutes)

One-page guide to quickly test the Pure A2A implementation.

---

## 1️⃣ Start Services (1 min)

```bash
./scripts/start_phase2.sh
```

✅ **Success:** You see "✅ All Services Started Successfully!"

---

## 2️⃣ Start Jarvis (30 sec)

```bash
python jarvis_agent/main_with_registry.py
```

---

## 3️⃣ Login (30 sec)

```
Username: vishal
Password: password123
```

✅ **Success:** You see "Jarvis is ready!"

---

## 4️⃣ Test Queries (2 min)

### Query 1: Single Agent (TicketsAgent)
```
vishal> show my tickets
```
✅ **Expected:** 2 tickets for vishal (IDs: 12301, 12303)

### Query 2: Single Agent (OxygenAgent)
```
vishal> what are my pending exams
```
✅ **Expected:** 2 exams with deadlines

### Query 3: Multi-Agent Query
```
vishal> show my tickets and my courses
```
✅ **Expected:** Both tickets AND courses in response

### Query 4: Organization Data (FinOpsAgent)
```
vishal> what is our total cloud cost
```
✅ **Expected:** $36,605.50 USD total

---

## 5️⃣ Test Session Persistence (1 min)

### Step 1: Exit
```
vishal> /exit
```

### Step 2: Restart & Login
```bash
python jarvis_agent/main_with_registry.py
```
Login as vishal again.

✅ **Expected:** See "Welcome back!" message with session info

### Step 3: Check History
```
vishal> /history
```
✅ **Expected:** Previous queries are still there!

---

## 6️⃣ Test User Isolation (1 min)

### Exit and login as different user
```
vishal> /exit
```

Start again and login as **happy**:
```
Username: happy
Password: password123
```

### Query tickets
```
happy> show my tickets
```

✅ **Expected:** Only 1 ticket (ID: 12302) - NOT vishal's tickets!

---

## 7️⃣ Test Security (Optional - 1 min)

### Try to access another user's data
```
happy> show vishal's tickets
```

✅ **Expected:** Still shows happy's ticket (12302), NOT vishal's!

**Why?** Non-admin users can ONLY see their own data. The query is automatically rewritten to "show happy's tickets" for security.

### Test admin access
```
happy> /exit
```

Login as **admin**:
```
Username: admin
Password: admin123
```

```
admin> show vishal's tickets
```

✅ **Expected:** Shows vishal's tickets (12301, 12303) - admin can access any data!

For complete security documentation, see: [SECURITY_ACCESS_CONTROL.md](./SECURITY_ACCESS_CONTROL.md)

---

## Done! ✅

If all tests passed, your Pure A2A implementation is working correctly!

---

## Test Users Reference

| User | Password | Role | Tickets | Courses | Exams |
|------|----------|------|---------|---------|-------|
| vishal | password123 | developer | 2 | 3 | 2 |
| happy | password123 | developer | 1 | 2 | 1 |
| alex | password123 | devops | 0 | 2 | 1 |
| admin | admin123 | admin | N/A | N/A | N/A |

**Note:** Admin user can access ANY user's data for system administration.

---

## Common Issues

### "Service not available"
```bash
./scripts/stop_all_services.sh
./scripts/start_phase2.sh
```

### "Authentication failed"
- Username: **vishal** (not Vishal)
- Password: **password123** (case-sensitive)

### Port already in use
```bash
lsof -ti:8080 | xargs kill -9  # Repeat for 8081, 8082, 8003, 9998
./scripts/start_phase2.sh
```

---

## Detailed Testing

For comprehensive testing, see: [TESTING_PURE_A2A.md](./TESTING_PURE_A2A.md)
