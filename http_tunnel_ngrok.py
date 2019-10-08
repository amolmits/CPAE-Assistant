#  -*- coding: utf-8 -*-
"""
Sample script to return current date/time in required formats.
Copyright (c) 2016-2019 Cisco and/or its affiliates.

Start ngrok using command "./ngrok start --none" and then run this script.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging
from current_datetime import curr_dtf, curr_dtl

import requests
import json
from webexteamssdk import WebexTeamsAPI, ApiError

# Constants
NGROK_CLIENT_API_BASE_URL = "http://127.0.0.1:4040/api/"
HEADERS = {'content-type': 'application/json', 'accept': 'application/json'}

def list_ngrok_public_url():
    """Get the ngrok public HTTP URL from the local client API."""
    try:
        ngrok_list = requests.get(url=NGROK_CLIENT_API_BASE_URL + "tunnels/", headers=HEADERS)
    except requests.exceptions.RequestException:
        print("Could not connect to the ngrok client API; assuming not running.")
        return None
    else:
        logging.info("Successfully retrieved all existing HTTP Tunnels.")
        return(ngrok_list.json())

def del_ngrok_public_url():
    """Get the ngrok public HTTP URL from the local client API and delete it."""
    ngrok_list = list_ngrok_public_url()
#    print(ngrok_list)
    while ngrok_list["tunnels"] != []:
#        print(ngrok_list["tunnels"])
        for i in range(len(ngrok_list["tunnels"])):
            tunnel_name = ngrok_list["tunnels"][i]['name']
            try:
                delete_tunnel = requests.delete(url=NGROK_CLIENT_API_BASE_URL + "tunnels/" + tunnel_name, headers=HEADERS)
            except requests.exceptions.RequestException as e:
                logging.error("Could not delete existing tunnel.\n  {}".format(e))
        logging.info("Successfully deleted all existing HTTP Tunnels.")
        break
    logging.info("No HTTP Tunnels exist!")
    return("True")

def create_ngrok_public_url(tunnel_name, protocol, port):
    """Create a new ngrok public HTTP Tunnel and catch thee URL."""
    payload = "{\"addr\": \"" + port + "\", \"proto\": \"" + protocol + "\", \"name\": \"" + tunnel_name + "\"}"
#    print(payload)
    try:
        ngrok_post = requests.post(url=NGROK_CLIENT_API_BASE_URL + "tunnels/", data=payload, headers=HEADERS)
#        print(ngrok_post)
#        print(ngrok_post.json())
    except requests.exceptions.RequestException:
        print("Could not connect to the ngrok client API; assuming not running.")
        return None
    else:
        ngrok_list = list_ngrok_public_url()
        for tunnel in ngrok_list["tunnels"]:
            if tunnel.get("public_url", "").startswith("http://"):
#                logging.info("Found ngrok public HTTP URL:", str(tunnel["public_url"]))
                return tunnel["public_url"]

def delete_existing_webhooks(api):
    """List all webhooks and delete them."""
    try:
        for webhook in api.webhooks.list():
            logging.info("Deleting Webhook:" + webhook.name + " TargetURL=" + webhook.targetUrl)
            api.webhooks.delete(webhook.id)
        logging.info("All WebHooks deleted!")
    except ApiError as e:
        logging.error(e)

def create_webhook_messages_created(api, webhook_name, ngrok_public_url, filter_messsages=None):
    """Create a Webex Teams webhook pointing to the public ngrok URL."""
    logging.info("Creating Webhook...")
    webhook = api.webhooks.create(name=webhook_name, targetUrl=ngrok_public_url, resource="messages", event="created", filter=filter_messsages)
#    print(webhook)
    logging.info("Webhook for messages created successfully.")
    return webhook

def create_webhook_memberships_created(api, webhook_name, ngrok_public_url, filter_memberships=None):
    """Create a Webex Teams webhook pointing to the public ngrok URL."""
    logging.info("Creating Webhook...")
    webhook = api.webhooks.create(name=webhook_name, targetUrl=ngrok_public_url, resource="memberships", event="created", filter=filter_memberships)
#    print(webhook)
    logging.info("Webhook for memberships created successfully.")
    return webhook

def main():
    api = WebexTeamsAPI()
    logging.basicConfig(level=logging.DEBUG, filename='http_tunnel_ngrok_'+curr_dtf()+'.log', filemode='w', format=curr_dtl()+' %(name)s - %(levelname)s - %(message)s')
    del_ngrok_public_url()
    public_url = create_ngrok_public_url('amol', 'http', '8080')
    delete_existing_webhooks(api)
    webhook_name_mes = api.people.me().displayName + " Messages WebHook"
    webhook_name_mem = api.people.me().displayName + " Memberships WebHook"
    if public_url is not None:
        filter_memberships = "personEmail=" + api.people.me().emails[0]
        create_webhook_messages_created(api, webhook_name_mes, public_url)
        create_webhook_memberships_created(api, webhook_name_mem, public_url, filter_memberships)
        logging.info("Webhooks Created!")

if __name__ == '__main__':
    main()
