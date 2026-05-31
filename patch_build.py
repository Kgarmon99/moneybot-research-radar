import re
import os

with open("build.py", "r") as f:
    content = f.read()

# Add re to imports if not there
if "import re" not in content:
    content = content.replace("import os", "import os\nimport re")

# 1. Add preview extraction logic
extraction_logic = """
            filename = os.path.basename(path)
            
            # Extract preview
            preview = ""
            match = re.search(r'## Bottom Line\\s*(.*?)(?=\\n##|\\Z)', body, re.DOTALL | re.IGNORECASE)
            if match:
                preview = match.group(1).strip()[:180] + "..."
            else:
                lines = [line.strip() for line in body.split('\\n') if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('**Date')]
                if lines:
                    preview = lines[0][:180] + "..."
            fm['preview'] = preview
"""
content = content.replace("            filename = os.path.basename(path)", extraction_logic)

# 2. Update the HTML in build.py for the library tab
old_html = """                    <div class="card item-card">
                        <div class="meta">{{ brief.date }} &nbsp;|&nbsp; {{ brief.source_quality }}</div>
                        <h3 style="margin: 0;"><a href="brief/{{ brief.html_filename }}">{{ brief.title }}</a></h3>
                        {% if brief.tags %}
                        <div class="tags">
                            {% for tag in brief.tags %}<span>{{ tag }}</span>{% endfor %}
                        </div>
                        {% endif %}
                    </div>"""

new_html = """                    <a href="brief/{{ brief.html_filename }}" style="display: block; text-decoration: none;">
                        <div class="card item-card">
                            <div class="meta" style="display: flex; justify-content: space-between;">
                                <span>{{ brief.date }} &nbsp;|&nbsp; {{ brief.source_quality }}</span>
                                <span style="color: var(--fg); font-weight: bold;">&rarr;</span>
                            </div>
                            <h3 style="margin: 10px 0 15px 0; font-size: 1.4rem;">{{ brief.title }}</h3>
                            <p style="color: #aaa; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;">
                                {{ brief.preview }}
                            </p>
                            {% if brief.tags %}
                            <div class="tags">
                                {% for tag in brief.tags %}<span style="background: #111; border: 1px solid #333; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em;">{{ tag }}</span>{% endfor %}
                            </div>
                            {% endif %}
                        </div>
                    </a>"""

content = content.replace(old_html, new_html)

with open("build.py", "w") as f:
    f.write(content)

print("Patched build.py")
