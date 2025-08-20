# Section 4: Use Cases/Application Flow

## Current File: `src/yc_matcher/application/use_cases.py`

### What EXISTS Now:

#### 1. `EvaluateProfile` (lines 24-31)
- Takes Profile + Criteria
- Runs decision adapter
- Renders message template
- Returns decision + draft

#### 2. `SendMessage` (lines 35-67)
- Checks quota
- Uses browser to send
- Has retry logic
- Verifies sent

#### 3. `ProcessCandidate` (lines 71-100+)
- **MAIN FLOW**: URL → Open → Click → Read → Evaluate → Send
- Has STOP flag checking
- Has seen/dedup logic
- Logs everything

### What's WRONG:
1. **REQUIRES URL**: Expects manual URL input (line 80)
2. **NO AUTONOMOUS**: Can't browse listing automatically
3. **NO BATCH**: Processes one profile at a time
4. **NO 3-INPUT**: Expects paste, not Your Profile input

### What NEW File Needed:

```python
# NEW FILE: src/yc_matcher/application/autonomous_flow.py

from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class AutonomousFlow:
    """CUA-driven autonomous browsing and matching"""
    
    browser: BrowserPort  # Will be CUA browser
    evaluate: EvaluateProfile  # Reuse existing
    send: SendMessage  # Reuse existing
    seen: SeenRepo  # Reuse existing
    logger: LoggerPort  # Reuse existing
    stop: StopController  # Reuse existing
    
    async def run(
        self,
        your_profile: str,  # NEW: Your profile input
        criteria: str,      # Match criteria
        template: str,      # Message template
        mode: str,          # advisor|rubric|hybrid
        limit: int = 20     # Max profiles
    ) -> Dict[str, Any]:
        """
        Autonomous flow:
        1. Browse to YC listing
        2. Extract all visible profiles
        3. Evaluate each against criteria
        4. Send messages based on mode
        """
        
        # 1. Navigate to listing
        await self.browser.navigate_to_listing()
        
        # 2. Extract profile list
        profile_list = await self.browser.extract_profile_list()
        
        results = []
        sent_count = 0
        
        for profile_data in profile_list[:limit]:
            # Check stop
            if self.stop.is_stopped():
                break
                
            # Open individual profile
            await self.browser.open_profile(profile_data['id'])
            
            # Extract full text
            text = await self.browser.read_profile_text()
            profile = Profile(raw_text=text)
            
            # Check seen
            phash = hash_profile_text(text)
            if self.seen.is_seen(phash):
                continue
            self.seen.mark_seen(phash)
            
            # Evaluate (reuse existing)
            criteria_obj = Criteria(text=criteria)
            decision = self.evaluate(profile, criteria_obj)
            
            # Auto-send logic based on mode
            should_send = self._should_auto_send(decision, mode)
            
            if should_send and decision['decision'] == 'YES':
                # Send (reuse existing)
                success = self.send(decision['draft'], limit)
                if success:
                    sent_count += 1
                    
            results.append({
                'profile': profile,
                'decision': decision,
                'sent': should_send
            })
            
        return {
            'total_evaluated': len(results),
            'total_sent': sent_count,
            'results': results
        }
    
    def _should_auto_send(self, decision: Dict, mode: str) -> bool:
        """Determine if should auto-send based on mode"""
        if mode == "advisor":
            return False  # Never auto-send
        elif mode == "rubric":
            return True  # Always auto-send if YES
        elif mode == "hybrid":
            # Check confidence or other criteria
            confidence = decision.get('confidence', 0)
            return confidence > 0.7
        return False
```

### Reusable Components:
- ✅ `EvaluateProfile` - Can reuse as-is
- ✅ `SendMessage` - Can reuse as-is  
- ✅ `SeenRepo` - Can reuse for dedup
- ✅ `StopController` - Can reuse for abort
- ✅ `LoggerPort` - Can reuse for logging

### Test Coverage:
- `test_use_cases.py` ✅ EXISTS (for current ones)
- `test_process_candidate.py` ✅ EXISTS
- **Missing**: Tests for autonomous flow

### Environment Variables:
- `AUTO_BROWSE_LIMIT` - Max profiles to process
- `SEND_DELAY_MS` - ✅ Already used (line 46)
- `YC_LISTING_URL` - Base URL for listing

### Effort Estimate:
- **New file**: ~150 lines
- **Time**: 2-3 hours
- **Risk**: Low (reuses existing components)
- **Testing**: Add integration tests