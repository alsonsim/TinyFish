"""
Master setup script for TinyFish Financial Agent.
Runs all file creation scripts in sequence.
"""

import os
import sys
import subprocess

def run_script(script_name):
    """Run a Python script and report results."""
    print(f"\n{'='*60}")
    print(f"Running {script_name}...")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}:")
        print(e.stdout)
        print(e.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ Script not found: {script_name}")
        return False

def main():
    """Main setup orchestrator."""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║    🐟 TinyFish Financial Agent - Complete Setup 🐟       ║
    ║                                                           ║
    ║    AI-Powered Financial Sentiment Analysis System        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Create directories using Python
    print("\n📁 Step 1: Creating directory structure...")
    if os.path.exists("setup_dirs.py"):
        if not run_script("setup_dirs.py"):
            print("\n⚠️  Directory creation had issues, but continuing...")
    
    # Step 2: Run all file creation scripts
    scripts = [
        "create_files_part1.py",
        "create_files_part2.py", 
        "create_files_part3.py",
        "create_files_part4.py",
    ]
    
    success_count = 0
    for script in scripts:
        if os.path.exists(script):
            if run_script(script):
                success_count += 1
        else:
            print(f"⚠️  Script not found: {script}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SETUP SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Completed: {success_count}/{len(scripts)} file creation scripts")
    
    # Check if key files exist
    key_files = [
        "README.md",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "docker-compose.yml",
        "Dockerfile",
    ]
    
    print("\n📄 Key Files Check:")
    for f in key_files:
        status = "✅" if os.path.exists(f) else "❌"
        print(f"  {status} {f}")
    
    # Next steps
    print(f"\n{'='*60}")
    print("🚀 NEXT STEPS")
    print(f"{'='*60}")
    print("""
1. Install dependencies:
   python -m venv venv
   venv\\Scripts\\activate  (Windows)
   pip install -r requirements.txt

2. Configure environment:
   copy .env.example .env
   Edit .env with your API keys

3. Run tests:
   pytest tests/ -v

4. Start the agent:
   python -m src.agent.core

For detailed instructions, see INSTALLATION.md
    """)
    
    print("\n✨ Setup complete! Happy coding! 🐟\n")

if __name__ == "__main__":
    main()
