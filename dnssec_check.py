import argparse
import dns.resolver
from termcolor import colored
import subprocess
import threading
import logging
import sys

# Thread lock for synchronizing print statements
print_lock = threading.Lock()

# Function to display banner
def banner():
    print("________________________________________________________________________________________")
    print("")
    print("Tool for testing DNSSEC based on an input file of (sub)domains")
    print("Incorrectly configured DNSSEC configurations are by default written to output_DNSSEC.txt")
    print("")
    print("                                                                   Created by IllmaticJV")
    print("________________________________________________________________________________________")
    print("")

# Function to check if 'dig' command is available
def check_dig_command():
    try:
        subprocess.run(['dig'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        logging.error("The 'dig' command is not found. Please install it to continue.")
        exit(1)

# Function to check DNSSEC for a given subdomain
def check_dnssec(subdomain):
    try:
        answers = dns.resolver.resolve(subdomain, dns.rdatatype.DNSKEY)
        if answers:
            return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
        return False

# Function to check if a given subdomain exists
def check_subdomain_existence(subdomain):
    try:
        answers = dns.resolver.resolve(subdomain, rdtype=dns.rdatatype.A)
        if answers:
            return True
    except (dns.resolver.NXDOMAIN, dns.exception.DNSException):
        return False

# Function to get parent domain of a given subdomain
def get_parent_domain(subdomain):
    parts = subdomain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    else:
        return None

# Function to run 'dig' command for a given subdomain
def get_dig_output(subdomain):
    command = ['dig', 'DNSKEY', subdomain]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return "dig command not found"
    except subprocess.CalledProcessError as e:
        return f"dig command error: {e.stderr}"

# Function to print the DNSSEC status for a given subdomain
def print_status(subdomain, verbose=False, output_file=None):
    with print_lock:
        check_dnssec_subdomain(subdomain, verbose, output_file)

# Function to check DNSSEC for a given subdomain with verbose option and output file
def check_dnssec_subdomain(subdomain, verbose=False, output_file=None):
    subdomain_exists = check_subdomain_existence(subdomain)
    dnssec_status = check_dnssec(subdomain)
    parent_domain = get_parent_domain(subdomain)

    if subdomain_exists:
        if dnssec_status:
            status_color = "green"
            status_text = colored("Subdomain exists, DNSSEC enabled", status_color)
        elif parent_domain and check_dnssec(parent_domain):
            status_color = "green"
            status_text = colored("Subdomain exists, inherits DNSSEC from parent domain", status_color)
        else:
            status_color = "red"
            status_text = colored("Subdomain exists, DNSSEC disabled", status_color)
            # Write dig output to file if specified
            if output_file:
                with open(output_file, 'a') as outfile:
                    outfile.write(f"\nDig output for {subdomain}:\n")
                    dig_output = get_dig_output(subdomain)
                    outfile.write(dig_output)
    else:
        status_color = "red"
        status_text = colored("Subdomain does not exist", status_color)

    print(colored(f"Subdomain: {subdomain}", "blue"))

    # Print additional information if verbose flag is provided
    if verbose:
        print(f"\nDig output for {subdomain}:")
        dig_output = get_dig_output(subdomain)
        print(dig_output)
        if parent_domain:
            print(f"\nDig output for {parent_domain}:")
            parent_dig_output = get_dig_output(parent_domain)
            print(parent_dig_output)

    print(colored(f"Status: {status_text}\n", status_color))

# Function to check DNSSEC for all subdomains from a file
def check_dnssec_file(filename, verbose=False, output_file=None):
    try:
        with open(filename, 'r') as file:
            subdomains = file.read().splitlines()
    except FileNotFoundError:
        logging.error(f"File {filename} not found!")
        return

    # Create threads with a limit of 10 concurrent threads
    with threading.BoundedSemaphore(10): 
        threads = [threading.Thread(target=print_status, args=(subdomain, verbose, output_file)) for subdomain in subdomains]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

# Main function
if __name__ == "__main__":
    banner()
    check_dig_command()

    # Manual argument parsing
    verbose = False
    output_file = "output_DNSSEC.txt" # Default output file
    filename = None
    host = None

    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '-f' and i < len(sys.argv) - 1:
            filename = sys.argv[i + 1]
            i += 1
        elif arg == '-v':
            verbose = True
        elif arg == '-o' and i < len(sys.argv) - 1:
            output_file = sys.argv[i + 1]
            i += 1
        elif arg == '-h' and i < len(sys.argv) - 1:
            host = sys.argv[i + 1]
            i += 1
        i += 1

    # Check DNSSEC for file or host based on the input flags
    if filename:
        check_dnssec_file(filename, verbose, output_file)
    elif host:
        print_status(host, verbose, output_file)
    else:
        print("Usage: python script.py [-f filename] [-h host] [-v] [-o output_file]")
