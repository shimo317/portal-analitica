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

prepend_block = """/* ======= FORZAR MODO CLARO CORPORATIVO ====== */
html, body, [class*="css"], [data-testid="stAppViewContainer"], .stApp {
    background: #F3FAFF !important;
    background-color: #F3FAFF !important;
    color: #1D496D !important;
}

"""

for filename in files_to_convert:
    path = os.path.join(css_dir, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            css = f.read()
        
        # 1. Add the global background block at the beginning
        if "FORZAR MODO CLARO" not in css:
            css = prepend_block + css
            
        # 2. Fix the broken CSS strings
        css = re.sub(r'background:\s*#FFFFFF\s*!important\)\s*!important;', 'background: #FFFFFF !important;', css)
        css = re.sub(r'background:\s*#FFFFFF\s*,\s*rgba.*?\)\)\s*!important;', 'background: #FFFFFF !important;', css)
        css = re.sub(r'background:\s*linear-gradient.*?#FFFFFF.*?rgba.*?\)\)\s*!important;', 'background: #FFFFFF !important;', css)
        css = re.sub(r'color:\s*#476E95\s*!important;\s*!important;', 'color: #476E95 !important;', css)
        css = re.sub(r'background:\s*linear-gradient\([^)]*#FFFFFF.*?\)', 'background: #FFFFFF !important', css)
        css = re.sub(r'background:\s*linear-gradient\(180deg,\s*rgba\(30,41,59,0.85\),\s*rgba\(15,23,42,0.78\)\)', 'background: #FFFFFF !important', css)
        
        # In case the table or interpret colors were messed up:
        css = re.sub(r'background:\s*linear-gradient\(180deg,\s*rgba\(30,41,59,.72\),\s*rgba\(2,6,23,.55\)\)', 'background: #FFFFFF !important', css)
        css = re.sub(r'background:\s*linear-gradient\(180deg,\s*rgba\(30,41,59,.65\),\s*rgba\(2,6,23,.45\)\)', 'background: #FFFFFF !important', css)
        
        # Check predictiva background fix just in case original wasn't completely cleared
        css = re.sub(r'background:\s*radial-gradient.*?(?:linear-gradient.*?)?;', 'background: #F3FAFF !important;', css, flags=re.DOTALL)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(css)
        print(f"Fixed {filename}")
