import socket
import select
from os import times

# Result codes for the getRTT method
ERROR = -1
UNKNOWN = 0
TOOLOW = 1
OK = 2

# Constants
BUFSIZE = 512
LOGGING = False
MILLISECONDS = 1000
PORT = 33434
HEADER = 'RTT\tTTL'
RESULT = '{0:.1f}\t{1}'
RESULT_ERROR = RESULT.format(-1., -1.)
TTL = 16
TIMEOUT = 30


def main(addresses, port=PORT, timeout=TIMEOUT, logging=LOGGING):
    log('Starting {} with port {}'.format(__file__, port))
    print HEADER
    for address in addresses:
        log('Pinging {}'.format(address), logging)
        rtt, ttl = ping(address, port, timeout, logging)
        if rtt is not ERROR:
            print RESULT.format(rtt, ttl)
        else:
            print RESULT_ERROR


def ping(address, port=PORT, timeout=TIMEOUT, logging=LOGGING):
    '''
    Pings an address and returns the rtt and ttl.
    '''
    ttl = TTL
    result, rtt, _ = getRTT(address, ttl, port, timeout, logging)
    if result is ERROR:
        return ERROR, ERROR
    while result is TOOLOW and ttl < 128:
        ttl = ttl * 2
        result, rtt, _ = getRTT(address, ttl, port, timeout, logging)
        if result is ERROR:
            return ERROR, ERROR
    last_ttl = ttl / 2
    while True:
        difference = (last_ttl - ttl) // 2
        if difference == 0:
            break
        if result is TOOLOW:
            temp = ttl
            ttl = ttl - difference
            last_ttl = temp
        else:
            temp = ttl
            ttl = ttl + difference
            last_ttl = temp
        result, rtt, _ = getRTT(address, ttl, port, timeout, logging)
        if result is ERROR:
            return ERROR, ERROR
    _, rtt, ttl = getRTT(address, ttl, port, timeout, logging)
    return rtt, ttl


def getRTT(address, ttl=TTL, port=PORT, timeout=TIMEOUT, logging=LOGGING):
    '''
    Attempts to get an RTT to the given address with the given TTL.
    '''

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

    # Send the packet and start counting
    result = ERROR
    start_time = times()[4]
    recv.bind(('', port))
    log('{0}: Sending to {1}:{2} with TTL of {3}...'.format(start_time, dest, port, ttl), logging)
    send.sendto('', (dest, port))
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
            log('Got response from {0}'.format(addr[0]), logging)
            result = TOOLOW
    except socket.error:
        log('Error: connecting to socket failed.', logging)

    finally:
        send.close()
        recv.close()

    # Stop counting and get the result and RTT
    end_time = times()[4]
    log('{0}: Finished ping attempt.'.format(end_time), logging)
    return result, (end_time - start_time) * MILLISECONDS, ttl


def log(message, logging=True):
    if logging:
        print message

from sys import argv
if __name__ == '__main__':
    logging = False
    port = PORT
    timeout = TIMEOUT
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
    main(argv[i:], port, timeout, logging)
