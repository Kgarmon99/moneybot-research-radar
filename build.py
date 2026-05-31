import os
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
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jsvectormap/dist/css/jsvectormap.min.css" />
    <script src="https://cdn.jsdelivr.net/npm/jsvectormap"></script>
    <script>jsVectorMap.prototype.addMap = jsVectorMap.addMap;</script>
    <script src="https://cdn.jsdelivr.net/npm/jsvectormap/dist/maps/us-aea-en.js"></script>
    <style>
        :root { --bg: #000000; --fg: #FFFFFF; --border: #333333; --accent: #888888; }
        body { background-color: var(--bg); color: var(--fg); font-family: 'Space Grotesk', sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; -webkit-font-smoothing: antialiased; }
        .container { max-width: 900px; margin: 0 auto; }
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.03em; margin-top: 0; }
        h1 { font-size: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 20px; }
        
        .header-bar { display: flex; justify-content: space-between; align-items: baseline; }
        .live-pulse { display: inline-block; width: 8px; height: 8px; background-color: #00ff00; border-radius: 50%; margin-right: 8px; box-shadow: 0 0 8px #00ff00; }
        .meta { font-size: 0.85rem; color: var(--accent); margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
        
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
        .card { border: 1px solid var(--border); padding: 24px; margin-bottom: 20px; border-radius: 6px; background-color: #050505; transition: all 0.2s; cursor: pointer; position: relative;}
        .card:hover { border-color: #666; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(255,255,255,0.05);}
        a { color: var(--fg); text-decoration: none; transition: color 0.2s;}
        .card a::after { content: ''; display: block; position: absolute; top: 0; left: 0; right: 0; bottom: 0; }
        
        .tags { margin-top: 15px; display: flex; flex-wrap: wrap; gap: 8px; }
        .tags span { background: #111; border: 1px solid var(--border); padding: 4px 10px; font-size: 0.75rem; border-radius: 12px; text-transform: lowercase; }

        /* Dashboard Viz Styles */
        .dashboard-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .viz-card { border: 1px solid var(--border); padding: 24px; border-radius: 6px; background-color: #050505; transition: border-color 0.3s; }
        .viz-card:hover { border-color: #555; }
        .viz-title { font-size: 0.85rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 15px; border-bottom: 1px solid #222; padding-bottom: 10px;}
        
        /* Map styles */
        #us-map { width: 100%; height: 400px; margin-bottom: 20px; }
        .jvm-tooltip {
            background-color: #111 !important;
            color: #fff !important;
            border: 1px solid var(--border) !important;
            border-radius: 4px !important;
            font-family: 'Space Grotesk', sans-serif !important;
            padding: 8px 12px !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5) !important;
        }
        
        /* Bar Chart */
        .bar-chart { display: flex; flex-direction: column; gap: 20px; margin-top: 20px;}
        .bar-row { display: flex; flex-direction: column; gap: 8px; }
        .bar-label { font-size: 0.9rem; display: flex; justify-content: space-between; font-weight: 600;}
        .bar-track { height: 12px; background-color: #222; border-radius: 6px; overflow: hidden; }
        .bar-fill { height: 100%; background-color: var(--fg); border-radius: 6px; transition: width 1s ease-in-out;}
        .bar-fill.danger { background-color: #ff4444; box-shadow: 0 0 8px rgba(255,68,68,0.4); }
        
        /* Interactive Calculator */
        .calc-container { display: flex; flex-wrap: wrap; gap: 30px; align-items: flex-start; justify-content: space-between; }
        .calc-left { flex: 1 1 300px; }
        .calc-right { flex: 0 0 auto; min-width: 200px; background: #111; padding: 20px; border-radius: 6px; border: 1px solid var(--border); }
        
        input[type=range] { -webkit-appearance: none; width: 100%; background: transparent; margin: 20px 0; }
        input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; height: 24px; width: 24px; border-radius: 50%; background: var(--fg); cursor: pointer; margin-top: -10px; box-shadow: 0 0 10px rgba(255,255,255,0.5); transition: transform 0.1s;}
        input[type=range]::-webkit-slider-thumb:hover { transform: scale(1.1); }
        input[type=range]::-webkit-slider-runnable-track { width: 100%; height: 4px; cursor: pointer; background: var(--border); border-radius: 2px; }
        .tax-result { font-size: 3rem; font-weight: 700; color: #ff4444; margin: 5px 0; text-shadow: 0 0 20px rgba(255,68,68,0.2); letter-spacing: -0.05em; line-height: 1.1;}
        
        /* --- MOBILE OPTIMIZATION --- */
        @media(max-width: 768px) { 
            body { padding: 20px 15px; }
            h1 { font-size: 1.8rem; margin-bottom: 10px; line-height: 1.2; border-bottom: none; }
            .header-bar { flex-direction: column; align-items: flex-start; gap: 15px; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 15px;}
            .header-actions { width: 100%; justify-content: space-between; margin-top: 5px; }
            
            p.intro-text { margin-top: 0; font-size: 0.95rem; margin-bottom: 25px;}
            
            .dashboard-grid { grid-template-columns: 1fr; gap: 15px;}
            
            .tabs { overflow-x: auto; -webkit-overflow-scrolling: touch; padding-bottom: 5px; gap: 15px; margin-bottom: 20px; }
            .tab { font-size: 0.95rem; padding: 8px 0; }
            .tabs::-webkit-scrollbar { display: none; }
            
            .card { padding: 18px; margin-bottom: 15px; }
            .viz-card { padding: 18px; }
            
            .states-grid { gap: 4px; }
            
            .search-bar { padding: 14px 15px; font-size: 1rem; margin-bottom: 20px;}
            .tax-result { font-size: 2.5rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header-bar">
            <h1>MONEYBOT RESEARCH RADAR</h1>
            <div class="header-actions" style="display: flex; gap: 15px; align-items: center;">
                <span class="meta" style="margin-bottom: 0;"><span class="live-pulse"></span>AUTO-UPDATED DAILY</span>
                <a href="https://getmoneybot.com" target="_blank" style="background: var(--fg); color: var(--bg); padding: 8px 16px; border-radius: 4px; font-weight: 700; font-size: 0.9rem; text-decoration: none; border: none; white-space: nowrap;">Try MoneyBot &rarr;</a>
            </div>
        </div>
        
        <p class="intro-text" style="color: var(--accent); max-width: 600px; margin-top: -10px; margin-bottom: 40px;">
            A live, interactive dashboard tracking empirical data and policy changes regarding financial literacy, household finance, and the "Fragility Tax".
        </p>

        <!-- TABS -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('dashboard')">Dashboard</button>
            <button class="tab" onclick="switchTab('library')">Research Library</button>
            <button class="tab" onclick="switchTab('feed')">Live Feed</button>
        </div>

        <!-- TAB: DASHBOARD -->
        <div id="dashboard" class="tab-content active">
            <div class="dashboard-grid">
                <!-- NGPF Map Viz -->
                <div class="viz-card">
                    <div class="viz-title">K-12 Policy Mandates (NGPF)</div>
                    <div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 20px; letter-spacing: -0.05em; line-height: 1.1;">25 <span style="font-size: 1.2rem; color: var(--accent); font-weight: 400; letter-spacing: normal;">/ 50 States</span></div>
                    <div id="us-map"></div>
                    <p style="font-size: 0.85rem; color: var(--accent); margin-top: 15px; line-height: 1.5; margin-bottom: 0;">States guaranteeing a standalone Personal Finance course for high school graduation.</p>
                </div>

                <!-- FINRA Gap Viz -->
                <div class="viz-card">
                    <div class="viz-title">Financial Capability (FINRA)</div>
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
                    <p style="font-size: 0.85rem; color: var(--accent); margin-top: 25px; line-height: 1.5; margin-bottom: 0;">Percentage of core financial literacy questions answered correctly. The capability gap is rapidly widening.</p>
                </div>
            </div>

            <!-- Fragility Tax Calculator (Interactive) -->
            <div class="viz-card" style="margin-bottom: 40px;">
                <div class="viz-title" style="display: flex; justify-content: space-between;">
                    <span>Interactive: The "Fragility Tax" Calculator</span>
                    <a href="https://twitter.com/intent/tweet?text=My%20lack%20of%20financial%20literacy%20could%20cost%20me%20hundreds%20in%20the%20annual%20%27Fragility%20Tax.%27%20Calculate%20yours%20on%20the%20MoneyBot%20Research%20Radar.&url=https://Kgarmon99.github.io/moneybot-research-radar/" target="_blank" style="color: #1DA1F2; font-weight: 600; font-size: 0.75rem; border: 1px solid #1DA1F2; padding: 2px 8px; border-radius: 4px; text-transform: none; letter-spacing: normal;">Share to X / Twitter</a>
                </div>
                <div class="calc-container">
                    <div class="calc-left">
                        <label style="font-weight: 600; font-size: 1.1rem; display: block; margin-bottom: 10px;">Average Credit Card Balance: $<span id="debtDisplay">5,000</span></label>
                        <input type="range" id="debtSlider" min="500" max="25000" step="500" value="5000" oninput="calcTax()">
                        <p style="font-size: 0.85rem; color: var(--accent); line-height: 1.5; margin-top: 15px; margin-bottom: 0;">
                            Based on Stanford SIEPR research, individuals with low financial literacy pay roughly a <strong>6% premium</strong> in transaction fees, higher interest rates, and minimum payment traps.
                        </p>
                    </div>
                    <div class="calc-right">
                        <div style="font-size: 0.85rem; color: var(--accent); text-transform: uppercase; letter-spacing: 0.05em;">Annual Fragility Tax</div>
                        <div class="tax-result">$<span id="taxDisplay">300.00</span></div>
                        <div style="font-size: 0.85rem; color: #ff4444; margin-bottom: 15px;">Lost wealth per year</div>
                        <div style="font-size: 0.7rem; color: #555; background: #0a0a0a; padding: 10px; border-radius: 4px; border: 1px dashed #222;">
                            <code style="background: transparent; padding: 0; border: none; display: block; color: var(--accent); margin-bottom: 5px;">&lt;iframe src="https://Kgarmon99.github.io/moneybot-research-radar"&gt;&lt;/iframe&gt;</code>
                            Embed this calculator
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB: LIBRARY -->
        <div id="library" class="tab-content">
            <input type="text" id="searchLibrary" class="search-bar" placeholder="Search curated briefs, memos, and tags..." onkeyup="filterCards('libraryCards', 'searchLibrary')">
            <div id="libraryCards">
                {% if briefs %}
                    {% for brief in briefs %}
                    <div class="card item-card">
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
            </div>
        </div>

        <!-- TAB: FEED -->
        <div id="feed" class="tab-content">
            <input type="text" id="searchFeed" class="search-bar" placeholder="Search live NBER working papers..." onkeyup="filterCards('feedCards', 'searchFeed')">
            <div id="feedCards">
                {% for item in feed_items %}
                <div class="card item-card">
                    <div class="meta">{{ item.source }} &nbsp;|&nbsp; {{ item.date }}</div>
                    <h3 style="margin: 0; font-size: 1.1rem;"><a href="{{ item.link }}" target="_blank">{{ item.title }}</a></h3>
                    <p style="color: var(--accent); font-size: 0.9rem; margin-top: 10px; margin-bottom: 10px;">{{ item.summary[:200] }}...</p>
                    <div style="background: #111; padding: 10px 15px; border-left: 3px solid var(--fg); border-radius: 4px; font-size: 0.85rem; font-weight: 600; color: #ddd;">
                        🤖 {{ item.takeaway }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        // Tab Switching Logic
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            document.querySelector(`button[onclick="switchTab('${tabId}')"]`).classList.add('active');
            
            // Trigger bar chart animation if switching to dashboard
            if(tabId === 'dashboard') {
                setTimeout(animateBars, 100);
            }
        }

        // Live Search Filtering
        function filterCards(containerId, inputId) {
            const query = document.getElementById(inputId).value.toLowerCase();
            const cards = document.getElementById(containerId).getElementsByClassName('item-card');
            for (let card of cards) {
                const text = card.innerText.toLowerCase();
                card.style.display = text.includes(query) ? 'block' : 'none';
            }
        }

        // Interactive Fragility Tax Calculator
        function calcTax() {
            const debt = document.getElementById('debtSlider').value;
            document.getElementById('debtDisplay').innerText = Number(debt).toLocaleString();
            
            const tax = debt * 0.06; 
            document.getElementById('taxDisplay').innerText = tax.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }

        // Animate Bars on Load
        function animateBars() {
            document.querySelectorAll('.bar-fill').forEach(bar => {
                bar.style.width = bar.getAttribute('data-width');
            });
        }

        // JSVectorMap Initialization
        const mandatedStates = ['US-AL', 'US-AR', 'US-CT', 'US-FL', 'US-GA', 'US-ID', 'US-IN', 'US-IA', 'US-KS', 'US-LA', 'US-MI', 'US-MN', 'US-MS', 'US-MO', 'US-NE', 'US-NV', 'US-NH', 'US-NC', 'US-OH', 'US-OR', 'US-PA', 'US-RI', 'US-SC', 'US-TN', 'US-UT', 'US-VA', 'US-WV'];
        
        const map = new jsVectorMap({
            selector: '#us-map',
            map: 'us_aea_en',
            backgroundColor: 'transparent',
            zoomButtons: false,
            zoomOnScroll: false,
            regionStyle: {
                initial: { fill: '#222222', stroke: '#333333', strokeWidth: 0.5 },
                hover: { fill: '#444444' },
                selected: { fill: '#FFFFFF' },
                selectedHover: { fill: '#cccccc' }
            },
            selectedRegions: mandatedStates,
            onRegionTooltipShow(event, tooltip, code) {
                if (mandatedStates.includes(code)) {
                    tooltip.html('<strong>' + tooltip.text() + '</strong><br><span style="color:#00ff00;">Guaranteed Personal Finance</span>');
                } else {
                    tooltip.html('<strong>' + tooltip.text() + '</strong><br><span style="color:#888888;">No Guarantee Yet</span>');
                }
            }
        });

        // Initialize
        window.onload = () => {
            calcTax();
            setTimeout(animateBars, 300);
            setTimeout(() => map.updateSize(), 500);
        };
    </script>
</body>
</html>
"""

BRIEF_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ title }} | Research Radar</title>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #000000; --fg: #FFFFFF; --border: #333333; --accent: #888888; }
        body { background-color: var(--bg); color: var(--fg); font-family: 'Space Grotesk', sans-serif; margin: 0; padding: 40px 20px; line-height: 1.6; -webkit-font-smoothing: antialiased;}
        .container { max-width: 800px; margin: 0 auto; background: #050505; padding: 40px; border: 1px solid var(--border); border-radius: 8px;}
        h1, h2, h3 { font-weight: 600; letter-spacing: -0.03em; }
        h1 { font-size: 2.5rem; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 20px; margin-top: 20px; line-height: 1.1;}
        h2 { font-size: 1.4rem; margin-top: 40px; color: var(--fg); border-bottom: 1px solid var(--border); padding-bottom: 5px;}
        a { color: var(--fg); text-decoration: none; border-bottom: 1px solid var(--border); transition: border-color 0.2s;}
        a:hover { border-bottom: 1px solid var(--fg); color: #ccc;}
        .back-link { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--accent); border: none; display: inline-block; margin-bottom: 20px; transition: color 0.2s;}
        .back-link:hover { color: var(--fg); border: none; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 24px; margin-top: 24px; display: block; overflow-x: auto; white-space: nowrap;}
        th, td { border: 1px solid var(--border); padding: 12px; text-align: left; font-size: 0.9rem; }
        th { color: var(--accent); font-weight: normal; text-transform: uppercase; letter-spacing: 0.05em;}
        code { background: #111; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; border: 1px solid #222;}
        pre { background: #111; padding: 15px; border-radius: 4px; overflow-x: auto; border: 1px solid var(--border); }
        blockquote { border-left: 3px solid var(--accent); margin: 0; padding-left: 15px; color: #ccc; font-style: italic;}
        ul, ol { padding-left: 20px; }
        li { margin-bottom: 10px; }
        
        @media(max-width: 768px) {
            body { padding: 15px 10px; }
            .container { padding: 20px; border-radius: 6px; }
            h1 { font-size: 1.8rem; }
            h2 { font-size: 1.2rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="back-link">&larr; Return to Dashboard</a>
        {{ content|safe }}
    </div>
</body>
</html>
"""

def build():
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
            
            html_content = markdown.markdown(body, extensions=['tables', 'fenced_code'])
            brief_html = Template(BRIEF_TEMPLATE).render(content=html_content, title=fm['title'])
            
            with open(f'public/brief/{html_filename}', 'w', encoding='utf-8') as f:
                f.write(brief_html)
                
        except Exception as e:
            print(f"Error reading {path}: {e}")
            
    briefs.sort(key=lambda x: str(x.get('date', '')), reverse=True)

    feed_items = []
    try:
        d = feedparser.parse("https://www.nber.org/rss/new.xml")
        for entry in d.entries[:10]:
            # Generate a 1-sentence "MoneyBot Takeaway" prompt locally
            summary = entry.get('summary', '').replace('<p>', '').replace('</p>', '')
            # For a static build script, we will synthesize a simple automated takeaway based on keywords
            takeaway = ""
            lower_title = entry.title.lower()
            if 'tax' in lower_title: takeaway = "MoneyBot Takeaway: This highlights how taxation systems systematically impact household wealth retention."
            elif 'mortgage' in lower_title or 'housing' in lower_title: takeaway = "MoneyBot Takeaway: Real estate structural dynamics are actively making homeownership a harder hurdle for Gen Z."
            elif 'literacy' in lower_title or 'education' in lower_title: takeaway = "MoneyBot Takeaway: Direct empirical proof that financial capability requires scalable, early intervention."
            else: takeaway = "MoneyBot Takeaway: Macroeconomic shifts directly dictate the purchasing power and fragility of everyday consumers."
            
            feed_items.append({
                'source': 'NBER Working Papers',
                'title': entry.title,
                'link': entry.link,
                'date': entry.get('published', '')[:16],
                'summary': summary[:200],
                'takeaway': takeaway
            })
    except Exception as e:
        print("RSS error:", e)

    index_html = Template(HTML_TEMPLATE).render(briefs=briefs, feed_items=feed_items)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

if __name__ == '__main__':
    build()
    print("Build complete in ./public")
