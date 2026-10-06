import re
with open('tests/test_ui_smoke.py', 'r') as f:
    content = f.read()

matches = list(re.finditer(r'at\.get\("tabs"\)', content))
for m in matches:
    line_num = content[:m.start()].count('\n') + 1
    line = content[m.start():m.end()+50].split('\n')[0]
    print(f'Line {line_num}: {line}')