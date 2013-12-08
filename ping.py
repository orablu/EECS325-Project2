import socket
from os import times

# Result codes for the getRTT method
ERROR = -1
UNKNOWN = 0
TOOLOW = 1
OK = 2

# Constants
RESULT = 'RTT, {0}, TTL, {1}'
RESULT_ERROR = RESULT.format('', '')
STARTING_TTL = 16
PORT = 35623
BUFSIZE = 512
TIME_EXCEEDED = ''


def main(addresses):
    print __file__
    for address in addresses:
        if address == __file__:
            continue
        print 'Pinging {}'.format(address)
        rtt, ttl = ping(address)
        if rtt is not ERROR:
            print RESULT.format(rtt, ttl)
        else:
            print ERROR


def ping(address):
    '''
    Pings a address and returns the rtt and ttl.
    '''
    ttl = STARTING_TTL
    result, rtt = getRTT(ttl, address)
    while result is TOOLOW:
        ttl = ttl * 2
        result, rtt = getRTT(ttl, address)
        if result is ERROR:
            return None, None
    last_ttl = ttl / 2
    while True:
        difference = (last_ttl - ttl) // 2
        if difference == 0:
            break
        if result is TOOLOW:
            temp = ttl
            ttl = ttl + difference
            last_ttl = temp
        else:
            temp = ttl
            ttl = ttl - difference
            last_ttl = temp
        result, rtt = getRTT(ttl, address)
        if result is ERROR:
            return ERROR, ERROR
    return getRTT(ttl, address)


def getRTT(ttl, address):
    '''
    Attempts to get an RTT to the given address with the given TTL.
    '''
    result = ERROR
    dest = socket.gethostbyname(address)
    recv = socket.socket(socket.AF_INET,
                         socket.SOCK_RAW,
                         socket.getprotobyname('icmp'))
    send = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM,
                         socket.getprotobyname('udp'))
    send.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)

    # Send the packet and start counting
    start_time = times()[0]
    send.bind((socket.gethostname(), PORT))
    send.sendto('', (dest, PORT))
    try:
        data, addr = recv.recvfrom(BUFSIZE)
        print data
        result = OK
    except socket.error:
        data = None
    finally:
        send.close()
        recv.close()
    end_time = times()[0]
    if not data:
        result = ERROR
    elif data == TIME_EXCEEDED:
        result = TOOLOW
    return result, end_time - start_time


from sys import argv
if __name__ == '__main__':
    main(argv)
