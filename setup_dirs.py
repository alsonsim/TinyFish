import os

# Create all directories
dirs = [
    'src',
    'src/agent',
    'src/sources', 
    'src/sentiment',
    'src/data',
    'src/trading',
    'src/utils',
    'tests',
    'scripts'
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

print("\nAll directories created successfully!")
