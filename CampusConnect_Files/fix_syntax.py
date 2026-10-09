# Fix the syntax error in app.py
with open('app.py', 'r') as f:
    content = f.read()

# Fix the broken line
content = content.replace('print(f"\\nNetwork access: http://"){local_ip}:5000")', 'print(f"\\nNetwork access: http://{local_ip}:5000")')

with open('app.py', 'w') as f:
    f.write(content)

print("Fixed!")

