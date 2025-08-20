# Refactor Part 4: Validation - Testing & Deployment

## Overview

This document details Phase 4 of the refactoring: comprehensive testing, validation, and safe deployment of the CUA-aligned codebase.

## Goals

1. Create comprehensive test suite for CUA integration
2. Establish acceptance criteria
3. Define deployment strategy
4. Create rollback procedures

## Step 1: CUA Integration Tests

### File: `tests/integration/test_cua_browser.py`

```python
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser

class TestCUABrowserIntegration:
    """Integration tests for OpenAI CUA browser"""
    
    @pytest.fixture
    def cua_browser(self):
        """Create CUA browser with mocked agent"""
        with patch.dict('os.environ', {'CUA_MODEL': 'test-model'}):
            with patch('yc_matcher.infrastructure.openai_cua_browser.Agent') as MockAgent:
                mock_agent = Mock()
                MockAgent.return_value = mock_agent
                browser = OpenAICUABrowser()
                browser.agent = mock_agent
                yield browser
                
    @pytest.mark.asyncio
    async def test_browse_to_listing(self, cua_browser):
        """Test CUA navigates to YC listing"""
        cua_browser.agent.run.return_value = {
            'success': True,
            'page_title': 'YC Startup School'
        }
        
        await cua_browser.browse_to_listing()
        
        cua_browser.agent.run.assert_called_once()
        call_args = cua_browser.agent.run.call_args
        assert 'cofounder' in str(call_args).lower()
        
    @pytest.mark.asyncio
    async def test_extract_profiles(self, cua_browser):
        """Test CUA extracts profile list"""
        cua_browser.agent.run.return_value = {
            'profiles': [
                {'id': '1', 'name': 'Alice', 'title': 'Technical Co-founder'},
                {'id': '2', 'name': 'Bob', 'title': 'Business Co-founder'}
            ]
        }
        
        profiles = await cua_browser.extract_profile_list()
        
        assert len(profiles) == 2
        assert profiles[0]['name'] == 'Alice'
        
    @pytest.mark.asyncio
    async def test_cua_error_handling(self, cua_browser):
        """Test CUA handles errors gracefully"""
        cua_browser.agent.run.side_effect = Exception("CUA timeout")
        
        with pytest.raises(Exception) as exc_info:
            await cua_browser.browse_to_listing()
            
        assert "CUA timeout" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_fallback_to_playwright(self):
        """Test fallback from CUA to Playwright"""
        from yc_matcher.infrastructure.browser_fallback import BrowserWithFallback
        
        cua = AsyncMock()
        cua.browse_to_listing.side_effect = Exception("CUA unavailable")
        
        playwright = AsyncMock()
        playwright.browse_to_listing.return_value = None
        
        browser = BrowserWithFallback(primary=cua, fallback=playwright)
        
        await browser.browse_to_listing()
        
        # Should try CUA first, then fallback
        cua.browse_to_listing.assert_called_once()
        playwright.browse_to_listing.assert_called_once()
```

### File: `tests/e2e/test_autonomous_flow.py`

```python
import pytest
import asyncio
from yc_matcher.interface.di import Dependencies

class TestAutonomousE2E:
    """End-to-end tests for autonomous flow"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_autonomous_flow(self):
        """Test complete flow from 3 inputs to message sending"""
        
        # Setup
        deps = Dependencies()
        processor = deps.create_autonomous_processor()
        
        # Test data
        your_profile = "Python developer with 5 years experience"
        match_criteria = "Business co-founder with B2B sales"
        message_template = "Hi [Name], interested in your background..."
        
        # Execute
        result = await processor(
            your_profile=your_profile,
            match_criteria=match_criteria,
            message_template=message_template,
            limit=5
        )
        
        # Verify
        assert result.total_evaluated > 0
        assert result.total_evaluated <= 5
        assert all(r['profile'] is not None for r in result.results)
        
    @pytest.mark.e2e
    @pytest.mark.asyncio  
    async def test_stop_flag_integration(self, tmp_path):
        """Test STOP flag halts processing"""
        
        stop_file = tmp_path / "STOP"
        
        deps = Dependencies()
        processor = deps.create_autonomous_processor()
        
        # Start processing in background
        task = asyncio.create_task(
            processor(
                your_profile="Test",
                match_criteria="Test",
                message_template="Test",
                limit=100
            )
        )
        
        # Create STOP file after short delay
        await asyncio.sleep(2)
        stop_file.touch()
        
        # Wait for completion
        result = await task
        
        # Should have stopped early
        assert result.total_evaluated < 100
        assert "STOP" in result.termination_reason
```

## Step 2: Acceptance Test Suite

### File: `tests/acceptance/test_cua_acceptance.py`

```python
import pytest
from typing import Dict, Any

class TestCUAAcceptance:
    """Acceptance tests for CUA implementation"""
    
    @pytest.fixture
    def acceptance_criteria(self) -> Dict[str, Any]:
        """Define acceptance criteria"""
        return {
            'navigation': {
                'can_reach_yc_site': True,
                'can_find_listing_page': True,
                'can_open_profiles': True
            },
            'extraction': {
                'extracts_name': True,
                'extracts_skills': True,
                'extracts_location': True,
                'handles_missing_fields': True
            },
            'decision': {
                'advisor_mode_works': True,
                'rubric_mode_works': True,
                'hybrid_mode_works': True
            },
            'messaging': {
                'fills_message_box': True,
                'sends_successfully': True,
                'respects_limits': True
            },
            'safety': {
                'stop_flag_works': True,
                'quotas_enforced': True,
                'dedup_works': True
            }
        }
        
    def test_navigation_acceptance(self, cua_browser, acceptance_criteria):
        """Test CUA navigation meets acceptance criteria"""
        for criterion, expected in acceptance_criteria['navigation'].items():
            result = self._test_navigation_criterion(cua_browser, criterion)
            assert result == expected, f"Failed: {criterion}"
            
    def test_extraction_acceptance(self, cua_browser, acceptance_criteria):
        """Test profile extraction meets acceptance criteria"""
        for criterion, expected in acceptance_criteria['extraction'].items():
            result = self._test_extraction_criterion(cua_browser, criterion)
            assert result == expected, f"Failed: {criterion}"
            
    def test_decision_modes_acceptance(self, acceptance_criteria):
        """Test all decision modes meet acceptance criteria"""
        for criterion, expected in acceptance_criteria['decision'].items():
            result = self._test_decision_criterion(criterion)
            assert result == expected, f"Failed: {criterion}"
            
    def test_safety_features_acceptance(self, acceptance_criteria):
        """Test safety features meet acceptance criteria"""
        for criterion, expected in acceptance_criteria['safety'].items():
            result = self._test_safety_criterion(criterion)
            assert result == expected, f"Failed: {criterion}"
```

## Step 3: Performance Tests

### File: `tests/performance/test_cua_performance.py`

```python
import pytest
import time
import asyncio
from statistics import mean, stdev

class TestCUAPerformance:
    """Performance tests for CUA implementation"""
    
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_profile_processing_speed(self):
        """Test profile processing meets performance targets"""
        
        processor = create_test_processor()
        timings = []
        
        for _ in range(10):
            start = time.time()
            await processor.process_single_profile(test_profile())
            duration = time.time() - start
            timings.append(duration)
            
        avg_time = mean(timings)
        std_dev = stdev(timings)
        
        # Performance criteria
        assert avg_time < 5.0, f"Too slow: {avg_time:.2f}s average"
        assert std_dev < 2.0, f"Too variable: {std_dev:.2f}s std dev"
        
    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test system handles concurrent operations"""
        
        processor = create_test_processor()
        
        # Create multiple concurrent tasks
        tasks = [
            processor.process_single_profile(test_profile())
            for _ in range(5)
        ]
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        # Should process concurrently, not take 5x single time
        assert duration < 10.0, f"Concurrent processing too slow: {duration:.2f}s"
        assert all(r is not None for r in results)
        
    @pytest.mark.performance
    def test_memory_usage(self):
        """Test memory usage stays within bounds"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Process many profiles
        processor = create_test_processor()
        for _ in range(100):
            processor.process_single_profile(test_profile())
            
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Should not leak memory excessively
        assert memory_increase < 100, f"Memory leak detected: {memory_increase:.2f}MB increase"
```

## Step 4: Contract Tests

### File: `tests/contract/test_browser_contract.py`

```python
import pytest
from typing import Protocol

class TestBrowserContract:
    """Contract tests ensuring all browser implementations match interface"""
    
    @pytest.fixture(params=['cua', 'playwright'])
    def browser(self, request):
        """Parameterized fixture for all browser implementations"""
        if request.param == 'cua':
            return create_cua_browser()
        elif request.param == 'playwright':
            return create_playwright_browser()
            
    @pytest.mark.asyncio
    async def test_browser_contract(self, browser):
        """Test all browsers implement required methods"""
        
        # All browsers must implement these methods
        required_methods = [
            'start_session',
            'browse_to_listing',
            'extract_profile_list',
            'open_profile',
            'extract_full_profile',
            'send_message',
            'close_session'
        ]
        
        for method in required_methods:
            assert hasattr(browser, method), f"Missing method: {method}"
            assert callable(getattr(browser, method)), f"Not callable: {method}"
            
    @pytest.mark.asyncio
    async def test_browser_behavior_contract(self, browser):
        """Test all browsers behave consistently"""
        
        # Start session
        await browser.start_session("https://example.com")
        
        # Navigate
        await browser.browse_to_listing()
        
        # Extract profiles (should return list)
        profiles = await browser.extract_profile_list()
        assert isinstance(profiles, list)
        
        if profiles:
            # Open first profile
            await browser.open_profile(profiles[0]['id'])
            
            # Extract details (should return Profile object)
            profile = await browser.extract_full_profile()
            assert hasattr(profile, 'name')
            assert hasattr(profile, 'skills')
            
        # Close session
        await browser.close_session()
```

## Step 5: Deployment Validation

### File: `scripts/validate_deployment.py`

```python
#!/usr/bin/env python
"""
Deployment validation script
Run this before and after deployment to ensure system health
"""

import asyncio
import sys
from typing import Dict, Any

async def validate_deployment() -> Dict[str, Any]:
    """Validate deployment readiness"""
    
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Check 1: Environment variables
    print("Checking environment variables...")
    env_vars = [
        'OPENAI_API_KEY',
        'CUA_MODEL',
        'OPENAI_DECISION_MODEL',
        'USE_CUA_PRIMARY',
        'USE_THREE_INPUT_UI',
        'USE_DECISION_MODES'
    ]
    
    import os
    for var in env_vars:
        if os.getenv(var):
            results['passed'].append(f"✅ {var} is set")
        else:
            results['failed'].append(f"❌ {var} is not set")
            
    # Check 2: CUA connectivity
    print("Checking CUA connectivity...")
    try:
        from yc_matcher.infrastructure.openai_cua_browser import OpenAICUABrowser
        browser = OpenAICUABrowser()
        await browser.start_session("https://example.com")
        await browser.close_session()
        results['passed'].append("✅ CUA browser initializes")
    except Exception as e:
        results['failed'].append(f"❌ CUA browser failed: {e}")
        
    # Check 3: Database connectivity
    print("Checking database...")
    try:
        from yc_matcher.infrastructure.sqlite_quota import SqliteQuotaService
        quota = SqliteQuotaService()
        quota.can_send()
        results['passed'].append("✅ Database accessible")
    except Exception as e:
        results['failed'].append(f"❌ Database failed: {e}")
        
    # Check 4: Feature flags
    print("Checking feature flags...")
    from yc_matcher.config import FeatureFlags
    
    if FeatureFlags.USE_CUA_PRIMARY:
        results['warnings'].append("⚠️ CUA is PRIMARY - ensure tested")
    else:
        results['passed'].append("✅ CUA not primary (safe)")
        
    if FeatureFlags.USE_THREE_INPUT_UI:
        results['warnings'].append("⚠️ New UI enabled - monitor closely")
    else:
        results['passed'].append("✅ Legacy UI active (safe)")
        
    # Check 5: Run acceptance tests
    print("Running acceptance tests...")
    import subprocess
    result = subprocess.run(
        ["pytest", "tests/acceptance", "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        results['passed'].append("✅ Acceptance tests pass")
    else:
        results['failed'].append("❌ Acceptance tests failed")
        
    return results

async def main():
    """Main validation runner"""
    
    print("=" * 50)
    print("DEPLOYMENT VALIDATION")
    print("=" * 50)
    
    results = await validate_deployment()
    
    print("\n📊 RESULTS:")
    print("-" * 30)
    
    for passed in results['passed']:
        print(passed)
        
    for warning in results['warnings']:
        print(warning)
        
    for failed in results['failed']:
        print(failed)
        
    print("-" * 30)
    
    if results['failed']:
        print("\n❌ DEPLOYMENT BLOCKED - Fix failures above")
        sys.exit(1)
    elif results['warnings']:
        print("\n⚠️ DEPLOYMENT ALLOWED - Monitor warnings")
        sys.exit(0)
    else:
        print("\n✅ DEPLOYMENT READY - All checks passed")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 6: Rollback Procedures

### File: `scripts/rollback.sh`

```bash
#!/bin/bash
# Emergency rollback script

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# Step 1: Disable feature flags immediately
echo "Disabling feature flags..."
export USE_CUA_PRIMARY=false
export USE_THREE_INPUT_UI=false
export USE_DECISION_MODES=false

# Step 2: Create STOP file to halt processing
echo "Creating STOP flag..."
touch STOP

# Step 3: Restart application with safe config
echo "Restarting with safe configuration..."
supervisorctl restart yc-matcher

# Step 4: Verify rollback
echo "Verifying rollback..."
python scripts/validate_deployment.py

echo "✅ Rollback complete"
```

### File: `docs/ROLLBACK_PROCEDURES.md`

```markdown
# Rollback Procedures

## Immediate Actions (< 1 minute)

1. **Disable feature flags**:
   ```bash
   export USE_CUA_PRIMARY=false
   export USE_THREE_INPUT_UI=false
   ```

2. **Create STOP file**:
   ```bash
   touch STOP
   ```

3. **Restart application**:
   ```bash
   supervisorctl restart yc-matcher
   ```

## If Issues Persist (< 5 minutes)

1. **Revert to previous version**:
   ```bash
   git checkout [previous-version-tag]
   pip install -r requirements.txt
   supervisorctl restart yc-matcher
   ```

2. **Restore database backup**:
   ```bash
   cp backups/quota.db.backup data/quota.db
   ```

## Post-Rollback

1. **Notify team**:
   - Send alert to #engineering
   - Create incident report

2. **Collect diagnostics**:
   ```bash
   tar -czf diagnostics.tar.gz logs/ data/
   ```

3. **Schedule post-mortem**
```

## Deployment Checklist

### Pre-Deployment
- [ ] All tests pass: `make test`
- [ ] Validation script passes: `python scripts/validate_deployment.py`
- [ ] Database backed up
- [ ] Feature flags configured correctly
- [ ] Team notified

### Deployment Steps
1. [ ] Deploy with flags disabled
2. [ ] Run validation script
3. [ ] Enable for internal testing
4. [ ] Monitor metrics for 1 hour
5. [ ] Gradual rollout (10% → 50% → 100%)

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Collect user feedback
- [ ] Document any issues

## Success Metrics

### Technical Metrics
- Error rate < 1%
- P95 latency < 5s
- CUA success rate > 95%
- Zero data loss

### Business Metrics
- Message send rate maintained or improved
- User satisfaction maintained or improved
- Support tickets not increased

## Monitoring Dashboard

```python
# monitoring/dashboard.py
class DeploymentMonitor:
    """Real-time deployment monitoring"""
    
    def __init__(self):
        self.metrics = {
            'errors': [],
            'latencies': [],
            'success_rate': 0,
            'active_users': 0
        }
        
    def check_health(self):
        """Check system health"""
        if self.error_rate > 0.05:
            self.alert("High error rate detected")
            
        if self.p95_latency > 10:
            self.alert("High latency detected")
            
        if self.success_rate < 0.9:
            self.alert("Low success rate")
```

## Conclusion

This comprehensive validation suite ensures:
1. CUA integration works correctly
2. All decision modes function properly
3. Safety features remain active
4. Performance meets requirements
5. Rollback procedures are ready

With these four refactoring documents, the codebase can be systematically transformed from the current paste-based workflow to the documented 3-input autonomous CUA architecture.