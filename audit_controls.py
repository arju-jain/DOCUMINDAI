import re

html = open("frontend/index.html", encoding="utf-8").read()
js = open("frontend/script.js", encoding="utf-8").read()

# Find all interactive elements: <button>, <input>, <a role="button">, <select>, etc.
pattern = r'<([a-zA-Z0-9]+)[^>]*?(id=["\']([^"\']+)["\'])[^>]*?>'
matches = re.findall(pattern, html)

interactive_tags = {'button', 'input', 'a', 'select', 'textarea'}
audit_results = []

for tag, id_attr, elem_id in matches:
    # Check if element is interactive (button, input, nav-item, role="button", etc.)
    # Extract the full tag string for context
    tag_match = re.search(r'<[^>]*?id=["\']' + re.escape(elem_id) + r'["\'][^>]*?>', html)
    tag_str = tag_match.group(0) if tag_match else ""
    is_interactive = tag in interactive_tags or 'role="button"' in tag_str or 'btn' in tag_str or elem_id.startswith('btn') or elem_id.startswith('nav')
    if is_interactive:
        present_in_js = elem_id in js
        audit_results.append((elem_id, tag, tag_str, present_in_js))

print(f"Total Interactive Controls Found: {len(audit_results)}")
print(f"{'Element ID':<30} | {'Tag':<8} | {'In JS?':<8}")
print("-" * 55)
for elem_id, tag, tag_str, in_js in audit_results:
    print(f"{elem_id:<30} | {tag:<8} | {str(in_js):<8}")
