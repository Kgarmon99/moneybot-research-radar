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
            <h1>STATE OF FINANCIAL LITERACY</h1>
            <div class="header-actions" style="display: flex; gap: 15px; align-items: center;">
                <span class="meta" style="margin-bottom: 0;"><span class="live-pulse"></span>AUTO-UPDATED DAILY</span>
            </div>
        </div>
        
        <p class="intro-text" style="color: var(--accent); max-width: 600px; margin-top: -10px; margin-bottom: 40px;">
            A live, interactive dashboard tracking empirical data and policy changes regarding financial literacy, household finance, and the "Fragility Tax".
        </p>

        
        <!-- TABS -->
        <div class="tabs">
            <button class="tab active" onclick="switchTab('dashboard')">Dashboard</button>
            <button class="tab" onclick="switchTab('library')">Research Library</button>
            <button class="tab" onclick="switchTab('pioneers')">Pioneers</button>
            <button class="tab" onclick="switchTab('timeline')">Timeline</button>
            <button class="tab" onclick="switchTab('feed')">Live Feed</button>
        </div>


        <!-- TAB: DASHBOARD -->
        <div id="dashboard" class="tab-content active">
            <div class="dashboard-grid">
                <!-- NGPF Map Viz -->
                <div class="viz-card">
                    <div class="viz-title">K-12 Policy Mandates (NGPF)</div>
                    <div style="font-size: 2.5rem; font-weight: 700; margin-bottom: 20px; letter-spacing: -0.05em; line-height: 1.1;">30 <span style="font-size: 1.2rem; color: var(--accent); font-weight: 400; letter-spacing: normal;">/ 50 States</span></div>
                    <div class="states-badge-grid">
                        {% for state in states_list %}
                        <div class="state-badge grade-{{ state.grade }}" onclick="openStateModal('{{ state.code }}', '{{ state.name }}', '{{ state.grade }}', '{{ state.details }}')" style="cursor: pointer;" title="Tap for info">{{ state.code }}</div>
                        {% endfor %}
                    </div>
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

            <!-- Stanford Validation / Solution Viz -->
            <div class="viz-card" style="margin-top: 20px; border-color: var(--fg);">
                <div class="viz-title" style="color: var(--fg); font-weight: 600;">The Solution: Just-In-Time Gamification (Stanford SIEPR)</div>
                <p style="font-size: 0.95rem; color: #ddd; margin-bottom: 25px; line-height: 1.6;">Stanford economic data proves that short, narrative-driven interventions significantly outperform traditional 14-week lectures. Empirical evidence points to bridging the Gen-Z capability gap by delivering education <strong>at the point of decision</strong>.</p>
                
                <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: stretch;">
                    <!-- Traditional -->
                    <div style="flex: 1 1 300px; padding: 20px; border: 1px solid #222; border-radius: 6px; background: #080808; position: relative; overflow: hidden;">
                        <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: #ff4444;"></div>
                        <h4 style="margin: 0 0 15px 0; color: #ff4444; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;">Traditional Education</h4>
                        <div style="font-size: 1.4rem; font-weight: 600; margin-bottom: 15px;">"Just-In-Case"</div>
                        <ul style="list-style: none; padding: 0; margin: 0; color: var(--accent); font-size: 0.9rem;">
                            <li style="margin-bottom: 10px;">&times; Taught at age 16</li>
                            <li style="margin-bottom: 10px;">&times; Textbook format (Low engagement)</li>
                            <li style="margin-bottom: 10px;">&times; Retained only 5-10% by adulthood</li>
                        </ul>
                    </div>
                    
                    <!-- Modern -->
                    <div style="flex: 1 1 300px; padding: 20px; border: 1px solid #333; border-radius: 6px; background: #111; position: relative; overflow: hidden; box-shadow: 0 0 20px rgba(255, 255, 255, 0.05);">
                        <div style="position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--fg);"></div>
                        <h4 style="margin: 0 0 15px 0; color: var(--fg); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.05em;">Targeted Interventions</h4>
                        <div style="font-size: 1.4rem; font-weight: 600; margin-bottom: 15px;">"Just-In-Time"</div>
                        <ul style="list-style: none; padding: 0; margin: 0; color: #ccc; font-size: 0.9rem;">
                            <li style="margin-bottom: 10px;">&check; Delivered at point-of-decision</li>
                            <li style="margin-bottom: 10px;">&check; 2-minute gamified storytelling</li>
                            <li style="margin-bottom: 10px;">&check; Dramatically lowers the "Fragility Tax"</li>
                        </ul>
                    </div>
                </div>
            </div>

        </div>

        <!-- TAB: LIBRARY -->
        <div id="library" class="tab-content">
            <div style="margin-bottom: 25px;">
                <h2 style="font-size: 1.5rem; margin-bottom: 5px;">Curated Intelligence</h2>
                <p style="color: var(--accent); font-size: 0.95rem;">Policy briefs, academic syntheses, and macro trend analysis tracking modern financial interventions.</p>
            </div>
            <input type="text" id="searchLibrary" class="search-bar" placeholder="Search curated briefs, memos, and tags..." onkeyup="filterCards('libraryCards', 'searchLibrary')">
            <div id="libraryCards">
                {% if briefs %}
                    {% for brief in briefs %}
                    <div class="card item-card" onclick="window.location.href='brief/{{ brief.html_filename }}'" style="cursor: pointer;">
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
                    </div>
                    {% endfor %}
                {% else %}
                    <p>No local research briefs found.</p>
                {% endif %}
            </div>
        </div>

        
        <!-- TAB: PIONEERS -->
        <div id="pioneers" class="tab-content">
            <div style="margin-bottom: 25px;">
                <h2 style="font-size: 1.5rem; margin-bottom: 5px;">Pioneers in Financial Literacy</h2>
                <p style="color: var(--accent); font-size: 0.95rem;">The researchers and advocates who defined the capability gap and drove the mandate movement.</p>
            </div>
            <div class="pioneer-grid">
                <div class="card" style="margin-bottom:0;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.3rem;">Dr. Annamaria Lusardi</h3>
                    <div class="meta" style="margin-bottom: 15px;">Stanford SIEPR & GFLEC</div>
                    <p style="font-size: 0.95rem; color: #ccc;">A globally recognized authority on financial literacy. Co-designed the "Big Three" questions, which became the global standard for measuring financial capability. Her research links illiteracy to the "Fragility Tax"—the high costs incurred by vulnerable populations.</p>
                </div>
                <div class="card" style="margin-bottom:0;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.3rem;">Dr. Olivia S. Mitchell</h3>
                    <div class="meta" style="margin-bottom: 15px;">Wharton School</div>
                    <p style="font-size: 0.95rem; color: #ccc;">Co-creator of the "Big Three" questions. Mitchell's extensive research focuses on pensions and household finance, proving empirically that individuals with higher financial literacy plan better and accumulate more wealth for retirement.</p>
                </div>
                <div class="card" style="margin-bottom:0;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.3rem;">Tim Ranzetta</h3>
                    <div class="meta" style="margin-bottom: 15px;">Co-Founder, NGPF</div>
                    <p style="font-size: 0.95rem; color: #ccc;">The driving force behind the Next Gen Personal Finance movement. By providing high-quality, free curriculum to teachers and lobbying state legislatures, Ranzetta helped catalyze the rapid expansion to 30 states mandating personal finance.</p>
                </div>
                <div class="card" style="margin-bottom:0;">
                    <h3 style="margin-top: 0; margin-bottom: 5px; font-size: 1.3rem;">CFPB</h3>
                    <div class="meta" style="margin-bottom: 15px;">Office of Financial Education</div>
                    <p style="font-size: 0.95rem; color: #ccc;">Following the 2008 financial crisis, the Consumer Financial Protection Bureau became the primary federal organ for researching consumer financial well-being, emphasizing action-oriented capability over mere knowledge retention.</p>
                </div>
            </div>
        </div>

        <!-- TAB: TIMELINE -->
        <div id="timeline" class="tab-content">
            <div style="margin-bottom: 25px;">
                <h2 style="font-size: 1.5rem; margin-bottom: 5px;">The Mandate Movement</h2>
                <p style="color: var(--accent); font-size: 0.95rem;">Key milestones in the fight to make financial literacy a national standard.</p>
            </div>
            <div class="timeline">
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">2004</div>
                    <div class="timeline-content">
                        <h4 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--fg);">The "Big Three" Created</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #ccc; line-height: 1.5;">Lusardi and Mitchell add three basic financial literacy questions (Compound Interest, Inflation, Risk Diversification) to the Health and Retirement Study, creating the global benchmark for measuring financial capability.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">2008 - 2010</div>
                    <div class="timeline-content">
                        <h4 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--fg);">Pioneer States Emerge</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #ccc; line-height: 1.5;">States like Utah and Missouri establish the first rigorous, standalone personal finance requirements for high school graduation, setting the "gold standard" for funding and curriculum.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">2011</div>
                    <div class="timeline-content">
                        <h4 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--fg);">CFPB Established</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #ccc; line-height: 1.5;">In the wake of the 2008 financial crisis, the Consumer Financial Protection Bureau is established, launching dedicated federal research into consumer financial well-being.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">2014</div>
                    <div class="timeline-content">
                        <h4 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--fg);">NGPF Founded</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #ccc; line-height: 1.5;">Next Gen Personal Finance is launched to provide free, up-to-date curriculum to high school teachers, removing the cost barrier for schools to implement financial education programs.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">2023 - 2024</div>
                    <div class="timeline-content">
                        <h4 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--fg);">The Legislative Tipping Point</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #ccc; line-height: 1.5;">A massive wave of state legislation passes. States like Pennsylvania, Wisconsin, and Connecticut mandate personal finance courses. The total number of states guaranteeing courses jumps dramatically.</p>
                    </div>
                </div>
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-date">Present Day</div>
                    <div class="timeline-content">
                        <h4 style="margin: 0 0 10px 0; font-size: 1.1rem; color: var(--fg);">The Adult Capability Gap</h4>
                        <p style="margin: 0; font-size: 0.9rem; color: #ccc; line-height: 1.5;">While 30 states now protect high schoolers with mandates, data reveals Gen Z adults who missed the mandates are struggling, with only 38% financial literacy capability, necessitating targeted technological interventions.</p>
                    </div>
                </div>
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

        <!-- State Modal -->
        <div id="stateModal" class="modal" onclick="closeStateModal(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <span class="close-btn" onclick="closeStateModal()">&times;</span>
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                    <div id="modalStateBadge" class="state-badge" style="font-size: 1.2rem; padding: 10px 15px; width: auto; pointer-events: none;">TX</div>
                    <h2 id="modalStateName" style="margin: 0; border: none; font-size: 1.8rem; padding: 0;">Texas</h2>
                </div>
                <div id="modalStateStatus" style="display: inline-block; padding: 6px 12px; border-radius: 4px; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 20px;">STATUS</div>
                <p id="modalStateDetails" style="color: #ccc; font-size: 1rem; line-height: 1.6; border-top: 1px solid var(--border); padding-top: 20px; margin-bottom: 0;"></p>
            </div>
        </div>

    </div>

    <script>
        // Tab Switching Logic
        
        function openStateModal(code, name, grade, details) {
            const modal = document.getElementById('stateModal');
            document.getElementById('modalStateName').innerText = name;
            
            const badge = document.getElementById('modalStateBadge');
            badge.innerText = code;
            badge.className = 'state-badge grade-' + grade;
            
            const status = document.getElementById('modalStateStatus');
            status.innerText = 'NGPF Grade: ' + grade;
            
            if (grade === 'A') {
                status.style.backgroundColor = 'var(--fg)'; 
                status.style.color = 'var(--bg)';
                status.style.boxShadow = '0 0 15px rgba(0, 255, 0, 0.3)';
                status.style.border = '1px solid #00ff00';
            } else if (grade === 'B' || grade === 'C') {
                status.style.backgroundColor = '#444'; status.style.color = '#ccc';
            } else {
                status.style.backgroundColor = '#220000'; status.style.color = '#ff4444';
            }
            
            document.getElementById('modalStateDetails').innerText = details;
            modal.style.display = 'flex';
        }

        function closeStateModal(e) {
            if (e && e.target !== document.getElementById('stateModal') && e.type === 'click' && !e.target.classList.contains('close-btn')) {
                return;
            }
            document.getElementById('stateModal').style.display = 'none';
        }

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
            const debtElem = document.getElementById('debtSlider');
            if (debtElem) {
                const debt = debtElem.value;
                document.getElementById('debtDisplay').innerText = Number(debt).toLocaleString();
                const tax = debt * 0.06; 
                document.getElementById('taxDisplay').innerText = tax.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
            }
        }

        // Animate Bars on Load
        function animateBars() {
            document.querySelectorAll('.bar-fill').forEach(bar => {
                bar.style.width = bar.getAttribute('data-width');
            });
        }

        // Initialize
        window.onload = () => {
            calcTax();
            setTimeout(animateBars, 300);
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
            
            # Extract preview
            preview = ""
            match = re.search(r'## Bottom Line\s*(.*?)(?=\n##|\Z)', body, re.DOTALL | re.IGNORECASE)
            if match:
                preview = match.group(1).strip()[:180] + "..."
            else:
                lines = [line.strip() for line in body.split('\n') if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('**Date')]
                if lines:
                    preview = lines[0][:180] + "..."
            fm['preview'] = preview

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
    
    # 1. NBER Working Papers
    try:
        d = feedparser.parse("https://www.nber.org/rss/new.xml")
        for entry in d.entries[:5]:
            takeaway = "Academic insight into economic structures and household finance."
            lower_title = entry.title.lower()
            if 'tax' in lower_title: takeaway = "Highlights how taxation systems systematically impact household wealth retention."
            elif 'mortgage' in lower_title or 'housing' in lower_title: takeaway = "Real estate structural dynamics are actively making homeownership a harder hurdle for Gen Z."
            elif 'literacy' in lower_title or 'education' in lower_title: takeaway = "Direct empirical proof that financial capability requires scalable, early intervention."
            feed_items.append({
                'source': 'NBER',
                'title': entry.title,
                'link': entry.link,
                'date': getattr(entry, 'published', 'Recent')[:16],
                'summary': entry.get('summary', '').replace('<p>', '').replace('</p>', '')[:200] + "...",
                'takeaway': takeaway
            })
    except: pass
    
    # 2. CFPB Newsroom
    try:
        d = feedparser.parse("https://www.consumerfinance.gov/about-us/newsroom/feed/")
        for entry in d.entries[:5]:
            feed_items.append({
                'source': 'CFPB',
                'title': entry.title,
                'link': entry.link,
                'date': getattr(entry, 'published', 'Recent')[:16],
                'summary': entry.get('summary', '').replace('<p>', '').replace('</p>', '')[:200] + "...",
                'takeaway': "Federal regulatory/enforcement action directly impacting consumer financial protection."
            })
    except: pass
    
    # 3. Industry News
    try:
        d = feedparser.parse("https://news.google.com/rss/search?q=%22financial+literacy%22+OR+%22financial+education%22")
        for entry in d.entries[:5]:
            feed_items.append({
                'source': 'Industry News',
                'title': entry.title,
                'link': entry.link,
                'date': getattr(entry, 'published', 'Recent')[:16],
                'summary': "Coverage of state-level mandates, institutional changes, or broad industry trends.",
                'takeaway': "Tracking public sentiment and legislative momentum for capability initiatives."
            })
    except: pass
    
    # Sort feeds by date fallback (just keep them grouped for now is fine, or random, they are strings)

    states_data_raw = [
        ("AL", "Alabama", "A", "Implemented for the Class of 2017. Requires a one-half credit course in Personal Finance."),
        ("AK", "Alaska", "F", "No state-wide standalone personal finance requirement for high school graduation."),
        ("AZ", "Arizona", "B", "Requires personal finance concepts to be embedded in economics or math, but no standalone course mandate."),
        ("AR", "Arkansas", "A", "Requires a standalone personal finance course. The requirement was strengthened by recent legislation."),
        ("CA", "California", "A", "AB 2927 signed in 2024. Guarantees a one-semester personal finance course starting with the Class of 2031."),
        ("CO", "Colorado", "C", "Standards are embedded in other courses; local districts make standalone decisions."),
        ("CT", "Connecticut", "A", "Passed legislation in 2023 requiring a personal finance course for the Class of 2027."),
        ("DE", "Delaware", "C", "Requires a half-credit course or equivalent integrated instruction for the Class of 2011 and beyond."),
        ("FL", "Florida", "A", "The Dorothy L. Hukill Financial Literacy Act guarantees a standalone course starting with the Class of 2027."),
        ("GA", "Georgia", "A", "Mandated a half-credit course in personal finance starting in 2024."),
        ("HI", "Hawaii", "F", "No state-wide standalone requirement. Schools offer courses as electives."),
        ("ID", "Idaho", "A", "Requires a financial literacy course integrated or as a standalone for graduation."),
        ("IL", "Illinois", "B", "Requires 9 weeks of consumer education, but not necessarily a standalone full semester course."),
        ("IN", "Indiana", "A", "SB 35 (2023) mandates a personal finance course for high school graduation (Class of 2028)."),
        ("IA", "Iowa", "A", "Requires a standalone personal finance course for graduation starting with the Class of 2023."),
        ("KS", "Kansas", "C", "No standalone course required, though standards exist."),
        ("KY", "Kentucky", "A", "Requires a financial literacy course for graduation, implemented for the Class of 2024."),
        ("LA", "Louisiana", "A", "Passed a mandate in 2023 requiring personal finance for graduation."),
        ("ME", "Maine", "C", "Embedded standards, but no standalone course requirement."),
        ("MD", "Maryland", "B", "Embedded standards, but no uniform statewide standalone requirement."),
        ("MA", "Massachusetts", "F", "No statewide requirement, though legislation has been frequently debated."),
        ("MI", "Michigan", "A", "Requires a half-credit personal finance course for graduation starting with the Class of 2028."),
        ("MN", "Minnesota", "A", "Signed into law in 2023, requiring a personal finance course for graduation."),
        ("MS", "Mississippi", "A", "Requires a standalone personal finance course for graduation."),
        ("MO", "Missouri", "A", "A pioneer state. Has required a one-half credit personal finance course for graduation since 2010."),
        ("MT", "Montana", "D", "No standalone requirement for high school graduation."),
        ("NE", "Nebraska", "A", "Requires a financial literacy course for graduation starting with the Class of 2024."),
        ("NV", "Nevada", "A", "Requires a standalone personal finance course for high school graduation."),
        ("NH", "New Hampshire", "A", "Requires a standalone personal finance course starting with the Class of 2027."),
        ("NJ", "New Jersey", "B", "Requires a half-credit of financial, economic, business, and entrepreneurial literacy. Not tracked as a standalone mandate by NGPF."),
        ("NM", "New Mexico", "C", "Requires personal finance as an elective option, but not a strict graduation mandate for all."),
        ("NY", "New York", "A", "Board of Regents recently moved to require personal finance for graduation."),
        ("NC", "North Carolina", "A", "Requires the EPF (Economics and Personal Finance) course for graduation starting Class of 2024."),
        ("ND", "North Dakota", "C", "No standalone mandate. Currently embedded in other subjects."),
        ("OH", "Ohio", "A", "Requires a one-half unit course in financial literacy for graduation starting Class of 2026."),
        ("OK", "Oklahoma", "B", "Requires the Passport to Financial Literacy, embedded rather than a strict standalone 1-semester course."),
        ("OR", "Oregon", "A", "Signed SB 3 in 2023, requiring a one-half credit personal finance course starting Class of 2027."),
        ("PA", "Pennsylvania", "A", "Passed Act 73 in 2023, requiring a standalone course starting Class of 2027."),
        ("RI", "Rhode Island", "A", "Requires a financial literacy course for graduation starting with the Class of 2024."),
        ("SC", "South Carolina", "A", "Requires a half-credit personal finance course starting with the Class of 2027."),
        ("SD", "South Dakota", "F", "Embedded within economics, no standalone requirement."),
        ("TN", "Tennessee", "A", "A pioneering state. Requires a standalone personal finance course for graduation since 2013."),
        ("TX", "Texas", "B", "Embedded in economics, but no standalone requirement for all graduation plans."),
        ("UT", "Utah", "A", "The gold standard pioneer. Required a half-credit standalone course since 2008 and fully funds it."),
        ("VT", "Vermont", "C", "No standalone state requirement."),
        ("VA", "Virginia", "A", "Requires a standalone Economics and Personal Finance course for graduation since 2015."),
        ("WA", "Washington", "C", "Requires districts to offer it, but it is not a state-mandated graduation requirement for students."),
        ("WV", "West Virginia", "A", "Requires a civics and personal finance course for graduation."),
        ("WI", "Wisconsin", "A", "Passed Act 60 in 2023, requiring a personal finance course for graduation starting Class of 2028."),
        ("WY", "Wyoming", "D", "No state-wide standalone personal finance requirement.")
    ]
    states_list = [{"code": c, "name": n, "grade": g, "details": d.replace('"', '&quot;').replace("'", "&#39;")} for c, n, g, d in states_data_raw]
    
    index_html = Template(HTML_TEMPLATE).render(briefs=briefs, feed_items=feed_items, states_list=states_list)
    with open('public/index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)

if __name__ == '__main__':
    build()
    print("Build complete in ./public")
