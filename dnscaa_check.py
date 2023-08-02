import argparse
import dns.resolver
from termcolor import colored
import subprocess
import logging
import threading
import sys

print_lock = threading.Lock()  # Lock to synchronize print statements

# Function to display banner
def banner():
    print("_________________________________________________________________________________________")
    print("")
    print("Tool for testing DNS CAA based on an input file of (sub)domains")
    print("Incorrectly configured DNS CAA configurations are by default written to output_DNSCAA.txt")
    print("")
    print("                                                                    Created by IllmaticJV")
    print("_________________________________________________________________________________________")
    print("")

# Function to check if 'dig' command is available
def check_dig_command():
    try:
        subprocess.run(['dig'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        logging.error("The 'dig' command is not found. Please install it to continue.")
        exit(1)

# Function to check DNS CAA for a given subdomain
def check_dns_caa(subdomain):
    try:
        answers = dns.resolver.resolve(subdomain, dns.rdatatype.CAA)
        if answers:
            return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
        return False

# Function to check DNS CAA for a given host (calls subdomain function)
def check_dns_caa_host(subdomain, verbose=False, output_file=None):
    check_dns_caa_subdomain(subdomain, verbose, output_file)

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
    return '.'.join(parts[-2:]) if len(parts) >= 2 else None

# Function to check if the parent domain has DNS CAA configured
def check_parent_domain(subdomain):
    parent_domain = get_parent_domain(subdomain)
    return check_dns_caa(parent_domain) if parent_domain else False

# Function to check DNS CAA for a given subdomain with verbose option and output file
def check_dns_caa_subdomain(subdomain, verbose=False, output_file=None):
    subdomain_exists = check_subdomain_existence(subdomain)
    dns_caa_status = check_dns_caa(subdomain)

    with print_lock:  # Lock to synchronize print statements
        if subdomain_exists:
            if dns_caa_status:
                status_color = "green"
                status_text = colored("Subdomain exists, DNS CAA configured", status_color)
            elif check_parent_domain(subdomain):
                status_color = "green"
                status_text = colored("Subdomain exists, inherits DNS CAA from parent domain", status_color)
            else:
                status_color = "red"
                status_text = colored("Subdomain exists, DNS CAA not configured", status_color)
                if output_file:
                    with open(output_file, 'a') as outfile:
                        outfile.write(f"\nDig output for {subdomain}:\n")
                        dig_output = get_dig_output(subdomain)
                        outfile.write(dig_output)
        else:
            status_color = "red"
            status_text = colored("Subdomain does not exist", status_color)

        print(colored(f"Subdomain: {subdomain}", "blue"))
        if verbose:
            print(f"\nDig output for {subdomain}:")
            dig_output = get_dig_output(subdomain)
            print(dig_output)
            if parent_domain := get_parent_domain(subdomain):
                print(f"\nDig output for {parent_domain}:")
                parent_dig_output = get_dig_output(parent_domain)
                print(parent_dig_output)
        print(colored(f"Status: {status_text}\n", status_color))

# Function to check DNS CAA for all subdomains from a file
def check_dns_caa_file(filename, verbose=False, output_file=None):
    try:
        with open(filename, 'r') as file:
            subdomains = file.read().splitlines()
    except FileNotFoundError:
        logging.error(f"File {filename} not found!")
        return

    with threading.BoundedSemaphore(10):  # Limit to 10 concurrent threads
        threads = [threading.Thread(target=check_dns_caa_subdomain, args=(subdomain, verbose, output_file)) for subdomain in subdomains]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

# Function to run 'dig' command for a given subdomain
def get_dig_output(subdomain):
    command = ['dig', 'CAA', subdomain]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout.strip()
    except FileNotFoundError:
        return "dig command not found"
    except subprocess.CalledProcessError as e:
        return f"dig command error: {e.stderr}"

# Main function
if __name__ == "__main__":
    banner()

    # Manual argument parsing
    verbose = False
    output_file = "output_DNSCAA.txt"  # Default output file
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

    check_dig_command()

    # Check DNS CAA for file or host based on the input flags
    if filename:
        check_dns_caa_file(filename, verbose, output_file)
    elif host:
        check_dns_caa_host(host, verbose, output_file)
    else:
        print("Usage: python script.py [-f filename | -h hostname] [-v] [-o output_file]")
