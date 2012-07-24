try:
    # Python 3.3
    import ipaddress
except:
    # Fallback (local copy)
    from . import ipaddress as ipaddress

import csv

def write_rows(file, rows, order):
    # Sort the rows before writing by IP address
    rows = sorted(rows, key=lambda x: ipaddress.ip_address(x['ip']))

    with open(file, 'w', newline='') as f:
        writer = csv.DictWriter(f, order, quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            # Deconvert
            row['ip'] = str(row['ip'])
            writer.writerow(row)

def read_rows(file, order):
    with open(file, newline='') as f:
        for row in csv.DictReader(f, order, quoting=csv.QUOTE_MINIMAL):
            # Convert
            row['ip'] = ipaddress.ip_address(row['ip'])
            yield row

def read_block(file):
    with open(file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or line == '': continue
            yield ipaddress.ip_network(line)

