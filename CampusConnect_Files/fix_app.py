# Fix app.py to remove local host
with open('app.py', 'r') as f:
    content = f.read()

# Find and replace
old_text = '''print(f"\\nLocal access:  http://localhost:5000")
    print(f"\\nNetwork access: http://{local_ip}:5000")'''

new_text = '''print(f"\\nNetwork access: http://{local_ip}:5000")'''

content = content.replace(old_text, new_text)

with open('app.py', 'w') as f:
    f.write(content)

print("Done!")

