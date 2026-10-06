"""Run the full pipeline: python run_pipeline.py"""
import subprocess, sys
for script in ["src/01_generate_data.py", "src/02_clean_data.py", "src/03_load_to_db.py"]:
    subprocess.run([sys.executable, script], check=True)
