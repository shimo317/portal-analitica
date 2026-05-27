import os
import re

css_dir = "styles"
files_to_convert = [
    "calidad_datos.css",
    "descriptiva.css",
    "mineria_segmentacion.css",
    "predictiva.css",
    "prescriptiva.css"
]

header_fix = """/* ======= REGLAS COMPLEMENTARIAS ====== */
h1, h2, h3, h4, h5, h6, .hero-title, .top-userbar {
    color: #1D496D !important;
}
"""

for filename in files_to_convert:
    path = os.path.join(css_dir, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            css = f.read()
            
        # Fix semicolon syntax errors
        css = css.replace("color: #005187; !important;", "color: #005187 !important;")
        css = css.replace("color: #1D496D !important; !important;", "color: #1D496D !important;")
        css = css.replace("color: #476E95 !important; !important;", "color: #476E95 !important;")
        
        # File uploader background
        css = re.sub(r'background:\s*rgba\(30,41,59,0?\.75\)\s*!important;', 'background: #F8FAFC !important;', css)
        
        # File Uploader button & Download button text should be white to contrast with navy blue
        css = re.sub(r'color:\s*#005187\s*!important;\s*border:none', 'color: #FFFFFF !important; border:none', css)
        
        # Make sure Streamlit dark mode text globally doesn't override titles and userbar
        if "REGLAS COMPLEMENTARIAS" not in css:
            css = css.replace("/* ======= FORZAR MODO CLARO CORPORATIVO ======", header_fix + "\n/* ======= FORZAR MODO CLARO CORPORATIVO ======")
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(css)
        print(f"Patched {filename}")
