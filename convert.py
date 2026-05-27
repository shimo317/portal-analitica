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

def process_css(content):
    # 1. Backgrounds & Gradients
    content = re.sub(r'background:\s*radial-gradient[^;]*;', 'background: #F3FAFF !important;', content, flags=re.IGNORECASE|re.DOTALL)
    # The .stApp rule might have been split, let's catch linear-gradient for stApp if it survived:
    content = re.sub(r'\.stApp\s*\{[^}]*\}', '.stApp{\\n  background: #F3FAFF !important;\\n  color: #1D496D;\\n}', content)
    
    # 2. Hero wrap
    content = re.sub(r'background:\s*linear-gradient\(180deg,\s*rgba\(255,255,255,0\.06\).*?\)', 'background: #FFFFFF !important', content)
    # Generic dark panel gradients
    content = re.sub(r'linear-gradient\(180deg,\s*rgba\((?:30|2|15).*?\)', '#FFFFFF', content)
    content = re.sub(r'linear-gradient\(180deg,\s*rgba\((?:30|2|15).*?\)', '#FFFFFF', content)
    # The table-wrap specifically:
    content = re.sub(r'rgba\(2,6,23,\.75\)', '#EAF3FF', content)
    
    # 3. Shadows
    content = re.sub(r'rgba\(0,0,0,0?\.[34]\d*\)', 'rgba(0, 81, 135, 0.08)', content)
    
    # 4. Borders
    content = re.sub(r'rgba\(34,211,238,0?\.[1-9]\d*\)', 'rgba(132, 182, 244, 0.4)', content)
    content = re.sub(r'rgba\(148,163,184,0?\.[1-9]\d*\)', 'rgba(132, 182, 244, 0.22)', content)
    
    # 5. Buttons (cyan gradient to navy, dark text to white text)
    # div.stDownloadButton > button, div.stFileUploader button, div[data-testid="stButton"] > button
    content = re.sub(r'background:\s*linear-gradient\(135deg,\s*#22D3EE.*?#60A5FA\)\s*!important;', 'background: #004578 !important;', content)
    content = re.sub(r'color:\s*#07101D\s*!important;', 'color: #FFFFFF !important;', content)
    
    # 6. Highlights & Accents
    content = re.sub(r'#22D3EE', '#4D82BC', content) # cyan to soft blue
    
    # 7. Text colors
    content = re.sub(r'color:\s*#FFFFFF;?', 'color: #005187;', content) # strong white to navy
    content = re.sub(r'color:\s*rgba\(255,255,255,0?\.[9]\d*\)[;!]*', 'color: #1D496D !important;', content) # near white to dark blue
    content = re.sub(r'color:\s*rgba\(226,232,240,0?\.[789]\d*\)[;!]*', 'color: #476E95 !important;', content) # muted white to slate blue
    
    # Pill badges inside hero
    content = re.sub(r'background:\s*rgba\(2,6,23,0?\.25\)', 'background: #EAF3FF', content)
    
    # Sidebar
    content = re.sub(r'section\[data-testid="stSidebar"\]\s*\{(.*?)\}', r'section[data-testid="stSidebar"]{ \1 \n  background: linear-gradient(180deg, #EAF3FF 0%, #FCFFFF 100%) !important;\n}', content, flags=re.DOTALL)
    
    # Table rows
    content = re.sub(r'rgba\(255,255,255,\.03\)', 'rgba(0, 81, 135, 0.04)', content)
    content = re.sub(r'rgba\(255,255,255,\.01\)', 'transparent', content)
    
    # Code tags inside panels
    content = re.sub(r'color:#07101D !important;', 'color:#1D496D !important;', content)
    content = re.sub(r'background:rgba\(34,211,238,\.95\) !important;', 'background:#D6E3FA !important;', content)
    
    return content

for filename in files_to_convert:
    path = os.path.join(css_dir, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            css = f.read()
        
        new_css = process_css(css)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_css)
        print(f"Processed {filename}")
    else:
        print(f"Skipped {filename} (not found)")
