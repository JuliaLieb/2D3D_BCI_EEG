# This file is part of PyTIAClient.
# This project is licensed under the GNU GPL (version 3 or higher).
# Copyright 2014 by Clemens Brunner.


"""TIA client for Python.

"""


import socket
import threading
import struct
import xml.etree.ElementTree as ElementTree

from .utils import recv_until, bitcount

# TODO: Include logger
# TODO: Include unit tests?


__version__ = "1.0.0"


SOCKET_TIMEOUT = 2  # Socket timeout (in seconds)
TIA_VERSION = 1.0
FIXED_HEADER_SIZE = 33  # Fixed header size (in bytes)
BUFFER_SIZE = 2  # TODO: Implement buffer size limit
SIGNAL_TYPES = {"eeg": 0, "emg": 1, "eog": 2, "ecg": 3, "hr": 4, "bp": 5, "button": 6,
                "axes": 7, "sensor": 8, "nirs": 9, "fmri": 10, "keycode": 11,
                "user1": 16, "user2": 17, "user3": 18, "user4": 19,
                "undefined": 20, "event": 21}


class TIAClient(object):
    """Client for the TIA network protocol.

    Provides methods to connect to a TIA server, receive meta information about the streams, and stream data over the
    network.

    """

    def __init__(self):
        self._sock_ctrl = None  # Socket for control connection
        self._sock_data = None  # Socket for data connection
        self._metainfo = {"subject": None, "masterSignal": None, "signals": []}
        self._thread_running = False  # Indicates if data thread is running
        self._data_thread = None
        self._buffer = None
        self._buffer_lock = None
        self._buffer_avail = None
        self._buffer_type = []
        self._buffer_empty = True

    def connect(self, host, port):
        """Connects to TIA server and establishes control connection.

        Parameters
        ----------
        host : str
            Host name or IP address.
        port : int
            Port number.

        Raises
        ------
        TIAError
            If a connection cannot be established.

        """
        if self._sock_ctrl is not None:
            raise TIAError("Control connection already established.")
        try:
            self._sock_ctrl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock_ctrl.settimeout(SOCKET_TIMEOUT)
            self._sock_ctrl.connect((host, port))
        except socket.error:
            self._sock_ctrl = None
            raise TIAError("Cannot establish control connection (server might be down).")
        if not self._check_protocol():  # Check if protocol is supported by server
            raise TIAError("Protocol version {} not supported by server.".format(TIA_VERSION))
        self._get_metainfo()

    def close(self):
        """Closes control connection to server.

        Raises
        ------
        TIAError
            If the connection cannot be closed.

        """
        if self._sock_data is not None:  # Stop data transmission (if running)
            self.stop_data()
        if self._sock_ctrl is not None:
            self._sock_ctrl.close()
            self._sock_ctrl = None
        else:
            raise TIAError("Control connection already closed.")

    def start_data(self, connection="TCP"):
        """Starts data transmission.

        Parameters
        ----------
        connection : {"TCP", "UDP"}
            Connection type used to stream data. Currently, only TCP connections are supported.

        Raises
        ------
        TIAError
            If the connection cannot be established.

        """
        if self._sock_ctrl is None:
            raise TIAError("Control connection to server not established.")
        if self._sock_data is not None:
            raise TIAError("Data connection already established.")
        if connection != "TCP":
            raise NotImplementedError("UDP connection has not been implemented yet.")
        try:
            port = self._get_data_connection("TCP")
            self._sock_data = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock_data.settimeout(SOCKET_TIMEOUT)
            self._sock_data.connect((self._sock_ctrl.getpeername()[0], port))  # Connect to same host, but new port
        except socket.error:
            self._sock_data = None
            raise TIAError("Cannot establish data connection.")
        try:
            self._sock_ctrl.sendall("TiA {}\nStartDataTransmission\n\n".format(TIA_VERSION).encode("ascii"))
            tia_version = recv_until(self._sock_ctrl).strip()
            status = recv_until(self._sock_ctrl).strip()
            self._sock_ctrl.recv(1)
        except (socket.error, EOFError):
            raise TIAError("Starting data transmission failed.")
        if status != b"OK":
            raise TIAError("Starting data transmission failed.")
        self._clear_buffer()
        self._thread_running = True
        self._data_thread = threading.Thread(target=self._get_data)
        self._buffer_lock = threading.RLock()
        self._buffer_avail = threading.Condition(self._buffer_lock)
        self._data_thread.start()

    def stop_data(self):
        """Stops data transmission.

        """
        if self._thread_running:
            self._thread_running = False  # The data socket is closed in _get_data() when the thread terminates
            self._data_thread.join()

    def get_data_chunk(self, blocking=False, timestamps=False):
        """Returns the data buffer and clears it.

        Parameters
        ----------
        blocking : bool
            If set to True, blocks/waits until data is available.
        timestamps : bool
            If set to True, the function returns a tuple consisting of data and
            timestamps; otherwise, it returns only the data (see below).

        Returns
        -------
        If timestamps is set to False (default):
        buffer
            Buffer containing all data received since the last call.

        If timestamps is set to True:
        (buffer, timestamps)
            Tuple containing data and timestamps.

        Raises
        ------
        TIAError
            If the data transmission has not been started.

        """
        if not self._thread_running:
            raise TIAError("Data transmission has not been started.")

        with self._buffer_lock:
            while self._buffer_empty and blocking:
                self._buffer_avail.wait()
            data = self._buffer
            time = self._timestamps
            self._clear_buffer()
            if timestamps:
                return data, time
            else:
                return data

    def get_state_connection(self):
        """Creates a state connection.

        """
        pass
        # TODO: This method should probably be private, run in a separate thread and just receive state messages.

    def _check_protocol(self):
        """Checks if server supports the protocol version implemented by this client.

        Returns
        -------
        bool
            If the server supports the protocol version implemented by this client, this method returns True.

        Raises
        ------
        TIAError
            If the connection cannot be established.

        """
        try:
            self._sock_ctrl.sendall("TiA {}\nCheckProtocolVersion\n\n".format(TIA_VERSION).encode("ascii"))
            tia_version = recv_until(self._sock_ctrl).strip()
            status = recv_until(self._sock_ctrl).strip()
            self._sock_ctrl.recv(1)
        except (socket.error, EOFError):
            raise TIAError("Checking protocol version failed (server might be down).")
        return status == b"OK"

    def _get_metainfo(self):
        """Retrieves meta information from the server.

        Raises
        ------
        TIAError
            If the connection cannot be established or the meta information cannot be parsed.

        """
        try:
            self._sock_ctrl.sendall("TiA {}\nGetMetaInfo\n\n".format(TIA_VERSION).encode("ascii"))
            tia_version = recv_until(self._sock_ctrl).strip()
            msg = recv_until(self._sock_ctrl).strip()
            msg = recv_until(
                self._sock_ctrl).strip()  # Contains "Content-Length:xxx", where "xxx" is the number of bytes
            content_len = int(msg.split(b":")[-1])
            xml_string = self._sock_ctrl.recv(
                content_len + 1).strip()  # There is one extra "\n" at the end of the message
        except (socket.error, EOFError):
            raise TIAError("Receiving meta information failed (server might be down).")
        try:
            xml = ElementTree.fromstring(xml_string)
        except ElementTree.ParseError:
            raise TIAError("Error while parsing XML meta information (syntax error).")
        if xml.find("subject") is not None:
            self._metainfo["subject"] = dict(xml.find("subject").attrib)
        if xml.find("masterSignal") is not None:
            self._metainfo["masterSignal"] = dict(xml.find("masterSignal").attrib)
        for index, signal in enumerate(xml.findall("signal")):
            self._metainfo["signals"].append(dict(signal.attrib))
            self._metainfo["signals"][index]["channels"] = []  # List of channels
            for channel in signal.findall("channel"):
                self._metainfo["signals"][index]["channels"].append(
                    channel.attrib)  # TODO: Check if conversion to dict() would make sense

        self._buffer_type = []
        for index, signal in enumerate(self._metainfo["signals"]):
            try:
                self._buffer_type.append(
                    SIGNAL_TYPES[signal["type"]])  # Assign corresponding signal type to each signal group
            except KeyError:
                raise TIAError("Unknown signal type found.")

    def _get_data_connection(self, connection):
        """Determines the port number of the new data connection.

        Parameters
        ----------
        connection : {"TCP", "UDP"}
            Connection type used to stream data.

        Returns
        -------
        int
            Port number of the new data connection.

        Raises
        ------
        TIAError
            If the connection cannot be established.

        """
        if connection != "TCP" and connection != "UDP":
            raise TIAError("Data connection must be either TCP or UDP.")
        try:
            self._sock_ctrl.sendall(
                ("TiA {}\nGetDataConnection: ".format(TIA_VERSION) + connection + "\n\n").encode("ascii"))
            tia_version = recv_until(self._sock_ctrl).strip()
            port = recv_until(self._sock_ctrl).strip()
            self._sock_ctrl.recv(1)
        except (socket.error, EOFError):
            raise TIAError("Could not get port of new data connection.")
        if port.find(b"Error -- Target and remote subnet do not match!") != -1:
            raise TIAError("Target and remote subnets do not match for a UDP data connection.")
        else:
            return int(port.split(b":")[-1])

    def _get_data(self):
        """Receive data from server and store it in buffer.

        Raises
        ------
        TIAError
            If the data connection cannot be closed properly.

        """
        while self._thread_running:
            d_version, d_size, d_flags, d_id, d_number, d_timestamp = struct.unpack("<BIIQQQ", self._sock_data.recv(
                FIXED_HEADER_SIZE))  # Get fixed header
            signal_types = bitcount(d_flags)  # Lists the signal types present in the data packet
            signal_list = [self._buffer_type.index(k) for k in signal_types]  # Indices into the buffer

            n_signals = len(signal_list)
            var_header_size = 4 * n_signals

            # FIXME: I don't know if these values are needed at all; I could just skip over the variable header
            # FIXME: After all, these values are available in the meta information!
            n_channels = []
            block_size = []
            for signals in range(n_signals):
                tmp = struct.unpack("<H", self._sock_data.recv(2))
                n_channels.append(tmp[0])
            for signals in range(n_signals):
                tmp = struct.unpack("<H", self._sock_data.recv(2))
                block_size.append(tmp[0])

            with self._buffer_lock:
                self._timestamps.append(d_timestamp)
                for index, signal in enumerate(signal_list):  # Read signal blocks; signal is the index into the buffer
                    for channel in range(n_channels[index]):
                        for sample in range(block_size[index]):
                            data = struct.unpack("<f", self._sock_data.recv(4))[0]
                            self._buffer[signal][channel].append(data)
                self._buffer_empty = False
                self._buffer_avail.notify_all()

                # TODO: Check for size of self._buffer and delete oldest sample if buffer is too big

        # Stop data transmission        
        try:
            self._sock_ctrl.sendall("TiA {}\nStopDataTransmission\n\n".format(TIA_VERSION).encode("ascii"))
            tia_version = recv_until(self._sock_ctrl).strip()
            status = recv_until(self._sock_ctrl).strip()
            self._sock_ctrl.recv(1)
        except (socket.error, EOFError):
            raise TIAError("Stopping data transmission failed.")
        self._sock_data.close()
        self._sock_data = None

    def _clear_buffer(self):
        """Initializes an empty buffer.

        Requires meta information to be read first.

        """
        # Each signal group is a list entry, so the first signal group is in self._buffer[0]
        # Each signal group is also a list of channels, and each channel is a list of samples
        self._buffer_empty = True
        self._timestamps = []
        self._buffer = [[] for _ in range(len(self._metainfo["signals"]))]  # Empty list for each signal group
        for index, signal in enumerate(self._metainfo["signals"]):
            self._buffer[index] = [[] for _ in range(int(signal["numChannels"]))]  # Empty list for each channel


class TIAError(Exception):
    """Exception for all TIA-related errors.

    """
    pass
