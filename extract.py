import os, glob

path = os.path.expanduser(r'~/.gemini/antigravity/conversations/*.pb')
files = glob.glob(path)
print(f"Found {len(files)} pb files in {path}")

for f in files:
    if 'e019ed68-fff5-4064-b370-cbbce77ffa03.pb' in f or '3de8d3be-9d1b-4ea8-bf5e-2289ae0656b5.pb' in f:
        with open(f, 'rb') as file:
            content = file.read().decode('utf-8', errors='ignore')
            print(f"--- {os.path.basename(f)} --- (Size: {len(content)})")
            
            # Print any text blocks longer than 20 chars
            import re
            text_blocks = re.findall(r'[a-zA-Z0-9ğüşıöçĞÜŞİÖÇ\s\.,!\?]{20,}', content)
            for i, block in enumerate(text_blocks):
                if 'teknopark' in block.lower() or 'eksik' in block.lower() or 'kategori' in block.lower():
                    print(f"MATCH: {block[:200]}")
