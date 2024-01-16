#!/usr/bin/python3
"""
Script that creates Personal Access Token for Gitlab API;
Tested with:
- Gitlab Community Edition 16.6.0
"""
import sys, os
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

# Remove warnings when running against a self signed cert deployment
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

endpoint = os.environ.get("GITLAB_SERVER", "https://localhost:8080")
login = os.environ.get("GITLAB_USERNAME", "root")
password = os.environ.get("GITLAB_PASSWORD", "password")
api_scope = os.environ.get("GITLAB_TOKEN_SCOPE", "api")

host_name = urlparse(endpoint).hostname
root_route = urljoin(endpoint, "/")
sign_in_route = urljoin(endpoint, "/users/sign_in")
pat_route = urljoin(endpoint, "/-/profile/personal_access_tokens")

headers = {
    "Host": host_name,
    "Content-Type": "application/x-www-form-urlencoded"
}


def find_csrf_token(text):
    soup = BeautifulSoup(text, "lxml")
    token = soup.find(attrs={"name": "csrf-token"})
    param = soup.find(attrs={"name": "csrf-param"})

    data = {param.get("content"): token.get("content")}
    return data


def obtain_csrf_token():
    r = requests.get(root_route, verify=False)
    token = find_csrf_token(r.text)
    return token, r.cookies


def sign_in(csrf, cookies):
    data = {
        "user[login]": login,
        "user[password]": password,
        "user[remember_me]": 0
    }
    data.update(csrf)

    r = requests.post(sign_in_route, headers=headers, cookies=cookies, data=data, verify=False)

    token = find_csrf_token(r.text)
    return token, r.history[0].cookies


def obtain_personal_access_token(name, expires_at, csrf, cookies):    
    query_params = {
        "personal_access_token[name]": name,
        "personal_access_token[expires_at]": expires_at,
        "personal_access_token[scopes][]": api_scope
    }

    headers = {
        "Host": host_name,
        "Cookie": f"_gitlab_session={cookies['_gitlab_session']}",
        "Referer": pat_route,
        "X-CSRF-Token": csrf
    }

    r = requests.post(pat_route, headers=headers, params=query_params, verify=False)
    token = json.loads(r.text)["new_token"]

    return token


def main():
    csrf1, cookies1 = obtain_csrf_token()
    csrf2, cookies2 = sign_in(csrf1, cookies1)

    name = sys.argv[1]
    expires_at = sys.argv[2]

    token = obtain_personal_access_token(name, expires_at, csrf2['authenticity_token'], cookies2)
    print(token)


if __name__ == "__main__":
    main()
