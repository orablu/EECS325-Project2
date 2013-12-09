EECS325-Project2
================

A hops/RTT measuring script for Case Western Reserve University's EECS 325 Networks class. Probes given sites and returns their RTTs and TTLs.

The probing parameters can be modified either by calling the methods with
custom values or by changing the module's PORT, TTL, TIMEOUT, and LOGGING
environment variables.

# How to Use
Help will be displayed if you just run `python probe.py`.

## Command-line use:
    python {0} probe [-l|--log] [-p|--port port] [-t|--timeout timeout] site1 site2 site3...
    python {0} probe [-l|--log] [-p|--port port] [-t|--timeout timeout] < sites

## Module use:
    from probe import probe
    probe(address, port, timeout, logging)
