# Script Wrapper for testssl, DNSSEC and DNS CAA checks

This Python script acts as a wrapper for various security checks, including DNSCAA, DNSSEC, and testssl. It allows you to clone the `testssl.sh` repository, run Python scripts for DNSCAA and DNSSEC checks, and launch bash processes to check the SSL configurations of given hostnames.

## Requirements

- Python 3.x
- Git (to clone the `testssl.sh` repository)

## Installation

1. Clone this repository.
2. Install the required Python packages using:

   ```bash
   pip3 install -r requirements.txt
   ```
   
##  Usage
You can run the script using one of the following commands, depending on whether you are providing a single hostname or a file containing multiple hostnames.

For a single hostname:
   ```bash
python3 multi_launcher.py -h [hostname]
   ```

For a file containing multiple hostnames:

   ```bash
python3 multi_launcher.py -f [filename]
   ```


Note:
For single hostname, a temporary file hostname.txt will be created and removed after the execution.

The cloned testssl.sh directory will remain in the script's location.

## Output
DNSCAA and DNSSEC checks are printed to the console. If there is any misconfigurations these are being outputted to a file. 

Testssl results are saved to CSV files with the naming pattern [hostname]_testssl.csv.
