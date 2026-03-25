import re

with open("f:/vv/index.html", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Extract <style>...</style> (but ignore the one with id="admin-custom-css")
style_pattern = re.compile(r'<style(?:(?!id="admin-custom-css").)*?>(.*?)</style>', re.DOTALL | re.IGNORECASE)
styles = style_pattern.findall(text)

if styles:
    combined_css = "\n".join(styles)
    with open("f:/vv/style.css", "a", encoding="utf-8") as f:
        f.write("\n/* --- Extracted from index.html --- */\n")
        f.write(combined_css)
    # Remove from HTML
    text = style_pattern.sub(r'<!-- Inline CSS extracted to style.css -->', text)

# 2. Extract <script>...</script> (only those without 'src=')
# This regex matches <script> tags that don't have 'src' attributes.
script_pattern = re.compile(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', re.DOTALL | re.IGNORECASE)

# We want to keep small scripts like GA4, so let's only extract scripts > 500 chars (the main app logic)
# Actually, it's safer to extract all non-src scripts except specific ones if they have GA4.
# Let's use a replacement function
extracted_js = []

def script_replacer(match):
    content = match.group(1)
    # Ignore GA4 or specific tiny scripts if needed, but keeping them inline is fine.
    if 'gtag(' in content or 'window.dataLayer' in content or len(content.strip()) < 150:
        return match.group(0) # Do not extract
    extracted_js.append(content)
    return '<!-- Inline JS extracted to main.js -->'

text = script_pattern.sub(script_replacer, text)

if extracted_js:
    combined_js = "\n\n/* --- Extracted from index.html --- */\n\n".join(extracted_js)
    with open("f:/vv/main.js", "a", encoding="utf-8") as f:
        f.write("\n\n/* --- Extracted from index.html --- */\n\n")
        f.write(combined_js)
    
    # Ensure <script src="main.js" defer></script> is in the HTML.
    if 'src="main.js"' not in text and "src='main.js'" not in text:
        # Add it before </body>
        text = text.replace('</body>', '<script src="main.js" defer></script>\n</body>')

with open("f:/vv/index.html", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Extracted {len(styles)} style blocks and {len(extracted_js)} script blocks.")
print(f"index.html size reduced to {len(text)} bytes.")
