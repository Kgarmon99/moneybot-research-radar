with open("build.py", "r") as f:
    content = f.read()

old_html = """                    <a href="brief/{{ brief.html_filename }}" style="display: block; text-decoration: none;">
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

new_html = """                    <div class="card item-card" onclick="window.location.href='brief/{{ brief.html_filename }}'" style="cursor: pointer;">
                        <div class="meta" style="display: flex; justify-content: space-between;">
                            <span>{{ brief.date }} &nbsp;|&nbsp; {{ brief.source_quality }}</span>
                            <span style="color: var(--fg); font-weight: bold;">&rarr;</span>
                        </div>
                        <h3 style="margin: 10px 0 15px 0; font-size: 1.4rem;"><a href="brief/{{ brief.html_filename }}" style="text-decoration: none;">{{ brief.title }}</a></h3>
                        <p style="color: #aaa; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px;">
                            {{ brief.preview }}
                        </p>
                        {% if brief.tags %}
                        <div class="tags">
                            {% for tag in brief.tags %}<span style="background: #111; border: 1px solid #333; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em;">{{ tag }}</span>{% endfor %}
                        </div>
                        {% endif %}
                    </div>"""

content = content.replace(old_html, new_html)

with open("build.py", "w") as f:
    f.write(content)

print("Fixed HTML wrapping")
