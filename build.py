import os
import glob
import yaml
import markdown
import feedparser
from jinja2 import Template
import ssl
import shutil

# Bypass SSL checks for scraping RSS feeds
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MoneyBot Research Radar</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #000000; --fg: #FFFFFF; --border: #333333; --accent: #888888; }
        body { background-color: var(--bg); color: var(--fg); font-family: 'Space Grotesk', sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; }
        .container { max-width: 900px; margin: 0 auto; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.03em; }
        h1 { font-size: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 40px; }
        h2 { font-size: 1.2rem; margin-top: 60px; color: var(--accent); text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid #111; padding-bottom: 10px;}
        a { color: var(--fg); text-decoration: none; border-bottom: 1px solid var(--border); transition: border-color 0.2s;}
        a:hover { border-bottom: 1px solid var(--fg); }
        .card { border: 1px solid var(--border); padding: 24px; margin-bottom: 20px; border-radius: 4px; background-color: #050505; transition: border-color 0.2s; }
        .card:hover { border-color: #666; }
        .meta { font-size: 0.85rem; color: var(--accent); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
        .tags { margin-top: 15px; }
        .tags span { background: #111; border: 1px solid var(--border); padding: 4px 10px; font-size: 0.75rem; border-radius: 12px; margin-right: 8px; text-transform: lowercase; }
        .header-bar { display: flex; justify-content: space-between; align-items: baseline; }
        .live-pulse { display: inline-block; width: 8px; height: 8px; background-color: #00ff00; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #00ff00; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>MONEYBOT RESEARCH RADAR</h1>
            <span class="meta"><span class="live-pulse"></span>AUTO-UPDATED DAILY</span>
        </div>
        <p style="color: var(--accent); max-width: 600px; margin-top: -20px;">
            A centralized dashboard tracking the latest empirical data and policy changes regarding financial literacy, household finance, and the "Fragility Tax".
        </p>
        <h2>Curated Briefs & Memos</h2>
        {% if briefs %}
            {% for brief in briefs %}
            <div class="card">
                <div class="meta">{{ brief.date }} &nbsp;|&nbsp; {{ brief.source_quality }}</div>
                <h3 style="margin: 0;"><a href="brief/{{ brief.html_filename }}">{{ brief.title }}</a></h3>
                {% if brief.tags %}
                <div class="tags">
                    {% for tag in brief.tags %}<span>{{ tag }}</span>{% endfor %}
                </div>
                {% endif %}
            </div>
            {% endfor %}
        {% else %}
            <p>No local research briefs found.</p>
        {% endif %}
        <h2>Live Feed (NBER Working Papers)</h2>
        {% for item in feed_items %}
        <div class="card">
            <div class="meta">{{ item.source }} &nbsp;|&nbsp; {{ item.date }}</div>
            <h3 style="margin: 0; font-size: 1.1rem;"><a href="{{ item.link }}" target="_blank">{{ item.title }}</a></h3>
            <p style="color: var(--accent); font-size: 0.9rem; margin-top: 10px;">{{ item.summary[:200] }}...</p>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

BRIEF_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Research Radar</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #000000; --fg: #FFFFFF; --border: #333333; --accent: #888888; }
        body { background-color: var(--bg); color: var(--fg); font-family: 'Space Grotesk', sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.03em; }
        h1 { font-size: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 20px; margin-top: 40px;}
        h2 { font-size: 1.4rem; margin-top: 40px; color: var(--fg); border-bottom: 1px solid var(--border); padding-bottom: 5px;}
        a { color: var(--fg); text-decoration: none; border-bottom: 1px solid var(--border); transition: border-color 0.2s;}
        a:hover { border-bottom: 1px solid var(--fg); }
        .back-link { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); }
        table { width: 100%; border-collapse: collapse; margin-bottom: 24px; margin-top: 24px;}
        th, td { border: 1px solid var(--border); padding: 12px; text-align: left; font-size: 0.9rem; }
        th { color: var(--accent); font-weight: normal; text-transform: uppercase; letter-spacing: 0.05em;}
        code { background: #111; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; }
        pre { background: #111; padding: 15px; border-radius: 4px; overflow-x: auto; border: 1px solid var(--border); }
        blockquote { border-left: 3px solid var(--border); margin: 0; padding-left: 15px; color: var(--accent); font-style: italic;}
        ul, ol { padding-left: 20px; }
        li { margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">&larr; Back to Radar</a>
        {{ content|safe }}
    </div>
</body>
</html>
"""

def build():
    # Clean and setup output dir
    if os.path.exists('public'):
        shutil.rmtree('public')
    os.makedirs('public/brief', exist_ok=True)
    
    briefs = []
    for path in glob.glob('briefs/*.md'):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            fm = {'title': os.path.basename(path).replace('.md', ''), 'date': '', 'tags': [], 'source_quality': 'Unknown'}
            body = content
            
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    body = parts[2]
                    try:
                        parsed_fm = yaml.safe_load(parts[1])
                        if parsed_fm:
                            fm.update(parsed_fm)
                    except:
                        pass
            
            filename = os.path.basename(path)
            html_filename = filename.replace('.md', '.html')
            fm['html_filename'] = html_filename
            briefs.append(fm)
            
            # Generate brief HTML
            html_content = markdown.markdown(body, extensions=['tables', 'fenced_code'])
            brief_html = Template(BRIEF_TEMPLATE).render(content=html_content, title=fm['title'])
            
            with open(f'public/brief/{html_filename}', 'w', encoding='utf-8') as f:
                f.write(brief_html)
                
        except Exception as e:
            print(f"Error reading {path}: {e}")
            
    briefs.sort(key=lambda x: str(x.get('date', '')), reverse=True)

    # Fetch NBER
    feed_items = []
    try:
        d = feedparser.parse("https://www.nber.org/rss/new.xml")
        for entry in d.entries[:10]:
            feed_items.append({
                'source': 'NBER Working Papers',
                'title': entry.title,
                'link': entry.link,
                'date': entry.get('published', '')[:16],
                'summary': entry.get('summary', '').replace('<p>', '').replace('</p>', '')
            })
    except Exception as e:
        print("RSS error:", e)

    index_html = Template(HTML_TEMPLATE).render(briefs=briefs, feed_items=feed_items)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

if __name__ == '__main__':
    build()
    print("Build complete in ./public")
