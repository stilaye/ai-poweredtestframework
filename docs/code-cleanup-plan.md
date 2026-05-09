# Code Cleanup and Refactoring Plan

## 📋 COMPREHENSIVE CODE CLEANUP PLAN

### **Phase 1: Configuration & Constants Cleanup** (High Priority)
1. **Extract Configuration Constants**
   - Create `tests/config/constants.py` for all hardcoded values
   - Move timeouts (20s, 30s), default IDs, file paths
   - Centralize all environment-specific defaults

2. **Improve Environment Management**
   - Simplify `get_config_id()` to support all environments (currently hardcoded to QA)
   - Add proper UUID validation for config IDs
   - Create environment-specific test data classes

### **Phase 2: Authentication & Session Management** (High Priority)
1. **Extract Authentication Logic**
   - Create `tests/auth/auth_manager.py`
   - Move Secret Manager logic from conftest.py
   - Reduce 70-line `common_cookies()` function to 10-15 lines
   - Eliminate 3x duplicated fallback logic

2. **Simplify Session Management**
   - Consolidate session creation and configuration
   - Add proper retry mechanisms for auth failures

### **Phase 3: API Operations Consolidation** (Medium Priority)
1. **Create API Operation Classes**
   - `tests/api/node_operations.py` - Node state, config assignment, details
   - `tests/api/url_builder.py` - Centralize URL construction patterns
   - Eliminate 20+ duplicated API call patterns

2. **Standardize API Assertions**
   - Make `APIAssertions` usage consistent across all files
   - Remove scattered `assert response.status_code == 200` patterns
   - Add response validation utilities

### **Phase 4: Test Structure Optimization** (Medium Priority)
1. **Create Base Test Classes**
   - `tests/base/base_test.py` - Common setup/teardown
   - Auto-inject `tenant_id`, `node_id` from test_constants
   - Eliminate repeated variable extraction

2. **Consolidate Test Utilities**
   - Make existing utils (`wait_for_operation`, `handle_409_conflict`) usage consistent
   - Remove direct `time.sleep()` calls (replace with `wait_for_operation()`)
   - Standardize subprocess command execution

### **Phase 5: File Organization & Imports** (Low Priority)
1. **Reorganize File Structure**
   ```
   tests/
   ├── api/           # API operation classes
   ├── auth/          # Authentication utilities  
   ├── base/          # Base test classes
   ├── config/        # Configuration constants
   ├── fixtures/      # Custom pytest fixtures
   └── utils/         # General utilities
   ```

2. **Optimize Imports**
   - Remove unused imports in conftest.py
   - Create standardized import modules
   - Use local imports where appropriate

### **Phase 6: Error Handling & Logging** (Low Priority)
1. **Standardize Error Handling**
   - Replace generic `Exception` catches with specific exceptions
   - Add proper logging configuration
   - Create consistent error message formats

2. **Improve Debugging Support**
   - Enhance request/response logging
   - Add debug modes for different test types
   - Standardize print statements vs proper logging

## 📊 **Expected Impact**

### **Code Reduction:**
- **conftest.py**: ~40% reduction (340 → 200 lines)
- **Test files**: ~30% reduction through consolidation
- **Overall codebase**: ~35% reduction while improving maintainability

### **Maintainability Improvements:**
- ✅ Single source of truth for configurations
- ✅ Consistent API patterns across all tests  
- ✅ Proper separation of concerns
- ✅ Easier environment management
- ✅ Better error handling and debugging

### **Performance Benefits:**
- ⚡ Reduced session creation overhead
- ⚡ Optimized authentication flows
- ⚡ Better resource management

## 🎯 **Implementation Priority:**

**Phase 1 & 2** will provide the biggest impact (authentication simplification and configuration cleanup) and should be done first.

**Phase 3 & 4** will improve day-to-day development experience.

**Phase 5 & 6** are nice-to-have improvements for long-term maintainability.

## 📝 **Detailed Findings from Code Review**

### **conftest.py Issues:**
- Lines 133-179: Repetitive fallback logic in `common_cookies()` function (3x duplicated)
- Lines 76, 97, 128, 204: Repeated `get_env()` calls across fixtures
- Lines 114-183: 70-line authentication function mixing multiple concerns
- Lines 267-339: 73-line `setup_module()` with too many responsibilities
- Lines 309, 321: Hardcoded sleep times (20s, 30s)
- Line 110: Empty User-Agent header
- Lines 213-215: Hardcoded default IDs that should be configurable

### **Test File Duplication Patterns:**
- **API URL Construction**: Repeated patterns for building tenant/node URLs
- **Response Assertions**: 20+ instances of manual status code checking
- **Node State Management**: Duplicated operational state setting logic
- **ID Extraction**: Repeated `TENANT_ID = test_constants["TENANT_ID"]` patterns
- **Subprocess Commands**: Inconsistent subprocess execution patterns
- **Sleep Operations**: Direct `time.sleep()` instead of using existing `wait_for_operation()`

### **utils.py Opportunities:**
- `get_config_id()` hardcoded to QA environment only (line 114)
- Good utility functions exist but not consistently used across tests
- `APIAssertions` class available but not universally adopted
- Version detection functions could be optimized

## 🚀 **Next Steps**

To implement this cleanup plan:

1. **Start with Phase 1**: Extract configuration constants
2. **Move to Phase 2**: Simplify authentication logic  
3. **Continue with remaining phases** based on priority and impact

Each phase can be implemented incrementally without breaking existing functionality.