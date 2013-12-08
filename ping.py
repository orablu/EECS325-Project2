import socket
import select
from os import times

# Result codes for the getRTT method
ERROR = -1
UNKNOWN = 0
TOOLOW = 1
OK = 2

# Constants
RESULT = 'RTT,{0},TTL,{1}'
RESULT_ERROR = RESULT.format('', '')
STARTING_TTL = 16
PORT = 33434
BUFSIZE = 512
TIME_EXCEEDED = ''


def main(addresses, logging=False):
    for address in addresses:
        log('Pinging {}'.format(address), logging)
        rtt, ttl = ping(address, PORT, logging)
        if rtt is not ERROR:
            print RESULT.format(rtt, ttl)
        else:
            print RESULT_ERROR


def ping(address, port, logging=False):
    '''
    Pings an address and returns the rtt and ttl.
    '''
    ttl = STARTING_TTL
    result, rtt, _ = getRTT(ttl, address, port, logging)
    while result is TOOLOW:
        ttl = ttl * 2
        result, rtt, _ = getRTT(ttl, address, port, logging)
        if result is ERROR:
            return None, None
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
        result, rtt, _ = getRTT(ttl, address, port, logging)
        if result is ERROR:
            return ERROR, ERROR
    _, rtt, ttl = getRTT(ttl, address, port, logging)
    return rtt, ttl


def getRTT(ttl, address, port, logging=False):
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
    #send.sendto(bytes('', 'utf-8'), (dest, port))
    send.sendto('', (dest, port))
    try:
        log('Waiting for response...', logging)
        recv.setblocking(0)
        ready = select.select([recv], [], [], 10)
        if ready[0]:
            _, addr = recv.recvfrom(BUFSIZE)
        if not addr:
            log('Error: attempt timed out', logging)
            return ERROR, 0, 0
        try:
            response = socket.gethostbyaddr(addr[0])[0]
            if response == address or addr[0] == dest:
                log('Got response from destination, TTL high enough', logging)
                result = OK
            else:
                log('Got response from {0}'.format(response), logging)
                result = TOOLOW
        except:
            log('Could not resolve {0}'.format(addr), logging)
            result = TOOLOW
    except socket.error:
        log('Error: connecting to socket failed.', logging)

    finally:
        send.close()
        recv.close()

    # Stop counting and get the result and RTT
    end_time = times()[4]
    log('{0}: Finished ping attempt.'.format(end_time), logging)
    return result, end_time - start_time, ttl


def log(message, logging=True):
    if logging:
        print message

from sys import argv
if __name__ == '__main__':
    if argv[1] == '--log' or argv[1] == '-l':
        main(argv[2:], True)
    else:
        main(argv[1:])
