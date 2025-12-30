# Manual Testing Guide - Agent Registry Service

This guide provides step-by-step instructions for manually testing the Agent Registry Service components.

---

## Task 1.2: AgentFactoryResolver Manual Testing

### Prerequisites

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Verify environment
python --version  # Should be Python 3.11+
```

### Test 1: Basic Agent Creation with Real Factory

**Purpose**: Test creating a real agent using the existing factory functions.

```python
# Run in Python REPL
python

# Import required modules
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver

# Create resolver instance
resolver = AgentFactoryResolver()

# Configure agent creation
config = {
    "agent_type": "tickets",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_tickets_agent",
    "factory_params": {}
}

# Create the agent
try:
    agent = resolver.create_agent(config)
    print(f"✓ Agent created successfully: {agent.name}")
    print(f"✓ Agent model: {agent.model}")
    print(f"✓ Agent description: {agent.description}")
except Exception as e:
    print(f"✗ Error creating agent: {e}")
```

**Expected Output**:
```
✓ Agent created successfully: TicketsAgent
✓ Agent model: gemini-2.5-flash
✓ Agent description: IT operations ticket management agent using MCP protocol
```

---

### Test 2: Create Multiple Agent Types

**Purpose**: Test creating different types of agents.

```python
# In Python REPL
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver

resolver = AgentFactoryResolver()

# Create Tickets Agent
tickets_config = {
    "agent_type": "tickets",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_tickets_agent",
    "factory_params": {}
}

# Create FinOps Agent
finops_config = {
    "agent_type": "finops",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_finops_agent",
    "factory_params": {}
}

# Create Oxygen Agent
oxygen_config = {
    "agent_type": "oxygen",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_oxygen_agent",
    "factory_params": {}
}

# Create all agents
try:
    tickets_agent = resolver.create_agent(tickets_config)
    finops_agent = resolver.create_agent(finops_config)
    oxygen_agent = resolver.create_agent(oxygen_config)

    print(f"✓ Created {tickets_agent.name}")
    print(f"✓ Created {finops_agent.name}")
    print(f"✓ Created {oxygen_agent.name}")

    # Check cache stats
    stats = resolver.get_cache_stats()
    print(f"\n✓ Cached modules: {stats['cached_modules']}")
    print(f"✓ Registered factories: {stats['registered_factories']}")
except Exception as e:
    print(f"✗ Error: {e}")
```

**Expected Output**:
```
✓ Created TicketsAgent
✓ Created FinOpsAgent
✓ Created OxygenAgent

✓ Cached modules: 1
✓ Registered factories: 0
```

---

### Test 3: Factory Registration

**Purpose**: Test registering custom factory functions.

```python
# In Python REPL
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver
from unittest.mock import Mock

resolver = AgentFactoryResolver()

# Create a mock factory
def create_test_agent():
    agent = Mock()
    agent.name = "TestAgent"
    agent.model = "test-model"
    agent.description = "Test agent for manual testing"
    return agent

# Register the factory
resolver.register_factory("test", create_test_agent)

# List available factories
factories = resolver.list_available_factories()
print(f"✓ Registered factories: {factories}")

# Create agent using registered factory
config = {
    "agent_type": "test",
    "factory_module": "unused",
    "factory_function": "unused"
}

agent = resolver.create_agent(config)
print(f"✓ Agent name: {agent.name}")
print(f"✓ Agent model: {agent.model}")
print(f"✓ Agent description: {agent.description}")
```

**Expected Output**:
```
✓ Registered factories: ['test']
✓ Agent name: TestAgent
✓ Agent model: test-model
✓ Agent description: Test agent for manual testing
```

---

### Test 4: Error Handling

**Purpose**: Test error handling for invalid configurations.

```python
# In Python REPL
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver, AgentFactoryError

resolver = AgentFactoryResolver()

# Test 1: Missing required fields
print("Test 1: Missing required fields")
try:
    config = {"agent_type": "test"}  # Missing factory_module and factory_function
    resolver.create_agent(config)
    print("✗ Should have raised error")
except AgentFactoryError as e:
    print(f"✓ Correctly raised error: {e}")

# Test 2: Invalid module
print("\nTest 2: Invalid module")
try:
    config = {
        "agent_type": "test",
        "factory_module": "nonexistent.module.that.does.not.exist",
        "factory_function": "create_agent"
    }
    resolver.create_agent(config)
    print("✗ Should have raised error")
except AgentFactoryError as e:
    print(f"✓ Correctly raised error: Module not found")

# Test 3: Invalid function
print("\nTest 3: Invalid function")
try:
    config = {
        "agent_type": "test",
        "factory_module": "os.path",
        "factory_function": "nonexistent_function"
    }
    resolver.create_agent(config)
    print("✗ Should have raised error")
except AgentFactoryError as e:
    print(f"✓ Correctly raised error: Function not found")
```

**Expected Output**:
```
Test 1: Missing required fields
✓ Correctly raised error: Missing required keys in agent_config: ['factory_module', 'factory_function']

Test 2: Invalid module
✓ Correctly raised error: Module not found

Test 3: Invalid function
✓ Correctly raised error: Function not found
```

---

### Test 5: Module Caching Performance

**Purpose**: Test that module caching improves performance.

```python
# In Python REPL
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver
import time

resolver = AgentFactoryResolver()

config = {
    "agent_type": "tickets",
    "factory_module": "jarvis_agent.mcp_agents.agent_factory",
    "factory_function": "create_tickets_agent",
    "factory_params": {}
}

# First creation (module import + agent creation)
start = time.time()
agent1 = resolver.create_agent(config)
time1 = time.time() - start

# Second creation (cached module + agent creation)
start = time.time()
agent2 = resolver.create_agent(config)
time2 = time.time() - start

print(f"First creation: {time1:.4f} seconds")
print(f"Second creation: {time2:.4f} seconds")
print(f"✓ Speedup: {time1/time2:.2f}x faster")

# Verify cache
stats = resolver.get_cache_stats()
print(f"\n✓ Cached modules: {stats['cached_modules']}")
```

**Expected Output**:
```
First creation: 0.0523 seconds
Second creation: 0.0012 seconds
✓ Speedup: 43.58x faster

✓ Cached modules: 1
```

---

### Test 6: Factory with Parameters

**Purpose**: Test creating agents with factory parameters.

```python
# In Python REPL
from agent_registry_service.registry.agent_factory_resolver import AgentFactoryResolver
from unittest.mock import Mock

resolver = AgentFactoryResolver()

# Create parameterized factory
def create_custom_agent(name="DefaultAgent", port=8000):
    agent = Mock()
    agent.name = name
    agent.port = port
    agent.config = {"name": name, "port": port}
    return agent

resolver.register_factory("custom", create_custom_agent)

# Test with custom parameters
config = {
    "agent_type": "custom",
    "factory_module": "unused",
    "factory_function": "unused",
    "factory_params": {
        "name": "CustomTicketsAgent",
        "port": 5011
    }
}

agent = resolver.create_agent(config)
print(f"✓ Agent name: {agent.name}")
print(f"✓ Agent port: {agent.port}")
print(f"✓ Agent config: {agent.config}")
```

**Expected Output**:
```
✓ Agent name: CustomTicketsAgent
✓ Agent port: 5011
✓ Agent config: {'name': 'CustomTicketsAgent', 'port': 5011}
```

---

## Task 1.1: FileStore Manual Testing

### Test 1: Basic Save and Load

```python
# In Python REPL
from agent_registry_service.registry.file_store import FileStore
import tempfile
import os

# Create FileStore with temp directory
temp_dir = tempfile.mkdtemp()
file_path = os.path.join(temp_dir, "test_registry.json")
store = FileStore(file_path)

# Create test data
registry_data = {
    "version": "1.0.0",
    "agents": {
        "tickets_agent": {
            "name": "tickets_agent",
            "description": "IT operations agent",
            "enabled": True
        }
    }
}

# Save data
result = store.save(registry_data)
print(f"✓ Save successful: {result}")

# Load data
loaded_data = store.load()
print(f"✓ Loaded version: {loaded_data['version']}")
print(f"✓ Agents count: {len(loaded_data['agents'])}")
print(f"✓ Agent name: {loaded_data['agents']['tickets_agent']['name']}")

# Cleanup
import shutil
shutil.rmtree(temp_dir)
```

**Expected Output**:
```
✓ Save successful: True
✓ Loaded version: 1.0.0
✓ Agents count: 1
✓ Agent name: tickets_agent
```

---

### Test 2: Backup and Restore

```python
# In Python REPL
from agent_registry_service.registry.file_store import FileStore
import tempfile
import os
import shutil

temp_dir = tempfile.mkdtemp()
file_path = os.path.join(temp_dir, "test_registry.json")
store = FileStore(file_path)

# Save original data
original_data = {
    "version": "1.0.0",
    "agents": {"agent1": {"name": "agent1"}}
}
store.save(original_data)

# Modify and save (creates backup)
modified_data = {
    "version": "1.0.0",
    "agents": {"agent2": {"name": "agent2"}}
}
store.save(modified_data)

print(f"✓ Backup file exists: {store.backup_path.exists()}")

# Restore from backup
result = store.restore_from_backup()
print(f"✓ Restore successful: {result}")

# Verify restoration
loaded_data = store.load()
print(f"✓ Restored agent: {list(loaded_data['agents'].keys())[0]}")

# Cleanup
shutil.rmtree(temp_dir)
```

**Expected Output**:
```
✓ Backup file exists: True
✓ Restore successful: True
✓ Restored agent: agent1
```

---

## Running Automated Tests

```bash
# Run all tests
source .venv/bin/activate

# Test FileStore
python -m pytest agent_registry_service/tests/test_file_store.py -v

# Test AgentFactoryResolver
python -m pytest agent_registry_service/tests/test_factory_resolver.py -v

# Run both with coverage
python -m pytest agent_registry_service/tests/ -v
```

---

## Troubleshooting

### Issue: ModuleNotFoundError

**Symptom**: Cannot import agent_registry_service modules

**Solution**:
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/Users/vishalkumar/projects/agentic_jarvis"

# Or run from project root
cd /Users/vishalkumar/projects/agentic_jarvis
python
```

### Issue: Cannot create real agents (MCP servers not running)

**Symptom**: Agent creation fails with connection errors

**Solution**:
```bash
# Start required MCP servers first
./scripts/start_tickets_server.sh
./scripts/start_finops_server.sh
./scripts/start_oxygen_agent.sh
```

**Note**: For testing AgentFactoryResolver alone, you don't need MCP servers running. The factory resolver is tested independently.

---

## Summary Checklist

- [ ] FileStore saves and loads data correctly
- [ ] FileStore creates backups automatically
- [ ] FileStore restores from backup when main file corrupted
- [ ] AgentFactoryResolver creates agents from config
- [ ] AgentFactoryResolver caches modules for performance
- [ ] AgentFactoryResolver handles errors gracefully
- [ ] AgentFactoryResolver supports factory registration
- [ ] AgentFactoryResolver supports factory parameters
- [ ] All automated tests pass (51 tests total)
