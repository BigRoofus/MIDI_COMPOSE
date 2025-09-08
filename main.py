# this is the main entry/starting point for the app.

# AST-based one-liner auto-installer
import sys,subprocess,importlib,inspect,ast;exec("""
f=inspect.currentframe()
while f.f_back:f=f.f_back
with open(f.f_code.co_filename,'r') as file:tree=ast.parse(file.read())
imports=set()
for node in ast.walk(tree):
    if isinstance(node,ast.Import):[imports.add(a.name.split('.')[0]) for a in node.names]
    elif isinstance(node,ast.ImportFrom) and node.module:imports.add(node.module.split('.')[0])
builtins={'sys','os','time','datetime','json','re','math','random','collections','itertools','functools','operator','string','io','pathlib','urllib','http','socket','threading','multiprocessing','subprocess','argparse','logging','unittest','csv','xml','html','email','base64','hashlib','hmac','secrets','uuid','pickle','shelve','sqlite3','zlib','gzip','bz2','lzma','tarfile','zipfile','configparser','tempfile','shutil','glob','fnmatch','ast','inspect','dis','importlib','tkinter'}
mappings={'cv2':'opencv-python','PIL':'Pillow','yaml':'PyYAML','sklearn':'scikit-learn','bs4':'beautifulsoup4','serial':'pyserial','skimage':'scikit-image'}
for m in imports-builtins:
    try:importlib.import_module(m)
    except ImportError:subprocess.check_call([sys.executable,'-m','pip','install',mappings.get(m,m)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
""")