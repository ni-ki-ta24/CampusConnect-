# Simple fix
with open('app.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    if 'Local access' in line and 'localhost' in line:
        # Skip this line and the next one (Network access)
        skip_next = True
        new_lines.append('    print(f"\\nNetwork access: http://")' + '{local_ip}:5000")\n')
    else:
        new_lines.append(line)

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print("Done!")

