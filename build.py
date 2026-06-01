import os
import re
import glob
import yaml
import markdown
import feedparser
from jinja2 import Template
import ssl
import shutil

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

    <title>Financial Literacy Radar</title>
    
    <!-- iOS / Android Web App Meta Tags -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="The Radar">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#000000">

    <!-- Android Web App Manifest -->
    <link rel="manifest" href="manifest.json">
    <!-- Generate simple black/white data icon for home screen -->
    <link rel="apple-touch-icon" href="apple-touch-icon.png">

    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #000000; --fg: #FFFFFF; --border: #333333; --accent: #888888; }
        body { background-color: var(--bg); color: var(--fg); font-family: 'Space Grotesk', sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; -webkit-font-smoothing: antialiased; }
        .container { max-width: 900px; margin: 0 auto; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.03em; margin-top: 0; }
        h1 { font-size: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 20px; }
        
        .header-bar { display: flex; justify-content: space-between; align-items: baseline; }
        .live-pulse { display: inline-block; width: 8px; height: 8px; background-color: #00ff00; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #00ff00; }
        .meta { font-size: 0.85rem; color: var(--accent); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
        
        
        /* Newsletter Capture */
        .newsletter-box { background: #050505; border: 1px solid #333; border-top: 3px solid var(--fg); padding: 30px; border-radius: 6px; margin-bottom: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        .newsletter-title { margin-top: 0; font-size: 1.4rem; color: var(--fg); margin-bottom: 10px;}
        .newsletter-desc { color: #aaa; font-size: 0.95rem; margin-bottom: 20px; line-height: 1.5; }
        .newsletter-form { display: flex; gap: 10px; }
        .newsletter-input { flex: 1; padding: 14px 15px; background: #000; border: 1px solid #444; color: #fff; font-family: 'Space Grotesk'; font-size: 1rem; border-radius: 4px; outline: none; transition: border-color 0.2s;}
        .newsletter-input:focus { border-color: var(--fg); }
        .newsletter-btn { background: var(--fg); color: var(--bg); border: none; padding: 0 25px; font-family: 'Space Grotesk'; font-size: 1rem; font-weight: 700; border-radius: 4px; cursor: pointer; transition: all 0.2s; white-space: nowrap;}
        .newsletter-btn:hover { opacity: 0.9; transform: translateY(-1px); }
        .newsletter-success { display: none; color: #00bbff; margin-top: 15px; font-weight: 600; font-size: 0.95rem; align-items: center; gap: 8px;}
        
        @media(max-width: 600px) { .newsletter-form { flex-direction: column; } .newsletter-btn { padding: 14px 0; } }

        /* Interactive Elements */
        .search-bar { width: 100%; padding: 18px 20px; background: #0a0a0a; border: 1px solid var(--border); color: white; font-family: 'Space Grotesk'; font-size: 1.1rem; border-radius: 6px; margin-bottom: 30px; box-sizing: border-box; transition: all 0.3s ease; -webkit-appearance: none; }
        .search-bar:focus { outline: none; border-color: var(--fg); box-shadow: 0 0 15px rgba(255,255,255,0.1); }
        .search-bar::placeholder { color: #555; }
        
        .tabs { display: flex; gap: 30px; border-bottom: 1px solid var(--border); margin-bottom: 30px; }
        .tab { background: none; border: none; color: var(--accent); font-family: 'Space Grotesk'; font-size: 1.1rem; padding: 10px 0; cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.3s; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; white-space: nowrap; }
        .tab.active { color: var(--fg); border-bottom: 2px solid var(--fg); }
        .tab:hover:not(.active) { color: #ccc; }
        .tab-content { display: none; animation: fadeIn 0.4s ease; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

        /* Cards */
        .card { border: 1px solid var(--border); padding: 24px; margin-bottom: 20px; border-radius: 6px; background-color: #050505; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); cursor: pointer; position: relative;}
        .card:hover { border-color: #888; transform: translateY(-3px); box-shadow: 0 10px 30px rgba(255,255,255,0.08); background-color: #0a0a0a;}
        a { color: var(--fg); text-decoration: none; transition: color 0.2s;}
        .card a::after { content: ''; display: block; position: absolute; top: 0; left: 0; right: 0; bottom: 0; }
        
        .tags { margin-top: 15px; display: flex; flex-wrap: wrap; gap: 8px; }
        .tags span { background: #111; border: 1px solid var(--border); padding: 4px 10px; font-size: 0.75rem; border-radius: 12px; text-transform: lowercase; }

        /* Dashboard Viz Styles */
        .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .viz-card { border: 1px solid var(--border); padding: 24px; border-radius: 6px; background-color: #050505; transition: border-color 0.3s; }
        .viz-card:hover { border-color: #555; }
        .viz-title { font-size: 0.85rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 15px; border-bottom: 1px solid #222; padding-bottom: 10px;}
        
        
        /* State Badges & Grades */
        .states-badge-grid { display: grid; grid-template-columns: repeat(10, 1fr); gap: 6px; margin-bottom: 20px; }
        .state-badge { background-color: #111; border: 1px solid #333; color: #555; border-radius: 4px; padding: 6px 0; text-align: center; font-size: 0.75rem; font-weight: 600; transition: all 0.2s;}
        .state-badge.grade-A { background-color: var(--fg); color: var(--bg); border-color: #00ff00; box-shadow: 0 0 12px rgba(0, 255, 0, 0.4); }
        .state-badge.grade-B { background-color: #555; color: #fff; border-color: #777; }
        .state-badge.grade-C { background-color: #333; color: #aaa; border-color: #444; }
        .state-badge.grade-D { background-color: #332222; color: #dd8888; border-color: #553333; }
        .state-badge.grade-F { background-color: #220000; color: #ff4444; border-color: #440000; box-shadow: 0 0 8px rgba(255,68,68,0.2); }
        
        /* Demographic Viz */
        .demo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 25px; border-top: 1px solid #222; padding-top: 20px;}
        .demo-box { background: #080808; border: 1px solid #222; padding: 15px; border-radius: 4px; }
        .demo-title { font-size: 0.8rem; color: #888; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em; border-bottom: 1px solid #222; padding-bottom: 5px; }
        .demo-stat { display: flex; justify-content: space-between; font-size: 0.95rem; margin-bottom: 8px; font-family: monospace;}
        @media(max-width: 480px) { .demo-grid { grid-template-columns: 1fr; } }

        
        
        /* Modal Styles */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.85); backdrop-filter: blur(5px); align-items: center; justify-content: center; }
        .modal-content { background-color: #0a0a0a; padding: 30px; border: 1px solid var(--border); border-radius: 8px; width: 90%; max-width: 500px; position: relative; animation: modalFadeIn 0.3s ease; }
        .close-btn { position: absolute; top: 15px; right: 20px; color: #888; font-size: 24px; font-weight: bold; cursor: pointer; transition: color 0.2s;}
        .close-btn:hover { color: var(--fg); }
        @keyframes modalFadeIn { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Timeline Styles */
        .timeline { position: relative; border-left: 2px solid var(--border); padding-left: 30px; margin-left: 15px; margin-top: 20px;}
        .timeline-item { position: relative; margin-bottom: 30px; }
        .timeline-dot { position: absolute; left: -37px; top: 5px; width: 12px; height: 12px; border-radius: 50%; background: var(--fg); box-shadow: 0 0 10px rgba(255,255,255,0.3);}
        .timeline-date { color: var(--accent); font-size: 0.85rem; font-weight: bold; margin-bottom: 5px; letter-spacing: 0.05em; }
        .timeline-content { background: #050505; border: 1px solid var(--border); padding: 20px; border-radius: 6px; transition: border-color 0.3s; }
        .timeline-content:hover { border-color: #555; }
        
        
        
        /* New Badge */
        .badge-new { background: #00ff00; color: #000; padding: 3px 8px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; margin-left: 10px; vertical-align: middle; letter-spacing: 0.05em; text-transform: uppercase; box-shadow: 0 0 10px rgba(0,255,0,0.4); display: inline-block; transform: translateY(-3px);}

        /* Pioneer Links */
        .pioneer-links { margin-top: 15px; border-top: 1px solid #222; padding-top: 15px; display: flex; gap: 10px; flex-wrap: wrap; }
        .p-link { font-size: 0.8rem; color: #888; text-decoration: none; border: 1px solid #333; padding: 4px 10px; border-radius: 4px; transition: all 0.2s; text-transform: uppercase; letter-spacing: 0.05em; display: flex; align-items: center; gap: 5px;}
        .p-link:hover { color: var(--fg); border-color: var(--fg); background: #111;}

        /* Pioneer Styles */
        .pioneer-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        @media(max-width: 768px) { .pioneer-grid { grid-template-columns: 1fr; } }

        /* Bar Chart */
        .bar-chart { display: flex; flex-direction: column; gap: 20px; margin-top: 20px;}
        .bar-row { display: flex; flex-direction: column; gap: 8px; }
        .bar-label { font-size: 0.9rem; display: flex; justify-content: space-between; font-weight: 600;}
        .bar-track { height: 12px; background-color: #222; border-radius: 6px; overflow: hidden; }
        .bar-fill { height: 100%; background-color: var(--fg); border-radius: 6px; transition: width 1s ease-in-out;}
        .bar-fill.danger { background-color: #ff4444; box-shadow: 0 0 8px rgba(255,68,68,0.4); }
        
        /* Interactive Calculator */
        .calc-container { display: none; }
        
        
        /* Momentum Styles */
        .momentum-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-top: 15px; }
        .momentum-card { background: #080808; border: 1px solid #222; border-left: 3px solid #00bbff; padding: 15px; border-radius: 4px; transition: all 0.2s; }
        .momentum-card:hover { border-color: #00bbff; background: #110a00; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,187,255,0.05); }

        
        /* Footer / Data Hub */
        .footer { margin-top: 60px; padding-top: 30px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        .footer-text { color: #666; font-size: 0.85rem; }
        .data-btn { background: #111; border: 1px solid #333; color: #aaa; padding: 8px 16px; border-radius: 4px; font-family: 'Space Grotesk'; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; text-decoration: none;}
        .data-btn:hover { background: #222; color: var(--fg); border-color: #555; }
        
        @media(max-width: 600px) { .footer { flex-direction: column; gap: 15px; align-items: flex-start; } }

        
        /* Implementation Blueprint Styles */
        .blueprint-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;}
        .bp-card { background: #080808; border: 1px solid #333; padding: 25px; border-radius: 6px; }
        .bp-step { display: flex; gap: 15px; margin-bottom: 25px; }
        .bp-number { background: var(--fg); color: var(--bg); width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; font-weight: bold; border-radius: 50%; flex-shrink: 0; }
        .bp-content h4 { margin: 0 0 8px 0; color: var(--fg); font-size: 1.1rem; }
        .bp-content p { margin: 0; color: #aaa; font-size: 0.95rem; line-height: 1.5;}
        
        .bp-case-study { background: #111; border-left: 3px solid #00bbff; padding: 15px; margin-top: 15px;}
        .bp-case-title { font-size: 0.8rem; color: #00bbff; text-transform: uppercase; letter-spacing: 0.05em; font-weight: bold; margin-bottom: 5px;}
        
        @media(max-width: 768px) { .blueprint-grid { grid-template-columns: 1fr; } }

        
        
        
        
        
                @media(max-width: 400px) { .states-badge-grid { grid-template-columns: repeat(5, 1fr); } }
    '''
    map_html = '<div style="font-size: 1.6rem; font-weight: 700; margin-bottom: 15px; letter-spacing: -0.05em; line-height: 1.1; text-align: left;">30 <span style="font-size: 1rem; color: var(--accent); font-weight: 400; letter-spacing: normal;">/ 50 States Mandate K-12 Finance</span></div>\n'
    map_html += '<div class="states-badge-grid">\n'
    for s in states_list:
        map_html += f'<div class="state-badge grade-{s["grade"]}" title="{s["name"]}">{s["code"]}</div>\n'
    map_html += '</div>'
    
    with open('public/embed/map.html', 'w', encoding='utf-8') as f:
        f.write(Template(EMBED_TEMPLATE).render(content=map_html, extra_css=map_css, extra_js=''))

    # Finra Embed
    finra_css = '''
        .bar-chart { display: flex; flex-direction: column; gap: 20px; }
        .bar-row { display: flex; flex-direction: column; gap: 8px; }
        .bar-label { font-size: 1rem; display: flex; justify-content: space-between; font-weight: 600;}
        .bar-track { height: 16px; background-color: #222; border-radius: 8px; overflow: hidden; }
        .bar-fill { height: 100%; background-color: var(--fg); border-radius: 8px; transition: width 1s ease-in-out;}
        .bar-fill.danger { background-color: #ff4444; box-shadow: 0 0 8px rgba(255,68,68,0.4); }
    '''
    finra_html = '<div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 25px; letter-spacing: -0.03em; text-align: left;">The Capability Gap</div>\n'
    finra_html += '''
        <div class="bar-chart">
            <div class="bar-row">
                <div class="bar-label"><span style="color: var(--accent);">Adult Average</span><span>49%</span></div>
                <div class="bar-track"><div class="bar-fill" style="width: 0%;" data-width="49%"></div></div>
            </div>
            <div class="bar-row" style="margin-top: 15px;">
                <div class="bar-label"><span style="color: var(--accent);">Gen Z Average</span><span style="color: #ff4444;">38%</span></div>
                <div class="bar-track"><div class="bar-fill danger" style="width: 0%;" data-width="38%"></div></div>
            </div>
        </div>
    '''
    finra_js = "setTimeout(() => { document.querySelectorAll('.bar-fill').forEach(bar => { bar.style.width = bar.getAttribute('data-width'); }); }, 200);"
    with open('public/embed/finra.html', 'w', encoding='utf-8') as f:
        f.write(Template(EMBED_TEMPLATE).render(content=finra_html, extra_css=finra_css, extra_js=finra_js))

    
    # --- Generate State SEO Pages ---
    os.makedirs('public/states', exist_ok=True)
    for s in states_list:
        state_html = Template(STATE_TEMPLATE).render(state=s)
        with open(f'public/states/{s["code"].lower()}.html', 'w', encoding='utf-8') as f:
            f.write(state_html)

    index_html = Template(HTML_TEMPLATE).render(briefs=briefs, feed_items=feed_items, states_list=states_list, active_bills=active_bills)

    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    try:
        shutil.copy('apple-touch-icon.png', 'public/apple-touch-icon.png')
    except:
        pass

if __name__ == '__main__':
    build()
    print("Build complete in ./public")
