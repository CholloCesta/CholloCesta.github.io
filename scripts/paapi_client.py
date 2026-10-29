import requests
import json
import hmac
import hashlib
from datetime import datetime

class PaapiClient:
    def __init__(self, access_key, secret_key, partner_tag, region="ES"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        self.host = f"webservices.amazon.{'es' if region == 'ES' else 'com'}"
        self.endpoint = f"https://{self.host}/paapi5"

    def _get_signature_key(self, key, date_stamp, region, service):
        k_date = hmac.new(('AWS4' + key).encode('utf-8'), date_stamp.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
        return k_signing

    def _make_request(self, target, payload):
        t = datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')
        
        # SigV4 canonicalization
        content_type = 'application/json; charset=utf-8'
        canonical_uri = f"/paapi5/{target}"
        canonical_querystring = ''
        
        payload_json = json.dumps(payload)
        payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
        
        canonical_headers = f"content-encoding:amz-1.0\ncontent-type:{content_type}\nhost:{self.host}\nx-amz-date:{amz_date}\nx-amz-target:com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{target}\n"
        signed_headers = 'content-encoding;content-type;host;x-amz-date;x-amz-target'
        canonical_request = f"POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        
        # String to sign
        credential_scope = f"{date_stamp}/{self.region}/ProductAdvertisingAPI/aws4_request"
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        
        # Signing
        signing_key = self._get_signature_key(self.secret_key, date_stamp, self.region, "ProductAdvertisingAPI")
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # Authorization Header
        authorization_header = f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        
        headers = {
            'Content-Type': content_type,
            'Content-Encoding': 'amz-1.0',
            'X-Amz-Date': amz_date,
            'X-Amz-Target': f"com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{target}",
            'Authorization': authorization_header,
            'Host': self.host
        }
        
        response = requests.post(f"{self.endpoint}/{target}", data=payload_json, headers=headers)
        return response.json()

    def search_items(self, keywords, resources=["ItemInfo.Title", "Offers.Listings.Price"]):
        payload = {
            "Keywords": keywords,
            "SearchIndex": "All",
            "PartnerTag": self.partner_tag,
            "PartnerType": "Associates",
            "Resources": resources
        }
        return self._make_request("SearchItems", payload)

def get_paapi_client(access_key, secret_key, partner_tag):
    return PaapiClient(access_key, secret_key, partner_tag)
