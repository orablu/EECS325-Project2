from socket import socket as new_socket, SOCK_DGRAM
from struct import pack

# Result codes for the getRTT method
ERROR = -1
UNKNOWN = 0
TOOLOW = 1
TOOHIGH = 2
OK = 3

# Constants
RESULT = 'RTT, {0}\nTTL, {1}'
ERROR = RESULT.format(-1, -1)
STARTING_TTL = 16


def main(*args):
    for address in args:
        ping(address)


def ping(address):
    ttl = STARTING_TTL
    result, rtt = getRTT(ttl, address)
    while result is TOOLOW:
        ttl = ttl * 2
        result, rtt = getRTT(ttl, address)
        if result is ERROR:
            print(ERROR)
            return
    last_ttl = ttl / 2
    while result is not OK:
        temp = ttl
        ttl = ttl + (last_ttl - ttl) / 2
        last_ttl = temp
        result, rtt = getRTT(ttl, address)
        if result is ERROR:
            print(ERROR)
            return
    print(RESULT.format(rtt, ttl))


def getRTT(ttl, address):
    socket = new_socket(SOCK_DGRAM)
    socket.setsockopt(socket.IPPROTO_IP,
                      socket.IP_MULTICAST_TTL,
                      pack('b', ttl))
    message = [0x00, 0x00, 0x00, 0x00]  # TODO: Is this the ind of body to use?
    socket.sendto(message, address)
    #Start timer
    #while not timed out
        #Wait for response from socket
        #Is that response for the sent message?
            #Was the ttl too short?
                #return TOOLOW, 0
            #Was the ttl too long?
                #return TOOHIGH, 0
            #Stop timer, get rtt
            #return rtt
    return ERROR, 0


from sys import argv
if __name__ is 'main':
    main(argv)
