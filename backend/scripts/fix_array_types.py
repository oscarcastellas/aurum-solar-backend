#!/usr/bin/env python3
"""
Quick script to fix all ARRAY type issues in models
"""

import os
import re

def fix_file(file_path):
    """Fix ARRAY types in a file"""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace ARRAY imports
    content = re.sub(
        r'from sqlalchemy\.dialects\.postgresql import UUID, ARRAY',
        'from sqlalchemy.dialects.postgresql import UUID, ARRAY\nfrom app.core.db_types import UUIDType, ArrayStringType, ArrayUUIDType, get_uuid_default',
        content
    )
    
    # Replace ARRAY(String) with ArrayStringType
    content = re.sub(r'ARRAY\(String\)', 'ArrayStringType', content)
    
    # Replace ARRAY(UUID) with ArrayUUIDType
    content = re.sub(r'ARRAY\(UUID\)', 'ArrayUUIDType', content)
    
    # Replace UUID imports and usage
    content = re.sub(r'UUID\(as_uuid=True\)', 'UUIDType', content)
    content = re.sub(r'default=uuid\.uuid4', 'default=get_uuid_default', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")

# Fix all model files
model_files = [
    'app/models/auth.py',
    'app/models/ai_models.py',
    'app/models/analytics.py',
    'app/models/nyc_data.py'
]

for model_file in model_files:
    if os.path.exists(model_file):
        fix_file(model_file)
        print(f"Fixed {model_file}")

print("🎉 All ARRAY type issues fixed!")
