# Fix app.py - remove local host
import re

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match the two print statements
pattern = r'print\(f"\\nLocal access:.*?"\)\s*print\(f"\\nNetwork access:'

replacement = 'print(f"\\nNetwork access:'

content = re.sub(pattern, replacement, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed!")

