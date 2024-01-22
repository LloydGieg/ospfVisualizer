#!/usr/bin/env python3

import re
from ipaddress import IPv4Network
import json
import cgi
import tempfile
import os

debugfile = '/tmp/ospfvisualizer.debug'


def buildhosts(infile):
    outhosts = {}
    hostre = re.compile(r"^([0-9.]+)\s+(\S+).*$")
    with open(infile, 'r') as f:
        inhosts = f.read().split('\n')
    for x in inhosts:
        if hostre.match(x):
            outhosts[hostre.match(x).group(1)] = hostre.match(x).group(2)
    return outhosts


def buildjson(infile, hostdata):
    nodes = set()
    links = []
    jsonout = {
        "nodes": [],
        "links": []
    }
    nodere = re.compile(r'^\s+Link State ID: ([0-9.]+).*$')
    linkre = re.compile(r'^\s+Link connected to: (.*)$')
    stubipre = re.compile(r'^\s+\(Link ID\) Network/subnet number: ([0-9.]+).*$')
    stubmaskre = re.compile(r'^\s+\(Link Data\) Network Mask: ([0-9.]+).*$')
    transitre = re.compile(r'^\s+\(Link ID\) Designated Router address: ([0-9.]+).*$')
    nodenamelinkre = re.compile(r'^link-(.*)$')
    nodenamelanre = re.compile(r'^lan-(.*)$')
    nodenamehostre = re.compile(r'^host-(.*)$')

    with open(infile, 'r') as f:
        indata = f.read().split('\n')

    curnode = ''
    for idx, x in enumerate(indata):
        if nodere.match(x):
            curnode = "host-" + nodere.match(x).group(1)
            nodes.add(curnode)
        elif linkre.match(x):
            if linkre.match(x).group(1) == 'a Stub Network':
                if stubipre.match(indata[idx + 1]) and stubmaskre.match(indata[idx + 2]):
                    stubip = stubipre.match(indata[idx + 1]).group(1)
                    stubmask = IPv4Network("0.0.0.0/" + stubmaskre.match(indata[idx + 2]).group(1)).prefixlen
                    nodes.add(f"link-{stubip}/{stubmask}")
                    links.append({curnode: f"link-{stubip}/{stubmask}"})
            elif linkre.match(x).group(1) == 'a Transit Network':
                if transitre.match(indata[idx + 1]):
                    lan = transitre.match(indata[idx + 1]).group(1)
                    nodes.add(f"lan-{lan}")
                    links.append({curnode: f"lan-{lan}"})
    for x in nodes:
        if nodenamelinkre.match(x):
            jsonout["nodes"].append({"id": x, "name": nodenamelinkre.match(x).group(1), "asset": "link.png"})
        elif nodenamelanre.match(x):
            jsonout["nodes"].append({"id": x, "name": "LAN", "asset": "cloud.png"})
        elif nodenamehostre.match(x):
            if nodenamehostre.match(x).group(1) in hostdata:
                thishost = hostdata[nodenamehostre.match(x).group(1)]
            else:
                thishost = nodenamehostre.match(x).group(1)
            jsonout["nodes"].append({"id": x, "name": thishost, "asset": "router.png"})
    for x in links:
        for y in x:
            jsonout["links"].append({"source": y, "target": x[y]})
    return jsonout


def main():
    host_data = {}
    form = cgi.FieldStorage()
    if 'inhosts' in form:
        inhosts = form['inhosts']
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(inhosts.file.read())
        host_data = buildhosts(temp_filename)
        os.remove(temp_filename)
    if 'indata' in form:
        infile = form['indata']
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(infile.file.read())
        json_data = buildjson(temp_filename, host_data)
        print("Content-type: application/json\n")
        print(json.dumps(json_data))
        os.remove(temp_filename)
    else:
        print("Content-type: text/plain\n")
        print("No file uploaded")


if __name__ == '__main__':
    main()
