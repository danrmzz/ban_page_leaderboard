import subprocess
import sys

# Path to the Python interpreter in the virtual environment
python_executable = sys.executable

# List of worker scripts
worker_scripts = [
    "worker1.py",
    "worker2.py",
    "worker3.py",
    "worker4.py"
]

# Start all worker scripts
processes = [subprocess.Popen([python_executable, script], stdout=subprocess.PIPE, stderr=subprocess.PIPE) for script in worker_scripts]

# Wait for all processes to complete and print their outputs and errors
for process in processes:
    stdout, stderr = process.communicate()
    print(f"Process {process.pid} finished with return code {process.returncode}")
    if stdout:
        print(f"STDOUT:\n{stdout.decode()}")
    if stderr:
        print(f"STDERR:\n{stderr.decode()}")

print("All workers have completed.")
