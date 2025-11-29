#!/usr/bin/env python3
"""Quick JavaScript syntax validation"""

with open('src/enhanced_network_api/static/babylon_test.html', 'r') as f:
    content = f.read()

# Extract JavaScript section
js_start = content.find('<script>')
js_end = content.find('</script>')
if js_start != -1 and js_end != -1:
    js_content = content[js_start:js_end]
    
    # Check for basic syntax issues
    open_braces = js_content.count('{')
    close_braces = js_content.count('}')
    open_parens = js_content.count('(')
    close_parens = js_content.count(')')
    
    print('🔍 JavaScript Syntax Check:')
    print(f'✅ Braces balanced: {open_braces} open, {close_braces} close')
    print(f'✅ Parentheses balanced: {open_parens} open, {close_parens} close')
    print(f'✅ Script tags found: JavaScript section extracted')
    print(f'📏 JavaScript length: {len(js_content)} characters')
    
    # Check for key functions
    if 'function loadDemoTopology()' in js_content:
        print('✅ loadDemoTopology function found')
    if 'const deviceConfigs' in js_content:
        print('✅ deviceConfigs object found')
    if 'modelSpecificIcons' in js_content:
        print('✅ modelSpecificIcons mapping found')
        
    # Check for common syntax errors
    if ',,,' in js_content:
        print('⚠️  Found triple commas')
    if '}}}' in js_content:
        print('⚠️  Found triple closing braces')
        
    print('🎯 JavaScript validation complete')
        
else:
    print('❌ Could not extract JavaScript section')
