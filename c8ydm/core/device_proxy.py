"""
Device Proxy Module which tunnels a TCP Socket through WebSocket to a C8Y Tenant.
Raises:
    WebSocketFailureException: Is raised when something is wrong with the Web Socket Connection
    TCPSocketFailureException: Is raised when something is wrong with the TCP Connection
"""
import logging
import socket
import threading
from base64 import b64encode
from socket import SHUT_RDWR

import certifi
import websocket


class WebSocketFailureException(Exception):
    """WS Failure error"""


class TCPSocketFailureException(Exception):
    """TCP Socket Failure error"""


class DeviceProxy:
    """ Main Proxy Class for tunneling TCP with WebSocket

        Args:
            tcp_host (string): Local TCP Host to connect to
            tcp_port (int): Local TCP Port to connect to
            buffer_size (int, optional): The buffer size (byte) used to receive TCP data. Default 16384 if None
            connection_key (string): The connection Key provided by Cumulocity to establish a Web Socket connection
            base_url (string): The Base URL of the C8Y Instance the Web Socket should connect to
            tenantuser (string): The C8Y TenantId + user, e.g. 't123143/username' required when token is None
            password (string): The C8Y Device Password, required when token is None
            token (string): The OAuth Token used to authenticate when tenant + user + password are not provided
    """

    def __init__(self, tcp_host: str,
                 tcp_port: int,
                 buffer_size: int,
                 connection_key: str,
                 base_url: str,
                 tenantuser: str,
                 password: str,
                 token: str):
        self.logger = logging.getLogger(__name__)
        self.tcp_host = tcp_host
        self.tcp_port = tcp_port
        self.connection_key = connection_key
        self.base_url = base_url
        self.tenantuser = tenantuser
        self.password = password
        self.token = token
        self.buffer_size = 16384 if buffer_size is None else buffer_size
        self._close = False
        self._websocket_device_endpoint = '/service/remoteaccess/device/'
        self._web_socket = None
        self._tcp_socket = None
        self._ws_open = False
        self._ws_open_event = None
        self._tcp_open_event = None
        self._ws_timeout = 20
        self._tcp_timeout = 10

    def connect(self):
        """Establishes the connection to Web Socket and TCP Port in this order

        Raises:
            WebSocketFailureException: Is raised when something is wrong with the Web Socket Connection
            Exception: Any other exception happening during execution
        """
        # They are needed to wait for succesful connections
        self._ws_open_event = threading.Event()
        self._tcp_open_event = threading.Event()
        try:
            self._websocket_connect(self.connection_key)
        except Exception as ex:
            self.logger.error(f'Error on Web Socket Connect: {ex}')
            self.stop()
            raise
        ws_result = self._ws_open_event.wait(timeout=self._ws_timeout)
        # WebSocket Connection is not successful
        if ws_result is False:
            raise WebSocketFailureException(
                'No WebSocket Connection could be established in time.')
        # Establish TCP Socket Connection
        try:
            self._tcp_port_connect(self.tcp_host, self.tcp_port)
        except Exception as ex:
            self.logger.error(f'Error on TCP Socket Connect: {ex}')
            # This is a dummy command to let the Web Socket Thread trigger the stop command!
            # see _on_ws_close(...) If we would just do self.stop() the Web Socket Thread
            # and event Threads are not properly removed sometimes
            if self._web_socket.sock is not None and self._ws_open:
                self._web_socket.send('## Shutdown ##')
            else:
                self.stop()
            raise

    def stop(self):
        """ Disconnecting all Connections and clean up objects & Threads """
        self.logger.info('Stopping TCP Socket and WebSocket Connections...')
        # Stopping Loop
        self._close = True
        # Shutdown TCP Socket
        if self._tcp_socket is not None:
            self._tcp_socket.shutdown(SHUT_RDWR)
            self._tcp_socket.close()
        # Closing WebSocket
        if self._web_socket is not None:
            self._web_socket.keep_running = False
            self._web_socket.close()
        self._web_socket = None
        self._tcp_socket = None
        self._ws_open = False
        self.logger.info('TCP Socket and WebSocket Connections stopped!')

    def _start_tcp_loop(self):
        try:
            # This is the TCP Loop looking for Data and forwarding it to Web Socket
            while not self._close:
                #ws_message = self._ws_buffer_queue.get()
                data = self._tcp_socket.recv(self.buffer_size)
                # If no data received anymore consider this loop as completed!
                if not data:
                    raise TCPSocketFailureException(
                        'No data received anymore from TCP-Socket. Consider TCP-Socket as closed.')
                self.logger.debug(f'Received data from TCP Socket: {data}')
                if self._web_socket.sock is not None:
                    self._web_socket.sock.send_binary(data)
        except Exception as ex:
            if not self._close:
                self.logger.error(f'Error in TCP Loop. Exception={ex}')
                # This is a dummy command to let the Web Socket Thread trigger the stop command!
                # see _on_ws_close(...) If we would just do self.stop() the Web Socket Thread
                # and event Threads are not properly removed sometimes
                if self._web_socket.sock is not None and self._ws_open:
                    self._web_socket.send('## Shutdown ##')
                else:
                    self.stop()

    def _tcp_port_connect(self, host, port):
        self.logger.info(f'Connecting to TCP Host {host} with Port {port} ...')
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((host, port))
        self._tcp_socket = tcp_socket
        self.logger.info(
            f'Connected to TCP Host {host} with Port {port} successfully.')
        # Start TCP Loop receiving Data
        tcpt = threading.Thread(target=self._start_tcp_loop)
        tcpt.daemon = True
        tcpt.name = f'TCPTunnelThread-{self.connection_key[:8]}'
        tcpt.start()
        self._tcp_open_event.set()

    def _is_tcp_socket_available(self) -> bool:
        if self._tcp_socket is not None:
            return True
        tcp_result = self._tcp_open_event.wait(timeout=self._tcp_timeout)
        return tcp_result

    def _on_ws_message(self, _ws, message):
        try:
            self.logger.debug(f'WebSocket Message received: {message}')
            #self._ws_buffer_queue.put(message)
            if self._is_tcp_socket_available():
                self.logger.debug(f'Sending to TCP Socket: {message}')
                if self._tcp_socket is not None:
                    self._tcp_socket.send(message)
        except Exception as ex:
            self.logger.error(
                f'Error on handling WebSocket Message {message}: {ex}')
            self.stop()

    def _on_ws_error(self, _ws, error):
        self.logger.error(f'WebSocket Error received: {error}')

    def _on_ws_close(self, _ws):
        self.logger.info(f'WebSocket Connection closed!')
        self.stop()

    def _on_ws_open(self, _ws):
        self.logger.info(f'WebSocket Connection opened!')
        self._ws_open = True
        self._ws_open_event.set()

    def _websocket_connect(self, connection_key):
        """Connecting to the CRA WebSocket

        Args:
            connection_key (string): Delivered by the Operation

        Raises:
            WebSocketFailureException: Is raised when something is wrong with the Web Socket Connection
        """
        if connection_key is None:
            raise WebSocketFailureException('Connection Key is required to establish a WebSocket Connection!')
        if not self.base_url.startswith('http'):
            self.base_url = f'https://{self.base_url}'
        base_url = self.base_url.replace(
            'https', 'wss').replace('http', 'ws')
        headers = None
        if self.token:
            # Use Device Certificates
            headers = f'Authorization: Bearer {self.token}'
        elif self.tenantuser and self.password:
            # Use Device Credentials
            auth_string = f'{self.tenantuser}:{self.password}'
            encoded_auth_string = b64encode(
                bytes(auth_string, 'utf-8')).decode('ascii')
            headers = f'Authorization: Basic {encoded_auth_string}'
        else:
            raise WebSocketFailureException('OAuth Token or tenantuser and password must be provided!')

        url = f'{base_url}{self._websocket_device_endpoint}{connection_key}'
        self.logger.info(f'Connecting to WebSocket with URL {url} ...')

        # websocket.enableTrace(True) # Enable this for Debug Purpose only
        web_socket = websocket.WebSocketApp(url, header=[headers])
        # pylint: disable=unnecessary-lambda
        # See https://stackoverflow.com/questions/26980966/using-a-websocket-client-as-a-class-in-python
        web_socket.on_message = lambda ws, msg: self._on_ws_message(ws, msg)
        web_socket.on_error = lambda ws, error: self._on_ws_error(ws, error)
        web_socket.on_close = lambda ws: self._on_ws_close(ws)
        web_socket.on_open = lambda ws: self._on_ws_open(ws)
        self.logger.info(f'Starting Web Socket Connection...')
        self._web_socket = web_socket
        wst = threading.Thread(target=self._web_socket.run_forever, kwargs={
            'ping_interval': 10, 'ping_timeout': 7, 'sslopt': {'ca_certs': certifi.where()}})
        wst.daemon = True
        wst.name = f'WSTunnelThread-{self.connection_key[:8]}'
        wst.start()
