# Product Owner Guide: Building Test Cases with AI Agents

## Overview

This guide shows product owners how to collaborate with AI agents to create comprehensive test cases for the Mimic API test automation framework. By providing requirements in structured formats, you can leverage AI to generate thorough test coverage that validates your product features.

## Available AI Agents

### 🔍 **test-gap-analyzer Agent**
- **Purpose:** Analyzes your requirements and identifies missing test coverage
- **Input:** Product requirements, user stories, scenarios
- **Output:** Comprehensive test plans and gap analysis

### 🧪 **pytest-test-developer Agent**  
- **Purpose:** Implements actual test code based on test plans
- **Input:** Test plans, OpenAPI specifications
- **Output:** Working pytest test cases

## How to Work with Agents

### Step 1: Provide Requirements to test-gap-analyzer

The agent accepts requirements in multiple formats:

#### **Format 1: Given-When-Then Scenarios**
```gherkin
Feature: Node Configuration Management
  Scenario: Assign configuration to active node
    Given: A tenant has an active node
    And: A valid configuration exists
    When: Admin assigns the configuration to the node
    Then: The node should receive the configuration
    And: The node status should reflect the new config
    And: The configuration assignment should be logged
```

#### **Format 2: User Stories**
```
As a tenant administrator
I want to manage node operational states
So that I can control when nodes are actively monitoring

Acceptance Criteria:
- Admin can set node to active state
- Admin can set node to idle state  
- State changes are reflected in real-time
- Invalid state transitions are rejected
- State changes generate audit events
```

#### **Format 3: Feature Requirements**
```
Requirement: Subtenant Management
- Create subtenants with name and description
- Retrieve subtenant details by ID
- List all subtenants for a tenant
- Update subtenant information
- Delete subtenants (with proper cleanup)
- Validate unique naming within tenant scope
```

### Step 2: Review Generated Test Plan

The test-gap-analyzer will provide:
- Current test coverage analysis
- Missing test scenarios
- Prioritized test plan
- Risk assessment
- Implementation recommendations

### Step 3: Generate Test Code with pytest-test-developer

The pytest-test-developer will create:
- Working pytest test functions
- Proper API assertions
- Error handling scenarios
- Integration with existing framework

## Real Examples from Current Framework

### Example 1: Node Management Feature

**Your Requirement:**
```
Feature: Node Lifecycle Management
User Story: As an admin, I want to control node states to manage system resources

Scenarios:
- Set node to active for monitoring
- Set node to idle to pause monitoring  
- Validate state transitions
- Handle concurrent state changes
```

**Current Implementation:** `tests/test_api_mp_endpoint.py:145-182`
```python
@pytest.mark.api
@pytest.mark.practitestid()
def test_node_set_active(base_url, session, test_constants):
    """Test POST request to set node operational state to active."""
    TENANT_ID = test_constants["TENANT_ID"]
    NODE_ID = test_constants["NODE_ID"]
    url = f"{base_url}/api/tenants/{TENANT_ID}/nodes/{NODE_ID}/operational-state"
    payload = {"requestedOperationalState": "active"}
    response = session.post(url, json=payload)
    
    if response.status_code == 409:
        print("Node is already active")
    else:
        assert 200 <= response.status_code < 300
    time.sleep(30)
```

**What Agents Would Add:**
- Validation of state before/after transition
- Error scenarios (invalid states, unauthorized access)
- Concurrent modification testing
- Audit trail verification

### Example 2: Subtenant CRUD Operations

**Your Requirement:**
```
Feature: Subtenant Management
As a tenant admin, I want to manage subtenants for organizational structure

Requirements:
- Create subtenant with validation
- Retrieve subtenant information
- Update subtenant details
- Delete subtenant with cleanup
- List all subtenants with filtering
```

**Current Implementation:** `tests/test_api_mp_endpoint.py:417-554`
```python
@pytest.mark.api
@pytest.mark.practitestid()
def test_subtenants_create_get_delete(base_url, session, test_constants):
    """Test POST to create a subtenant, GET to retrieve it, and DELETE to remove it."""
    TENANT_ID = test_constants["TENANT_ID"]
    
    # Create subtenant
    create_url = f"{base_url}/api/tenants/{TENANT_ID}/subtenants"
    subtenant_payload = {
        "name": f"Test Subtenant {int(time.time())}",
        "description": "Automated test subtenant for API validation"
    }
    create_response = session.post(create_url, json=subtenant_payload)
    assert create_response.status_code == 201
    
    # Validate and cleanup...
```

**What Agents Would Enhance:**
- Validation boundary testing (max name length, special characters)
- Duplicate name handling
- Permission-based access testing
- Bulk operations testing

### Example 3: Configuration Assignment

**Your Requirement:**
```
Feature: Configuration Management
As a system admin, I want to assign configurations to nodes for policy enforcement

Scenarios:
- Assign valid configuration to node
- Handle configuration conflicts
- Track configuration history
- Validate configuration before assignment
```

**Current Implementation:** `tests/test_api_mp_endpoint.py:125-142`
```python
@pytest.mark.api
def test_node_config_assign(base_url, session, test_constants):
    """Test POST request to assign a configuration to a node."""
    TENANT_ID = test_constants["TENANT_ID"]
    NODE_ID = test_constants["NODE_ID"]
    CONFIG_ID = test_constants["CONFIG_IDS"].get("e2e", "default-config-id")
    url = f"{base_url}/api/tenants/{TENANT_ID}/config/{CONFIG_ID}/assign"
    payload = {"configRevisionNumber": 1, "nodeIds": [NODE_ID]}
    response = session.post(url, json=payload)
    
    assert 200 <= response.status_code < 300
    time.sleep(20)
```

**What Agents Would Add:**
- Invalid configuration ID testing
- Configuration version conflict scenarios
- Multiple node assignment testing
- Configuration rollback scenarios

## How to Request New Test Cases

### Template for Agent Requests

```markdown
**Feature:** [Feature Name]

**Business Context:**
[Why this feature exists and its business value]

**User Stories:**
As a [user type]
I want [capability]
So that [benefit]

**Scenarios:**
Given [initial state]
When [action occurs]
Then [expected outcome]
And [additional validations]

**Edge Cases to Consider:**
- [Edge case 1]
- [Edge case 2]
- [Error conditions]

**Current Test Coverage:**
[Reference existing test file if applicable]

**Priority:** High/Medium/Low
**Risk Level:** Critical/High/Medium/Low
```

### Example Request

```markdown
**Feature:** Alert Management System

**Business Context:**
Users need to be notified when security events occur in their environment. The alert system should provide real-time notifications with proper escalation paths.

**User Stories:**
As a security administrator
I want to configure alert rules for different event types
So that I can respond quickly to security incidents

**Scenarios:**
Given a tenant has configured alert rules
When a security event matching the rule occurs
Then an alert should be generated
And the alert should be sent to configured recipients
And the alert should be stored for audit purposes

**Edge Cases to Consider:**
- Alert flooding (too many alerts)
- Invalid recipient configurations
- Network failures during alert delivery
- Duplicate event processing

**Current Test Coverage:**
No existing test coverage identified

**Priority:** High
**Risk Level:** Critical
```

## Agent Collaboration Workflow

1. **Submit Requirements** → Use template above to describe your feature
2. **Gap Analysis** → test-gap-analyzer identifies missing tests and creates plan
3. **Review Plan** → Validate the proposed test scenarios match your expectations
4. **Generate Tests** → pytest-test-developer creates working test code
5. **Review & Integrate** → Review generated tests and integrate into framework

## Best Practices

### ✅ **Do This:**
- Provide clear business context
- Include edge cases and error scenarios
- Reference existing test patterns when possible
- Specify priority and risk levels
- Include acceptance criteria

### ❌ **Avoid This:**
- Vague requirements without context
- Technical implementation details (let agents decide)
- Assumptions about existing test coverage
- Mixing multiple unrelated features

## Framework Integration

The agents understand your existing framework:
- **pytest structure** with fixtures and markers
- **PractiTest integration** with `@pytest.mark.practitestid()`
- **Multi-environment support** (QA, DEV, STAGING, PROD)
- **Session management** with secure cookies
- **Test constants** and configuration patterns

Generated tests will seamlessly integrate with your current:
- `conftest.py` fixtures
- Environment configuration (`.env` file)
- Test utilities in `tests/utils.py`
- Existing test patterns and conventions

## Getting Started

To request new test cases:

1. **Choose your feature** to test
2. **Fill out the request template** with your requirements
3. **Submit to test-gap-analyzer** for analysis
4. **Review the generated test plan**
5. **Use pytest-test-developer** to implement tests
6. **Integrate into your test suite**

The agents will ensure your test cases follow established patterns while providing comprehensive coverage for your product requirements.