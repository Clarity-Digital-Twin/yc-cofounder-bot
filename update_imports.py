#!/usr/bin/env python3
"""Script to update all imports after infrastructure reorganization."""

import os
import re
from pathlib import Path

# Mapping of old imports to new imports
IMPORT_MAPPINGS = {
    # Browser imports
    'from yc_matcher.infrastructure.browser.playwright_async': 'from yc_matcher.infrastructure.browser.playwright_async',
    'from yc_matcher.infrastructure.browser.playwright_sync': 'from yc_matcher.infrastructure.browser.playwright_sync',
    'from yc_matcher.infrastructure.browser.openai_cua': 'from yc_matcher.infrastructure.browser.openai_cua',
    'from yc_matcher.infrastructure.browser.observable': 'from yc_matcher.infrastructure.browser.observable',
    'from yc_matcher.infrastructure.browser.debug': 'from yc_matcher.infrastructure.browser.debug',
    'from yc_matcher.infrastructure.browser.helpers': 'from yc_matcher.infrastructure.browser.helpers',
    'from yc_matcher.infrastructure.browser.async_loop_runner': 'from yc_matcher.infrastructure.browser.async_loop_runner',
    
    # Persistence imports
    'from yc_matcher.infrastructure.persistence.sqlite_quota': 'from yc_matcher.infrastructure.persistence.sqlite_quota',
    'from yc_matcher.infrastructure.persistence.sqlite_progress': 'from yc_matcher.infrastructure.persistence.sqlite_progress',
    'from yc_matcher.infrastructure.persistence.sqlite_repo': 'from yc_matcher.infrastructure.persistence.sqlite_repo',
    'from yc_matcher.infrastructure.persistence.storage': 'from yc_matcher.infrastructure.persistence.storage',
    
    # Logging imports
    'from yc_matcher.infrastructure.logging.jsonl_logger': 'from yc_matcher.infrastructure.logging.jsonl_logger',
    'from yc_matcher.infrastructure.logging.stamped_logger': 'from yc_matcher.infrastructure.logging.stamped_logger',
    'from yc_matcher.infrastructure.logging.pipeline_observer': 'from yc_matcher.infrastructure.logging.pipeline_observer',
    
    # AI imports
    'from yc_matcher.infrastructure.ai.openai_decision': 'from yc_matcher.infrastructure.ai.openai_decision',
    'from yc_matcher.infrastructure.ai.local_decision': 'from yc_matcher.infrastructure.ai.local_decision',
    'from yc_matcher.infrastructure.ai.model_resolver': 'from yc_matcher.infrastructure.ai.model_resolver',
    
    # Control imports
    'from yc_matcher.infrastructure.control.stop_flag': 'from yc_matcher.infrastructure.control.stop_flag',
    'from yc_matcher.infrastructure.control.quota': 'from yc_matcher.infrastructure.control.quota',
    'from yc_matcher.infrastructure.control.error_recovery': 'from yc_matcher.infrastructure.control.error_recovery',
    
    # Utils imports
    'from yc_matcher.infrastructure.utils.time_utils': 'from yc_matcher.infrastructure.utils.time_utils',
    'from yc_matcher.infrastructure.utils.normalize': 'from yc_matcher.infrastructure.utils.normalize',
    'from yc_matcher.infrastructure.utils.templates': 'from yc_matcher.infrastructure.utils.templates',
    'from yc_matcher.infrastructure.utils.template_loader': 'from yc_matcher.infrastructure.utils.template_loader',
    'from yc_matcher.infrastructure.utils.preflight_check': 'from yc_matcher.infrastructure.utils.preflight_check',
    
    # Relative imports within infrastructure files
    'from .playwright_async': 'from .playwright_async',
    'from .playwright_sync': 'from .playwright_sync',
    'from .openai_cua': 'from .openai_cua',
    'from .observable': 'from .observable',
    'from .debug': 'from .debug',
    'from .helpers': 'from .helpers',
    'from ..browser.async_loop_runner': 'from ..browser.async_loop_runner',
    
    'from ..persistence.sqlite_quota': 'from ..persistence.sqlite_quota',
    'from ..persistence.sqlite_progress': 'from ..persistence.sqlite_progress',
    'from ..persistence.sqlite_repo': 'from ..persistence.sqlite_repo',
    'from ..persistence.storage': 'from ..persistence.storage',
    
    'from ..logging.jsonl_logger': 'from ..logging.jsonl_logger',
    'from ..logging.stamped_logger': 'from ..logging.stamped_logger',
    'from ..logging.pipeline_observer': 'from ..logging.pipeline_observer',
    
    'from ..ai.openai_decision': 'from ..ai.openai_decision',
    'from ..ai.local_decision': 'from ..ai.local_decision',
    'from ..ai.model_resolver': 'from ..ai.model_resolver',
    
    'from ..control.stop_flag': 'from ..control.stop_flag',
    'from ..control.quota': 'from ..control.quota',
    'from ..control.error_recovery': 'from ..control.error_recovery',
    
    'from ..utils.time_utils': 'from ..utils.time_utils',
    'from ..utils.normalize': 'from ..utils.normalize',
    'from ..utils.templates': 'from ..utils.templates',
    'from ..utils.template_loader': 'from ..utils.template_loader',
    'from ..utils.preflight_check': 'from ..utils.preflight_check',
    
    # From .. imports for files in subdirs that need parent
    'from ..utils.time_utils': 'from ..utils.time_utils',
    'from ..utils.normalize': 'from ..utils.normalize',
}

def update_file(filepath: Path) -> bool:
    """Update imports in a single file."""
    try:
        content = filepath.read_text()
        original = content
        
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        if content != original:
            filepath.write_text(content)
            return True
        return False
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

def main():
    """Update all Python files in the project."""
    root = Path('/mnt/c/Users/JJ/Desktop/Clarity-Digital-Twin/yc-cofounder-bot')
    
    # Find all Python files
    py_files = list(root.glob('**/*.py'))
    
    updated_count = 0
    for py_file in py_files:
        if '.venv' in str(py_file) or '__pycache__' in str(py_file):
            continue
        
        if update_file(py_file):
            print(f"Updated: {py_file.relative_to(root)}")
            updated_count += 1
    
    print(f"\nTotal files updated: {updated_count}")
    
    # Create __init__.py files for new subdirectories
    subdirs = [
        'src/yc_matcher/infrastructure/browser',
        'src/yc_matcher/infrastructure/persistence',
        'src/yc_matcher/infrastructure/logging',
        'src/yc_matcher/infrastructure/ai',
        'src/yc_matcher/infrastructure/control',
        'src/yc_matcher/infrastructure/utils',
    ]
    
    for subdir in subdirs:
        init_file = root / subdir / '__init__.py'
        if not init_file.exists():
            init_file.write_text('"""Infrastructure submodule."""\n')
            print(f"Created: {init_file.relative_to(root)}")

if __name__ == '__main__':
    main()