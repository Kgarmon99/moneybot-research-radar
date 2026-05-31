import re
with open("build.py", "r") as f:
    content = f.read()

# Enhance card CSS
old_card_css = """.card { border: 1px solid var(--border); padding: 24px; margin-bottom: 20px; border-radius: 6px; background-color: #050505; transition: all 0.2s; cursor: pointer; position: relative;}
        .card:hover { border-color: #666; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255,255,255,0.05);}"""

new_card_css = """.card { border: 1px solid var(--border); padding: 24px; margin-bottom: 20px; border-radius: 6px; background-color: #050505; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); cursor: pointer; position: relative;}
        .card:hover { border-color: #888; transform: translateY(-3px); box-shadow: 0 10px 30px rgba(255,255,255,0.08); background-color: #0a0a0a;}"""
        
content = content.replace(old_card_css, new_card_css)

with open("build.py", "w") as f:
    f.write(content)

print("Patched CSS")
