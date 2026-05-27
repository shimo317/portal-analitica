import os

css_dir = "styles"
files_to_convert = [
    "calidad_datos.css",
    "descriptiva.css",
    "mineria_segmentacion.css",
    "predictiva.css",
    "prescriptiva.css"
]

definitive_text_fix = """/* ======= FORZAR MODO CLARO CORPORATIVO ====== */
html, body, [class*="css"], [data-testid="stAppViewContainer"], .stApp {
    background: #F3FAFF !important;
    background-color: #F3FAFF !important;
    color: #1D496D !important;
}

h1, h2, h3, h4, h5, h6, .hero-title {
    color: #005187 !important;
}

.top-userbar, .top-userbar * {
    color: #005187 !important;
}

[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] div {
    color: #1D496D;
}

.panel, .panel div, .panel span, .panel small {
    color: #1D496D !important;
}

.word-card *, .interpret-card * {
    color: #1D496D;
}

button[kind="primary"] *, div.stDownloadButton button * {
    color: inherit;
}
"""

for filename in files_to_convert:
    path = os.path.join(css_dir, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            css = f.read()
            
        # We need to replace everything from "/* ======= FORZAR MODO CLARO CORPORATIVO ======" 
        # up to the end of the previous header block.
        # But wait, we can just replace the whole existing block.
        if "/* ======= REGLAS COMPLEMENTARIAS ====== */" in css:
            pos1 = css.find("/* ======= REGLAS COMPLEMENTARIAS ====== */")
            pos2 = css.find("/* ================= HERO")
            if pos1 != -1 and pos2 != -1:
                css = definitive_text_fix + "\n" + css[pos2:]
        elif "/* ======= FORZAR MODO CLARO CORPORATIVO ======" in css:
            pos1 = css.find("/* ======= FORZAR MODO CLARO CORPORATIVO ======")
            pos2 = css.find("/* ================= HERO")
            if pos1 != -1 and pos2 != -1:
                css = definitive_text_fix + "\n" + css[pos2:]

        # Make sure pills maintain their color
        css = css.replace("color: #476E95 !important;", "color: #005187 !important;")
        # Fix button texts
        css = css.replace("color: #005187 !important;\n  border:none !important;", "color: #FFFFFF !important;\n  border:none !important;")

        with open(path, 'w', encoding='utf-8') as f:
            f.write(css)
        print(f"Text fixed {filename}")
