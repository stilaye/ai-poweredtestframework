# PractiTest Plugin Hooks Reference

## Overview

The PractiTest pytest plugin uses pytest's hook system to integrate seamlessly with test execution. This document details the plugin's implementation and hook usage.

## Plugin Lifecycle

The plugin follows pytest's standard hook execution order:

```
pytest_configure
    ↓
pytest_collection_modifyitems
    ↓
pytest_sessionstart
    ↓
pytest_runtest_setup (for each test)
    ↓
pytest_runtest_makereport (for each test)
    ↓
pytest_sessionfinish
```

## Hook Implementations

### `pytest_configure(config)`

**Purpose:** Configure the plugin when pytest starts

**Execution:** Once at startup

**Logic:**
1. Check for `--practitest` command line flag
2. Load environment variables from `.env` file
3. Validate PractiTest credentials
4. Initialize PractiTest client
5. Enable plugin if all conditions met

**Code Flow:**
```python
def pytest_configure(self, config):
    # Check --practitest flag
    if not config.getoption("--practitest", default=False):
        return  # Plugin disabled
    
    # Load .env file
    load_dotenv()
    
    # Get credentials
    email = os.getenv("PRACTITEST_EMAIL")
    token = os.getenv("PRACTITEST_TOKEN") 
    project_id = os.getenv("PRACTITEST_PROJECT_ID")
    
    # Validate and initialize
    if all([email, token, project_id]):
        self.client = PractiTestClient(email, token, project_id)
        self.enabled = True
```

**Exit Conditions:**
- Missing `--practitest` flag → Plugin remains disabled
- Missing credentials → Plugin remains disabled, warning logged
- Client initialization failure → Plugin disabled, error logged

### `pytest_collection_modifyitems(config, items)`

**Purpose:** Validate that marked tests exist after collection

**Execution:** Once after test collection

**Logic:**
1. Count tests with `@pytest.mark.practitestid` markers
2. Disable plugin if no marked tests found
3. Log information about marked tests

**Code Flow:**
```python
def pytest_collection_modifyitems(self, config, items):
    if not self.enabled:
        return
    
    # Find tests with practitestid markers
    marked_tests = [item for item in items if item.get_closest_marker("practitestid")]
    
    if not marked_tests:
        self.enabled = False  # No tests to report
        return
    
    # Log count of marked tests
    self.logger.info(f"Found {len(marked_tests)} tests with practitestid markers")
```

**Exit Conditions:**
- Plugin not enabled → No action
- No marked tests → Plugin disabled, info logged

### `pytest_sessionstart(session)`

**Purpose:** Create test set in PractiTest for this test run

**Execution:** Once at session start

**Logic:**
1. Gather system information (node version, OS)
2. Generate test set name with metadata
3. Create test set in PractiTest
4. Store test set ID for later use

**Code Flow:**
```python
def pytest_sessionstart(self, session):
    if not self.enabled:
        return
    
    # Get system info
    node_version = get_node_version()
    os_name = get_os_distribution()
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Create test set
    test_set_name = f"Automated Test Run-{node_version}-{os_name}-{timestamp}"
    self.test_set_id = self.client.get_or_create_test_set(test_set_name, description)
```

**Generated Test Set Names:**
```
Automated Test Run-1.2.3-Ubuntu 20.04-2024-01-15_14-30-45
Automated Test Run-2.1.0-Windows 10-2024-01-15_09-15-22
Automated Test Run-Unknown-macOS-2024-01-15_16-45-33
```

**Exit Conditions:**
- Plugin not enabled → No action
- Test set creation failure → Plugin disabled, error logged

### `pytest_runtest_setup(item)`

**Purpose:** Create test instance in PractiTest for each marked test

**Execution:** Before each test with `practitestid` marker

**Logic:**
1. Check if test has `@pytest.mark.practitestid` marker
2. Extract display ID from marker
3. Lookup test in PractiTest by display ID
4. Create test instance in the test set
5. Store instance ID for result reporting

**Code Flow:**
```python
def pytest_runtest_setup(self, item):
    if not self.enabled or not self.test_set_id:
        return
    
    # Get practitestid marker
    practitest_marker = item.get_closest_marker("practitestid")
    if not practitest_marker or not practitest_marker.args:
        return
    
    display_id = str(practitest_marker.args[0])
    
    # Get test from PractiTest
    test_data = self.client.get_test_by_display_id(display_id)
    if test_data:
        # Create test instance
        instance_id = self.client.create_test_instance(
            test_data["id"], 
            self.test_set_id
        )
        self.test_instances[item.nodeid] = instance_id
```

**Exit Conditions:**
- Plugin not enabled → No action
- No test set ID → No action
- No marker or invalid marker → No action
- Test not found in PractiTest → Warning logged
- Instance creation failure → Error logged

### `pytest_runtest_makereport(item, call)`

**Purpose:** Capture test results for reporting

**Execution:** After each test execution (setup, call, teardown phases)

**Logic:**
1. Only process "call" phase (main test execution)
2. Determine test status from exception info
3. Extract failure details if test failed
4. Store result data for later reporting

**Code Flow:**
```python
def pytest_runtest_makereport(self, item, call):
    if call.when == "call":  # Only main test execution
        if not self.enabled or item.nodeid not in self.test_instances:
            return
        
        # Determine status
        if call.excinfo is None:
            status = 0  # PASSED
            notes = "Test passed successfully"
        else:
            status = 1  # FAILED
            notes = f"Test failed: {str(call.excinfo.value)}"
        
        # Store for later reporting
        self.test_results[item.nodeid] = {
            "status": status,
            "notes": notes,
            "duration": getattr(call, 'duration', None)
        }
```

**Status Mapping:**
- `call.excinfo is None` → Status 0 (PASSED)
- `call.excinfo is not None` → Status 1 (FAILED)

**Exit Conditions:**
- Not "call" phase → No action
- Plugin not enabled → No action
- Test instance not found → No action

### `pytest_sessionfinish(session, exitstatus)`

**Purpose:** Report all test results to PractiTest

**Execution:** Once at session end

**Logic:**
1. Check for duplicate reporting prevention
2. Iterate through all captured results
3. Report each result to PractiTest
4. Log success/failure for each update

**Code Flow:**
```python
def pytest_sessionfinish(self, session, exitstatus):
    if not self.enabled or not self.test_results:
        return
    
    # Prevent duplicate reporting
    if hasattr(self, '_results_reported'):
        return
    self._results_reported = True
    
    # Report all results
    for nodeid, result_data in self.test_results.items():
        if nodeid in self.test_instances:
            instance_id = self.test_instances[nodeid]
            success = self.client.update_test_result(
                instance_id=instance_id,
                status=result_data["status"],
                notes=result_data["notes"],
                duration=int(result_data["duration"]) if result_data["duration"] else None
            )
```

**Exit Conditions:**
- Plugin not enabled → No action
- No results to report → No action
- Already reported → No action (duplicate prevention)

## Plugin State Management

### Instance Variables

```python
class PractiTestPlugin:
    def __init__(self):
        self.client: Optional[PractiTestClient] = None
        self.test_set_id: Optional[str] = None
        self.test_instances: Dict[str, str] = {}  # nodeid -> instance_id
        self.test_results: Dict[str, Dict[str, Any]] = {}  # nodeid -> result data
        self.logger = logging.getLogger(__name__)
        self.enabled = False
```

### State Transitions

```
Initial State:
  enabled = False
  client = None

pytest_configure:
  enabled = True (if conditions met)
  client = PractiTestClient(...)

pytest_collection_modifyitems:
  enabled = False (if no marked tests)

pytest_sessionstart:
  test_set_id = "12345"
  enabled = False (if test set creation fails)

pytest_runtest_setup:
  test_instances[nodeid] = instance_id

pytest_runtest_makereport:
  test_results[nodeid] = {...}

pytest_sessionfinish:
  _results_reported = True
```

## Error Handling Strategy

### Graceful Degradation

The plugin is designed to fail gracefully:

1. **Missing Dependencies:** Plugin disables itself
2. **API Errors:** Individual operations fail but don't stop test execution
3. **Network Issues:** Results not reported but tests continue
4. **Invalid Configuration:** Clear warnings with fallback behavior

### Logging Strategy

```python
# Info: Normal operation milestones
self.logger.info("PractiTest integration enabled")
self.logger.info(f"Created test set: {test_set_name}")

# Warning: Non-fatal issues
self.logger.warning("Test with display ID 123 not found in PractiTest")

# Error: Operation failures
self.logger.error(f"Failed to initialize PractiTest client: {e}")
self.logger.error(f"Error updating result for {nodeid}: {e}")
```

## Plugin Registration

The plugin is registered through global functions that delegate to the plugin instance:

```python
# Global plugin instance
_plugin_instance = PractiTestPlugin()

def pytest_configure(config):
    """Register the plugin with pytest."""
    _plugin_instance.pytest_configure(config)
    config.pluginmanager.register(_plugin_instance, "practitest")

# Delegate all hooks to the instance
def pytest_collection_modifyitems(config, items):
    _plugin_instance.pytest_collection_modifyitems(config, items)

def pytest_sessionstart(session):
    _plugin_instance.pytest_sessionstart(session)

# ... etc for all hooks
```

## Integration Points

### Command Line Interface

The plugin adds the `--practitest` flag via `conftest.py`:

```python
def pytest_addoption(parser):
    parser.addoption(
        "--practitest", 
        action="store_true", 
        default=False, 
        help="Enable PractiTest integration"
    )
```

### Test Marker Registration

The `practitestid` marker should be registered in `pytest.ini`:

```ini
[tool:pytest]
markers =
    practitestid: Mark test for PractiTest integration with display ID
```

### Environment Integration

The plugin integrates with the existing environment system:

```python
# Loads from .env file automatically
load_dotenv()

# Uses same environment variable pattern
PRACTITEST_EMAIL = os.getenv("PRACTITEST_EMAIL")
```

## Performance Considerations

### Batch Operations

The plugin performs operations in batches where possible:
- Single test set creation per session
- Bulk result reporting at session end
- Minimal API calls during test execution

### Network Optimization

- Results are cached and reported once at the end
- No API calls during individual test execution
- Connection reuse through requests session

### Memory Usage

- Minimal state storage (only IDs and basic result data)
- Results cleaned up after reporting
- No large object retention between tests

## Custom Hook Usage

### Adding Custom Metadata

You can extend the plugin to add custom metadata:

```python
def pytest_sessionstart(self, session):
    # Get additional metadata
    git_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    
    # Include in test set description
    description = f"Automated test execution | Commit: {git_commit}"
```

### Custom Result Processing

Extend result processing for additional data:

```python
def pytest_runtest_makereport(self, item, call):
    if call.when == "call":
        # Add custom metadata
        custom_data = {
            "environment": os.getenv("TEST_ENV"),
            "browser": getattr(item, 'browser', 'N/A'),
            "test_category": item.get_closest_marker("category")
        }
        
        # Include in notes
        notes = f"Standard notes... | Metadata: {custom_data}"
```

This architecture provides a robust, non-intrusive integration that enhances test reporting without interfering with normal test execution.