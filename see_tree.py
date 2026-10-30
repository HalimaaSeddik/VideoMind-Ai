import os

def print_tree(startpath):
    for root, dirs, files in os.walk(startpath):
        # Ignore hidden folders like .git, .venv, or __pycache__
        dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]
        
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f'{indent}├── {os.path.basename(root)}/')
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if not f.startswith('.'):
                print(f'{subindent}└── {f}')

print_tree(os.getcwd())
