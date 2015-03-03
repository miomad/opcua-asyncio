import logging
import uuid

from opcua import uaprotocol as ua
from opcua import BinaryClient, Node
from urllib.parse import urlparse


class Client(object):
    def __init__(self, url):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.server_url = urlparse(url)
        self.name = "Pure Python Client" 
        self.description = self.name 
        self.application_uri = "urn:freeopcua:client"
        self.product_uri = "urn:freeopcua.github.no:client"
        self.security_policy_uri = "http://opcfoundation.org/UA/SecurityPolicy#None"
        self.secure_channel_id = None
        self.default_timeout = 3600000
        self.bclient = BinaryClient()
        self._nonce = None
        self._session_counter = 1

    def connect(self):
        self.connect_socket()
        self.send_hello()
        self.open_secure_channel()
        endpoints = self.get_endpoints()
        #FIXME check endpoint, config, etc
        self.close_secure_channel()
        #here we expect server to close connection automatically
        self.connect_socket()
        self.create_session()
        self.activate_session()

    def connect_socket(self):
        self.bclient.connect(self.server_url.hostname, self.server_url.port)

    def disconnect_socket(self):
        self.bclient.disconnect()

    def disconnect(self):
        self.close_secure_channel()
        self.bclient.disconnect()

    def send_hello(self):
        ack = self.bclient.send_hello(self.server_url.geturl())

    def open_secure_channel(self):
        params = ua.OpenSecureChannelParameters()
        params.ClientProtocolVersion = 0
        params.RequestType = ua.SecurityTokenRequestType.Issue
        params.SecurityMode = ua.MessageSecurityMode.None_
        params.RequestedLifetime = 300000
        params.ClientNonce = '\x00'
        self.bclient.open_secure_channel(params)

    def close_secure_channel(self):
        return self.bclient.close_secure_channel()

    def get_endpoints(self):
        params = ua.GetEndpointsParameters()
        params.EndpointUrl = self.server_url.geturl()
        params.ProfileUris = ["http://opcfoundation.org/UA-Profile/Transport/uatcp-uasc-uabinary"]
        params.LocaleIds = ["http://opcfoundation.org/UA-Profile/Transport/uatcp-uasc-uabinary"]
        return self.bclient.get_endpoints(params)

    def create_session(self):
        desc = ua.ApplicationDescription()
        desc.ApplicationUri = self.application_uri
        desc.ProductUri = self.product_uri
        desc.ApplicationName = ua.LocalizedText(self.name)
        desc.ApplicationType = ua.ApplicationType.Client

        params = ua.CreateSessionParameters()
        params.ClientNonce = uuid.uuid4().bytes
        params.ClientCertificate = b''
        params.ClientDescription = desc 
        params.EndpointUrl = self.server_url.geturl()
        params.SessionName = self.description + " Session" + str(self._session_counter)
        params.RequestedSessionTimeout = 3600000
        params.MaxResponseMessageSize = 0 #means not max size
        response = self.bclient.create_session(params)
        return response

    def activate_session(self):
        params = ua.ActivateSessionParameters()
        params.LocaleIds.append("en")
        params.UserIdentityToken = ua.AnonymousIdentityToken()
        params.UserIdentityToken.PolicyId = b"anonymous"
        return self.bclient.activate_session(params)

    def close_session(self):
        return self.bclient.close_session(True)

    def get_root_node(self):
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.RootFolder))

    def get_objects_node(self):
        return self.get_node(ua.TwoByteNodeId(ua.ObjectIds.ObjectsFolder))

    def get_node(self, nodeid):
        return Node(self.bclient, nodeid)




