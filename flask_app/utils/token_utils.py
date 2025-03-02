import base64
import requests
import time

TOKEN_INFO = {
    "access_token": None,
    "expires_at": 0
}

def fetch_new_token():
    """
    Fetch a new bearer token from the authentication server using Basic Auth.
    Replace this with your actual token endpoint and credentials.
    """
    token_url = "https://osp.prod.favv-afsca.be:8543/osp/a/idm/auth/oauth2/token"
    client_id = "rbpmrest"
    client_secret = "eyqscmnc"

    # Encode the client_id and client_secret in Base64 for Basic Auth
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    # Set up the headers with Basic Auth
    headers = {
        "Authorization": f"Basic {encoded_credentials}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Set up the payload for the token request
    payload = {
        "grant_type": "password",
        "username": "uaadmin",
        "password": "eyqscmnc"
    }

    # Make the POST request to fetch the token
    response = requests.post(token_url, headers=headers, data=payload, verify=False)

    if response.status_code == 200:
        token_data = response.json()
        TOKEN_INFO["access_token"] = token_data["access_token"]
        TOKEN_INFO["expires_at"] = time.time() + token_data["expires_in"]  # Current time + expiration duration
    else:
        raise Exception(f"Failed to fetch new token: {response.status_code}, {response.text}")