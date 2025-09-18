import re
import tkinter as tk
from typing import List, Dict, Tuple

from interface import NormaApp

LABEL_RE = re.compile(r'^\s*([0-9]+)\s*:\s*(.+)$', re.IGNORECASE)
COMMENT_RE = re.compile(r'#.*$')

if __name__ == '__main__':
    root = tk.Tk()
    app = NormaApp(root)
    root.mainloop()
