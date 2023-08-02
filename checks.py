import sys
import threading
import subprocess
import concurrent.futures
from termcolor import colored
import time
import os
from pathlib import Path
from contextlib import contextmanager

# Define the absolute path of the directory where this Python script is located
SCRIPT_LOCATION = Path(__file__).absolute().parent

@contextmanager
def change_dir(new_dir):
    # Save the current working directory
    old_dir = os.getcwd()
    # Change to the new directory
    os.chdir(new_dir)
    try:
        yield
    finally:
        # Change back to the original directory
        os.chdir(old_dir)

def clone_testssl():
    with change_dir(SCRIPT_LOCATION):
        if not os.path.exists('testssl.sh'):
            print(colored("Cloning testssl.sh from GitHub...", "blue"))
            subprocess.run(['git', 'clone', 'https://github.com/drwetter/testssl.sh.git'])
            print(colored("Cloning completed.", "green"))
        else:
            print(colored("testssl.sh already present in the current directory.", "green"))


def launch_python_script1(hostname_file):
    script_path = SCRIPT_LOCATION / 'dnscaa_check.py'
    result = subprocess.run(['python3', str(script_path), "-f", hostname_file], capture_output=True, text=True)
    print(f"DNSCAA output:\n{result.stdout}")

def launch_python_script2(hostname_file):
    script_path = SCRIPT_LOCATION / 'dnssec_check.py'
    result = subprocess.run(['python3', str(script_path), "-f", hostname_file], capture_output=True, text=True)
    print(f"DNSSEC output:\n{result.stdout}")

def launch_bash_script(hostname_file):
    with open(hostname_file, 'r') as file:
        hostnames = file.read().splitlines()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(launch_bash_process, hostname) for hostname in hostnames]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(colored(f"Error occurred: {str(e)}","red"))

def launch_bash_process(hostname):
    bash_script_path = SCRIPT_LOCATION / 'testssl.sh' / 'testssl.sh'
    file = hostname + "_testssl.csv"
    print(colored(f"Launching testssl for hostname {hostname}\n", "blue"))
    subprocess.run(['bash', str(bash_script_path), '--severity','LOW','--quiet', '--csvfile', file, hostname], stdout=subprocess.DEVNULL)
    print(colored(f"TestSSL output for hostname {hostname} outputted to {file}\n", "green"))

def create_hostname_file(hostname):
    with open('hostname.txt', 'w') as file:
        file.write(hostname)

def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ['-f', '-h']:
        print("Usage: python wrapper.py [-f filename | -h hostname]")
        return

    clone_testssl()

    use_file = sys.argv[1] == '-f'

    if use_file:
        hostname_file = sys.argv[2]
    else:
        hostname = sys.argv[2]
        create_hostname_file(hostname)
        hostname_file = 'hostname.txt'

    python_thread1 = threading.Thread(target=launch_python_script1, args=(hostname_file,))
    python_thread2 = threading.Thread(target=launch_python_script2, args=(hostname_file,))
    bash_thread = threading.Thread(target=launch_bash_script, args=(hostname_file,))

    python_thread1.start()
    python_thread2.start()
    bash_thread.start()

    python_thread1.join()
    python_thread2.join()
    bash_thread.join()

    if not use_file:
        subprocess.run(['rm', 'hostname.txt'])

if __name__ == '__main__':
    main()
