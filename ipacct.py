#!/usr/bin/env python3
try:
    import ipaddress
except:
    import iptools.ipaddress as ipaddress

import iptools.iptools as iptools
import argparse
from sys import stderr

import settings

def match_args_row(args, row, all_none_match=False):
    s = (args.ip, args.block, args.name, args.type, args.desc, args.os, args.mac)
    if s == (None,) * len(s): return all_none_match

    # Eliminate

    if args.block:
        if row['ip'] not in args.block: return False
    else:
        if args.ip is not None and args.ip != row['ip']: return False 

    if args.name is not None and args.name != row['name']: return False
    if args.type is not None and args.type != row['type']: return False
    if args.desc is not None and args.desc != row['desc']: return False
    if args.os is not None and args.os != row['os']: return False

    return True

parser = argparse.ArgumentParser(description='IP address management util')

# Change args here
parser.add_argument('action', help='What to do [list|delete|add]')
parser.add_argument('--ip', type=ipaddress.ip_address, help='IP address')
parser.add_argument('--block', type=ipaddress.ip_network, help='IP network') # XXX -- allow list of blocks
parser.add_argument('--name', help='Name of the server')
parser.add_argument('--type', help='Server type (VPS, Native, Router, etc.)')
parser.add_argument('--desc', help='Server description')
parser.add_argument('--os', help='Operating system of the server')
parser.add_argument('--mac', help='MAC address of server')
args = parser.parse_args()

rows = [x for x in iptools.read_rows(settings.addrfile, settings.defaultorder)]
networks = [x for x in iptools.read_block(settings.blocksfile)]

if args.action == 'list':
    for row in rows:
        if match_args_row(args, row, all_none_match=True):
            print("{ip}: {name} (type: {type}) (description: {desc}) (os: {os})".format(**row))

    quit(0)

if args.action == 'add':
    # All these options mandatory
    s = (args.name, args.type, args.desc, args.os, args.mac)
    if s == (None,) * len(s): # Clever hack eh?
        print("Not enough arguments", file=stderr)
        parser.print_help()
        quit(1)

    # Either one must be specified
    if args.ip is None and args.block is None:
        print("Either --ip or --block must be specified", file=stderr)
        quit(1)
    elif args.ip is not None and args.block is not None:
        print("Ambiguous; either select --ip or --block, but not both.", file=stderr)
        quit(1)

    # XXX need more MAC checks
    macsplit = args.mac.split(':')
    if len(macsplit) not in (6, 8):
        print("Invalid MAC address", file=stderr)
        quit(1)

    # If a block, make sure the block is valid
    if args.block is not None: 
        if args.block not in networks:
            print("Block not found in networks file, typo?", file=stderr)
            quit(1)

        # List of IP's 
        addrlist = sorted([x['ip'] for x in rows])

        # Shitlisted IP's that aren't really usable
        shitlist = (args.block.network_address,     # The tin says it all
                    args.block.network_address + 1, # Typical gateway
                    args.block.broadcast_address)   # Tin says it it all

        # Scan for a free IP
        found = False
        for baddr in args.block:
            if baddr in addrlist: continue
            if baddr in shitlist: continue

            ip = baddr
            print("Free IP found! Address", ip)
            found = True
            break

        if not found:
            print("No free IP's found, aborting :(", file=stderr)
            quit(1)

    else: # IP address specified
        # Sanity check
        check = False
        ip = args.ip
        for net in networks:
            if ipaddress.ip_address(ip) in net:
                check = True
                break

        if not check:
            print("IP does not match existing netblocks, typo?", file=stderr)
            quit(1)

        # Check for uniqueness
        for row in rows:
            if row['ip'] == ip:
                print("IP is not unique", file=stderr)
                quit(1)

    # Now create the dict entry
    entry = {'ip' : ip, 'name' : args.name, 'type' : args.type,
             'desc' : args.desc, 'os' : args.os, 'mac' : args.mac}

    # Append
    rows.append(entry)

    # Write back
    iptools.write_rows(settings.addrfile, rows, settings.defaultorder)

    quit(0)

if args.action in ('del', 'delete', 'remove'):
    # If block is set, ignore it
    if args.block: args.block = None

    # Find the rows matching
    match = False
    for row in list(rows):
        if match_args_row(args, row):
            match = True
            rows.remove(row)

    if not match:
        print("Entry/entries not found", file=stderr)
        quit(1)

    # Write back
    iptools.write_rows(settings.addrfile, rows, settings.defaultorder)

    quit(0)

# No options found
parser.print_help()
quit(1)

