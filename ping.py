"""Probes given sites and returns their RTTs and TTLs.

The probing parameters can be modified either by calling the methods with
custom values or by changing the module's PORT, TTL, TIMEOUT, and LOGGING
environment variables.
"""

import socket
import select
from os import times

# Result codes for the getRTT method
ERROR = -1
TOOLOW = 1
OK = 2

# Constants
BUFSIZE = 512
MAX_TTL = 128
MILLISECONDS = 1000
HEADER = 'Address,RTT,TTL'
RESULT = '{},{:.1f},{}'
RESULT_ERROR = '{},ERROR,ERROR'
HELP = '''Command-line use:
python {} probe [-l|--log] [-p|--port port] [-t|--timeout timeout] site1 site2 site3...
python {} probe [-l|--log] [-p|--port port] [-t|--timeout timeout] < sites'''

# Module environment variables
PORT = 33434
TTL = 16
TIMEOUT = 30
LOGGING = False


def main(addresses, port=PORT, timeout=TIMEOUT, logging=LOGGING):
    """Probes the given addresses and outputs their RTTs and TTLs.
    
    Keyword arguments:
    addresses -- the addresses to probe
    port -- the port to send/receive probes (default PORT variable)
    timeout -- the timeout value for giving up on unresponsive probes (default TIMEOUT variable)
    logging -- boolean determining whether or not to log all actions (default LOGGING variable)
    """
    log('Starting {}:\nPort: {}\nTimt: {}\nSites:'.format(__file__, port, timeout), logging)
    if logging:
        for address in addresses:
            log('  {}'.format(address))
    log('------------------------------------------', logging)
    print HEADER
    for address in addresses:
        log('Probing {}'.format(address), logging)
        rtt, ttl = probe(address, port, timeout, logging)
        if rtt is not ERROR:
            print RESULT.format(address, rtt, ttl)
        else:
            print RESULT_ERROR.format(address)
        log('', logging)


def probe(address, port=PORT, timeout=TIMEOUT, logging=LOGGING):
    """Probes the given address and outputs its RTT and TTL.
    
    Keyword arguments:
    address -- the address to probe
    port -- the port to send/receive probes (default PORT variable)
    timeout -- the timeout value for giving up on unresponsive probes (default TIMEOUT variable)
    logging -- boolean determining whether or not to log all actions (default LOGGING variable)
    """
    # Send an initial probe
    ttl = TTL
    result, last_rtt, last_ttl = getRTT(address, ttl, port, timeout, logging)
    if result is ERROR:
        return ERROR, ERROR

    # Probe, doubling TTL until we successfully reach the
    # destination or exceed the max TTL
    while result is not OK and ttl < MAX_TTL:
        ttl = ttl * 2
        result, rtt = getRTT(address, ttl, port, timeout, logging)
        if result is not ERROR:
            last_rtt = rtt
            last_ttl = ttl

    # Binary search for the correct TTL
    min_ttl = ttl / 2
    max_ttl = ttl
    while min_ttl < max_ttl and result is not ERROR:
        ttl = (min_ttl + max_ttl) // 2
        result, rtt = getRTT(address, ttl, port, timeout, logging)
        if result is TOOLOW:
            min_ttl = ttl + 1
        elif result is OK:
            max_ttl = ttl
            last_rtt = rtt
            last_ttl = ttl
    if result is not ERROR:
        last_rtt = rtt
        last_ttl = ttl

    # Return the last successful probe's RTT and TTL
    return last_rtt, last_ttl


def getRTT(address, ttl=TTL, port=PORT, timeout=TIMEOUT, logging=LOGGING):
    """Gets the status and RTT for the given address and ttl request.
    
    Keyword arguments:
    address -- the address to probe
    ttl -- the maximum time to live for the packet (default TTL variable)
    port -- the port to send/receive probes (default PORT variable)
    timeout -- the timeout value for giving up on unresponsive probes (default TIMEOUT variable)
    logging -- boolean determining whether or not to log all actions (default LOGGING variable)
    """
    # Create the sockets
    try:
        dest = socket.gethostbyname(address)
    except:
        return ERROR, 0, 0
    recv = socket.socket(socket.AF_INET,
                         socket.SOCK_RAW,
                         socket.getprotobyname('icmp'))
    send = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM,
                         socket.getprotobyname('udp'))
    send.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)

    # Send the probe
    result = ERROR
    start_time = times()[4]
    recv.bind(('', port))
    log('{0}: Sending to {1}:{2} with TTL of {3}...'.format(start_time, dest, port, ttl), logging)
    packet = "\x08\x00M5\x00\x01\x00&abcdefghijklmnopqrstuvwabcdefghi"
    send.sendto(packet, (dest, port))

    # Wait for a resonse or timeout
    try:
        log('Waiting for response...', logging)
        recv.setblocking(0)
        ready = select.select([recv], [], [], timeout)
        addr = None
        if ready[0]:
            _, addr = recv.recvfrom(BUFSIZE)
        if not addr:
            log('Error: attempt timed out', logging)
            return ERROR, ERROR, ERROR
        try:
            response = socket.gethostbyaddr(addr[0])[0]
            if response == address or addr[0] == dest:
                log('Got response from destination, TTL high enough', logging)
                result = OK
            else:
                log('Got response from {0}'.format(response), logging)
                result = TOOLOW
        except:
            if addr[0] == dest:
                log('Got response from destination, TTL high enough', logging)
                result = OK
            else:
                log('Got response from {0}'.format(addr[0]), logging)
                result = TOOLOW
    except socket.error:
        log('Error: connecting to socket failed.', logging)
        return ERROR, ERROR, ERROR
    finally:
        send.close()
        recv.close()

    # Stop counting and get the result and RTT
    end_time = times()[4]
    log('{0}: Finished probe attempt.'.format(end_time), logging)
    return result, (end_time - start_time) * MILLISECONDS


def log(message, logging=LOGGING):
    """Logs the message if logging is on."""
    if logging:
        print message

from sys import argv, stdin
if __name__ == '__main__':
    # Set defaults for command-line use
    sites = []
    logging = False
    port = PORT
    timeout = TIMEOUT

    # Parse any command line flags
    i = 1
    while i < len(argv):
        if argv[i] == '-l' or argv[i] == '--log':
            logging = True
            i = i + 1
        elif argv[i] == '-p' or argv[i] == '--port':
            port = int(argv[i+1])
            i = i + 2
        elif argv[i] == '-t' or argv[i] == '--timeout':
            timeout = int(argv[i+1])
            i = i + 2
        else:
            break

    # Read in the sites to probe
    if len(argv) is i:
        for site in stdin:
            sites.append(site.strip())
    else:
        sites = argv[i:]

    # Only start if we have sites to probe
    if len(sites) > 0:
        main(sites, port, timeout, logging)
    else:
        print HELP
