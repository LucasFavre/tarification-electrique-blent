import subprocess
import time

def run_benchmark():
    command = "wrk -t100 -c100 -d60s http://35.205.178.175/tarification-electrique?code_commune=77081&code_region=11"
    # Adjust parameters according to your requirements:
    # -t: Number of threads
    # -c: Number of connections
    # -d: Duration of the test

    start_time = time.time()
    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    end_time = time.time()

    if process.returncode == 0:
        print("Benchmark completed successfully.")
        print(stdout.decode())
        print("Execution time:", end_time - start_time, "seconds")
    else:
        print("Benchmark failed.")
        print(stderr.decode())

if __name__ == "__main__":
    run_benchmark()