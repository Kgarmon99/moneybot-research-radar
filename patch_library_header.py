with open("build.py", "r") as f:
    content = f.read()

old_tab = """        <!-- TAB: LIBRARY -->
        <div id="library" class="tab-content">
            <input type="text" id="searchLibrary" class="search-bar" placeholder="Search curated briefs, memos, and tags..." onkeyup="filterCards('libraryCards', 'searchLibrary')">"""

new_tab = """        <!-- TAB: LIBRARY -->
        <div id="library" class="tab-content">
            <div style="margin-bottom: 25px;">
                <h2 style="font-size: 1.5rem; margin-bottom: 5px;">Curated Intelligence</h2>
                <p style="color: var(--accent); font-size: 0.95rem;">Internal policy briefs, academic syntheses, and macro trend analysis shaping the MoneyBot intervention framework.</p>
            </div>
            <input type="text" id="searchLibrary" class="search-bar" placeholder="Search curated briefs, memos, and tags..." onkeyup="filterCards('libraryCards', 'searchLibrary')">"""

content = content.replace(old_tab, new_tab)

with open("build.py", "w") as f:
    f.write(content)

print("Patched Library Header")
