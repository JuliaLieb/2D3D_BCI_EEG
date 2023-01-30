# This file is part of PyTIAClient.
# This project is licensed under the GNU GPL (version 3 or higher).
# Copyright 2014 by Clemens Brunner.


"""Utility functions.

"""


import math


def recv_until(sock, suffix="\n".encode("ascii")):
    """Reads from a socket until the specified character suffix is in the stream.

    Parameters
    ----------
    suffix : str, optional

    Returns
    -------
    str
        Received string.

    """
    msg = b""
    while not msg.endswith(suffix):
        data = sock.recv(1)  # Read a fixed number of bytes
        if not data:
            raise EOFError("Socket closed before receiving the delimiter.")
        msg += data
    return msg


def bitcount(number):
    """Determines the positions of high bits in a number.

    Parameters
    ----------
    number : int
        Integer number.

    Returns
    -------
    list of int
        Contains the positions of high bits (1s) in the binary representation of the input number.

    Examples
    --------
    >>> bitcount(15)
    [0, 1, 2, 3]
    >>> bitcount(16)
    [4]

    """
    high_bits = []
    if number > 0:
        for mask in range(int(math.ceil(math.log(number, 2))) + 1):
            if number & int(math.pow(2, mask)):
                high_bits.append(mask)
    return high_bits
