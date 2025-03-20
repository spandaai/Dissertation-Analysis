import uuid
from datetime import datetime
import zlib
import base64

def create_authn_request():
    issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    request_id = f"_{uuid.uuid4().hex}"

    authn_request = f'''
        <samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            AssertionConsumerServiceURL="http://172.16.92.136/dissertation/Shibboleth.sso/SAML2/POST"
            Destination="https://idp.bits-pilani.ac.in/idp/profile/SAML2/Redirect/SSO"
            ID="{request_id}"
            IssueInstant="{issue_instant}"
            ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST"
            Version="2.0">
            <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
                https://www.spanda.ai/shibboleth/da
            </saml:Issuer>
            <samlp:NameIDPolicy AllowCreate="1"/>
        </samlp:AuthnRequest>
    '''
    return authn_request.strip()

def compress_and_encode_request(authn_request):
    compressor = zlib.compressobj(wbits=-15)
    deflated_request = compressor.compress(authn_request.encode('utf-8')) + compressor.flush()
    encoded_request = base64.b64encode(deflated_request).decode('utf-8')
    return encoded_request

def create_logout_request():
    issue_instant = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    request_id = f"_{uuid.uuid4().hex}"

    logout_request = f'''
    <samlp:LogoutRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
        Destination="https://idp.bits-pilani.ac.in/idp/profile/SAML2/Redirect/SLO"
        ID="{request_id}"
        IssueInstant="{issue_instant}"
        Version="2.0">
        <saml:Issuer xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            https://www.spanda.ai/shibboleth
        </saml:Issuer>
        <saml:NameID xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" 
            Format="urn:oasis:names:tc:SAML:1.1:nameid-format:unspecified">
            dummyuser@wilp.bits-pilani.ac.in
        </saml:NameID>
        <samlp:SessionIndex>
            _1f4a3c642d193cd485413184a3b990a8
        </samlp:SessionIndex>
    </samlp:LogoutRequest>
    '''
    return logout_request.strip()

def compress_and_encode_logout_request(logout_request):
    compressor = zlib.compressobj(wbits=-15)
    deflated_request = compressor.compress(logout_request.encode('utf-8')) + compressor.flush()
    encoded_request = base64.b64encode(deflated_request).decode('utf-8')
    return encoded_request
