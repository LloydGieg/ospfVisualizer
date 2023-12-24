#!/usr/bin/env python3

import re
from ipaddress import IPv4Network
import json
import cgi
import tempfile
import os


def buildjson(infile):
    nodes = set()
    links = []
    jsonout = {
        "nodes": [],
        "links": []
    }
    nodere = re.compile(r'^\s+Link State ID: ([0-9.]+)$')
    linkre = re.compile(r'^\s+Link connected to: (.*)$')
    stubipre = re.compile(r'^\s+\(Link ID\) Network/subnet number: ([0-9.]+)$')
    stubmaskre = re.compile(r'^\s+\(Link Data\) Network Mask: ([0-9.]+)$')
    transitre = re.compile(r'^\s+\(Link ID\) Designated Router address: ([0-9.]+)$')

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
        if 'link-' in x:
            jsonout["nodes"].append({"id": x, "name": x, "asset": "link.png"})
        elif 'lan-' in x:
            jsonout["nodes"].append({"id": x, "name": "LAN", "asset": "cloud.png"})
        else:
            jsonout["nodes"].append({"id": x, "name": x, "asset": "router.png"})
    for x in links:
        for y in x:
            jsonout["links"].append({"source": y, "target": x[y]})
    return json.dumps(jsonout)


def main():
    form = cgi.FieldStorage()
    if 'indata' in form:
        infile = form['indata']
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(infile.file.read())
        json_data = buildjson(temp_filename)
        print("Content-type: application/json\n")
        print(json_data)
        os.remove(temp_filename)
    else:
        print("Content-type: text/plain\n")
        print("No file uploaded")


if __name__ == '__main__':
    main()
