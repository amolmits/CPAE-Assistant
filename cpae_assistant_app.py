#  -*- coding: utf-8 -*-
"""
Sample script to return current date/time in required formats.
Copyright (c) 2016-2019 Cisco and/or its affiliates.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import sys
import logging
import datetime
from current_datetime import curr_dtf, curr_dtl

import requests
import json
from webexteamssdk import WebexTeamsAPI, ApiError
import csv
import random
import time

from http_tunnel_ngrok import del_ngrok_public_url
from http_tunnel_ngrok import create_ngrok_public_url
from http_tunnel_ngrok import delete_existing_webhooks
from http_tunnel_ngrok import create_webhook_messages_created
from http_tunnel_ngrok import create_webhook_memberships_created

from attendee_list_csv_reader import read_list
from attendee_list_csv_reader import read_csv
from attendee_list_csv_reader import compare_csv_2
from attendee_list_csv_reader import compare_csv_3
from attendee_list_csv_reader import compare_csv_4

try:
    from flask import Flask
    from flask import request
except ImportError as e:
    print(e)
    print("Looks like 'flask' library is missing.\n"
          "Type 'pip3 install flask' command to install the missing library.")
    sys.exit()

access_token=os.environ.get("WEBEX_TEAMS_ACCESS_TOKEN")
api = WebexTeamsAPI()


def send_message_room(room_id, message_html, message_text, textorhtml):
    if textorhtml == "html":
        send_message = api.messages.create(roomId=room_id, html=message_html, text=message_text)
    elif textorhtml == "text":
        send_message = api.messages.create(roomId=room_id, text=message_text)
    return "True"

def send_message_person(email, message_html, message_text, textorhtml):
    if textorhtml == "html":
        send_message = api.messages.create(toPersonEmail=email, html=message_html, text=message_text)
    elif textorhtml == "text":
        send_message = api.messages.create(toPersonEmail=email, text=message_text)
    return "True"

def text_or_html_format(raw_message_htm):
    if raw_message_htm != None:
        logging.info(raw_message_htm != "")
        format = "html"
    else:
        format = "text"
    return format

def handle_incoming_messages(webhook, result_message, msg_html, msg_text):
    raw_message_html = result_message.html
    raw_message_text = result_message.text
    in_message_roomid = result_message.roomId
    in_message_sender = result_message.personEmail.lower()
    logging.info("Original message sent (in TEXT format) = " + raw_message_text)
    message_format = text_or_html_format(raw_message_html)
    logging.info("Message format is " + message_format)
    moderator_emails = read_list('moderator_emails.txt')
    attendee_emails, attendee_num, attendee_fnames, attendee_fullnames = compare_csv_4('attendee_data.csv', 4, 1, 2, 6)
    demobooth_emails, demobooth_names = compare_csv_2('demobooth_emails.csv', 1, 2)
    for i in range(len(demobooth_emails)):
        if demobooth_emails[i].lower() == in_message_sender.lower():
            demo_name = demobooth_names[i]
            break

    if message_format == "html":
        if webhook['data']['roomType'] == "group":
            in_message_html = (raw_message_html.split('spark-mention')[0] + raw_message_html.split('spark-mention')[2]).replace("<> ", "")
        elif webhook['data']['roomType'] == "direct":
            in_message_html = raw_message_html

    if webhook['data']['roomType'] == "group":
        in_message_text = raw_message_text.replace(bot_nickname + " ", '')
        logging.info("Original Message was sent in a group space. Bot name removed from the message text.")
    elif webhook['data']['roomType'] == "direct":
        in_message_text = raw_message_text
        logging.info("Original Message was sent in a direct space. No actions needed on message text.")

    if in_message_text == "help":
        try:
            sender = api.people.list(email=in_message_sender)
        except ApiError as e:
            logging.error(e)
        for i in sender:
            sender_fname = i.firstName
        if in_message_sender in moderator_emails:
            out_message_mark = "Hello **{}**! I can help you with the following tasks.\n\n* **#sendpage 'message'** - Sends the 'message' to all CPAE attendees via 1:1 spaces in persoanlised format. Limited text formatting is supported.\n* **#sendtogroup 'message'** - Sends the 'message' to the CPAE group space with @All tagged. Limited text formatting is supported.\n* **#demo** - Sends out real-time information of demo booth participation at CPAE.\n* **#luckydraw** - Picks out a random winner from the list of candidates who have attended at least 6 demo booths.\n".format(sender_fname)
        elif in_message_sender in attendee_emails:
            out_message_mark = "Hello **{}**! I can help you with the following tasks.\n\n* **#demo** - Sends out real-time information of the number of demo booths you've attended so far.\n\nHope you're having a good time at **Cisco Partner Architect Exchange 2019**!\n".format(sender_fname)
        else:
            out_message_mark = "Hello **{}**! You need to be a registered CPAE attendee in order to be able to interact with me. If you're already registered and received this message in error, please contact andreril@cisco.com!\n".format(sender_fname)
        try:
            send_help_response = api.messages.create(roomId=in_message_roomid, markdown=out_message_mark)
        except ApiError as e:
            logging.error(e)
        return "True"

    elif in_message_text == "#demo":
        if in_message_sender in moderator_emails:
            with open('track_demo_booth.txt') as demo_b_file:
                demo_booth_dict = json.load(demo_b_file)
            out_message_mark = "Current Levels of Participation at Demo Booths -\n\n"
            for key in sorted(demo_booth_dict.keys()):
                l = "* **%s** : %s" % (key, demo_booth_dict[key]) + "\n"
                out_message_mark += l
        elif in_message_sender in attendee_emails:
            with open('track_demo_attendee.txt') as demo_a_file:
                demo_attendee_dict = json.load(demo_a_file)
            if demo_attendee_dict.get(in_message_sender) == None:
                out_message_mark = "Looks like you're yet to attend the demo booths! Please do attend the same to find out what's happening within Cisco on technologies viz. Enterprise Networking, Meraki, Collaboration, AppDynamics and many more."
            else:
                num_list = list(demo_attendee_dict.get(in_message_sender).values())
                sum_num_list = 0
                for num in num_list:
                    sum_num_list += num
                if sum_num_list == 0:
                    out_message_mark = "Looks like you're yet to attend the demo booths! Please do attend the same to find out what's happening within Cisco on technologies viz. Enterprise Networking, Meraki, Collaboration, AppDynamics and many more."
                else:
                    out_message_mark = "You have attended {} demo sessions so far at Cisco Partner Architect Exchange 2019.".format(sum_num_list)
        try:
            send_demo_response = api.messages.create(roomId=in_message_roomid, markdown=out_message_mark)
        except ApiError as e:
            logging.error(e)
        return "True"

    elif in_message_text.startswith('#sendpage ') == True:
        if in_message_sender in moderator_emails:
            out_message_text = in_message_text.replace("#sendpage ", '')
            if message_format == "html":
                out_message_html = in_message_html.replace("#sendpage ", '')
            else:
                out_message_html = ""
            logging.info("Ready to bulk send the message.")
            for n in range(len(attendee_emails)):
                out_message_html_p = "Hello " + attendee_fnames[n] + "!\n" + out_message_html
                out_message_text_p = "Hello " + attendee_fnames[n] + "!\n" + out_message_text
                logging.info(out_message_text_p)
                try:
                    send_bulk_message = send_message_person(attendee_emails[n], out_message_html_p, out_message_text_p, message_format)
                    logging.info("Bulk message successfully sent to {}.".format(attendee_emails[n]))
                except ApiError as e:
                    logging.error("Bulk message to {} FAILED!.".format(attendee_emails[n]))
                    logging.error(e)
            ack_html = "Following message has been paged successfully.\n\n" + out_message_html
            ack_text = "Following message has been paged successfully.\n\n" + out_message_text
            try:
                send_ack = send_message_room(in_message_roomid, ack_html, ack_text, message_format)
            except ApiError as e:
                logging.error(e)
            logging.info("Bulk message transsmission confirmation sent back to sender.")
        else:
            try:
                send_denial = api.messages.create(roomId=in_message_roomid, text="Sorry, you're not authorized to page messages to CPAE Attendees. Please contact amomitta@cisco.com for further assistance.")
            except ApiError as e:
                logging.error(e)
        return "True"

    elif in_message_text.startswith('#sendtogroup ') == True:
        if in_message_sender in moderator_emails:
            group_room_id = os.environ.get("CPAE_GROUP_ROOM_ID")
            out_message_text = in_message_text.replace("#sendtogroup ", '')
            logging.info("Line 186" + out_message_text)
            if message_format == "html":
                out_message_html = in_message_html.replace("#sendtogroup ", '')
            else:
                out_message_html = out_message_text
            logging.info("Ready to send the message to group space.")
            out_message_html_p = "Hello <@all>!\n" + out_message_html
            out_message_text_p = "Hello All!\n" + out_message_text
            logging.info("Line 186" + out_message_text_p)
            try:
                send_group_message = send_message_room(group_room_id, out_message_html_p, out_message_text_p, "html")
                logging.info("Group message sent successfully.")
            except ApiError as e:
                logging.error("Group message FAILED!.")
                logging.error(e)
            ack_html = "Following message has been sent to group space successfully.\n\n" + out_message_html
            ack_text = "Following message has been sent to group space successfully.\n\n" + out_message_text
            try:
                send_ack = send_message_room(in_message_roomid, ack_html, ack_text, message_format)
            except ApiError as e:
                logging.error(e)
            logging.info("Group message transsmission confirmation sent back to sender.")
        else:
            try:
                send_denial = api.messages.create(roomId=in_message_roomid, text="Sorry, you're not authorized to send group messages to CPAE Attendees. Please contact amomitta@cisco.com for further assistance.")
            except ApiError as e:
                logging.error(e)
        return "True"

    elif in_message_text == "#luckydraw":
        if in_message_sender in moderator_emails:
            qual_names_list_raw = read_list('track_demo_qual.txt')
            qual_names_list = []
            [qual_names_list.append(x) for x in qual_names_list_raw if x not in qual_names_list]
            try:
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'Fetching list of qualified candidates...'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'.......'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'...........'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'.................'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'Picking a name randomly...'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'.......'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'...........'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'.................'+'</h3>')
                time.sleep(0.5)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h3>'+'And the winner is...'+'</h3>')
                time.sleep(1)
                print = api.messages.create(roomId=in_message_roomid, html='&nbsp;<h1>'+ random.choice(qual_names_list) +'</h1>')
            except ApiError as e:
                logging.error(e)
        else:
            try:
                send_denial = api.messages.create(roomId=in_message_roomid, text="Sorry, you're not authorized to run this command. Please contact amomitta@cisco.com for further assistance.")
            except ApiError as e:
                logging.error(e)
        return "True"

    elif in_message_sender in demobooth_emails:
        if str.isdigit(in_message_text.lower()) == False:
            logging.error("A non-digit character was included in the original message.")
            msg_html = "**Error**: That's not a valid Attendee Number. Please try again."
            msg_text = "Error: That's not a valid Attendee Number. Please try again."
        else:
            logging.info("Message text only included numeric characters. Proceeding to open attendee_data.csv file...")
            for n in range(len(attendee_num)):
                if in_message_text.lower() == attendee_num[n]:
                    logging.info("Attendee match found. Sending ACK.")
                    number_demo = track_demo_attendee(attendee_emails[n], demo_name)
                    track_demo_booth(demo_name)
                    msg1_html = "Thank you for participating at CPAE Demo Booth, **{}**!".format(attendee_fnames[n].title()) + " " + "The number of demo booths you've attended so far is now **{}**.".format(number_demo)
                    msg1_text = "Thank you for participating at CPAE Demo Booth, {}!".format(attendee_fnames[n].title()) + " " + "The number of demo booths you've attended so far is now {}.".format(number_demo)
                    msg2_html = "Thank you for listening, **{}**! Please do ensure to visit at least **6 Demo Booths** in order to qualify to win a lucky draw.".format(attendee_fnames[n].title()) + " " + "The number of demo booths you've attended so far is now **{}**.".format(number_demo)
                    msg2_text = "Thank you for listening, {}! Please do ensure to visit at least 6 Demo Booths in order to qualify to win a lucky draw.".format(attendee_fnames[n].title()) + " " + "The number of demo booths you've attended so far is now {}.".format(number_demo)
                    msg3_html = "Thank you for your time, **{}**! We hope the demo was informative.".format(attendee_fnames[n].title()) + " " + "The number of demo booths you've attended so far is now **{}**.".format(number_demo)
                    msg3_text = "Thank you for your time, {}! We hope the demo was informative.".format(attendee_fnames[n].title()) + " " + "The number of demo booths you've attended so far is now {}.".format(number_demo)
                    msg_list_html = [msg1_html, msg2_html, msg3_html]
                    msg_list_text = [msg1_text, msg2_text, msg3_text]
                    msg_html = random.choice(msg_list_html)
                    msg_text = random.choice(msg_list_text)
                    min_demo = int(os.environ.get("MIN_DEMO"))
                    if number_demo == min_demo:
                        with open('track_demo_qual.txt', 'a+') as qual_file:
                            qual_file.write(attendee_fullnames[n].title() + "\n")
                        congrats_text = "Congratulations, {}! You have attended 6 demo booths and are now qualified for the lucky draw.".format(attendee_fnames[n].title())
                        try:
                            api.messages.create(toPersonEmail=attendee_emails[n], text=congrats_text)
                        except ApiError as e:
                            logging.error(e)
                    break
        if msg_html == "" and msg_text == "":
            msg_html = "You seem to have keyed in an **incorrect Attendee Number**. Please try again."
            msg_text = "You seem to have keyed in an incorrect Attendee Number. Please try again."
        logging.info("Responding to sender...")

        try:
            send_post = api.messages.create(roomId=webhook['data']['roomId'], markdown=msg_html, text=msg_text)
            logging.info("Message sent to sender - {}".format(msg_text))
        except ApiError as e:
            logging.error(e)
        return "true"
    else:
        t0 = api.rooms.get(in_message_roomid).to_dict()["created"][:-5]
        t0 = datetime.datetime.strptime(t0, '%Y-%m-%dT%H:%M:%S')
        t_delta = datetime.datetime.utcnow() - t0
        if t_delta > datetime.timedelta(minutes=1):
            try:
                api.messages.create(roomId=in_message_roomid, markdown="Something doesn't seem to be right. Please message **'help'** to understand what is it that I can do for you.")
            except ApiError as e:
                logging.error(e)
            return "true"
    return "true"

def track_demo_attendee(attendee_email, demo_name):
    with open('track_demo_attendee.txt') as demo_a_file:
        demo_attendee_dict = json.load(demo_a_file)
    if demo_attendee_dict.get(attendee_email) == None:
        demo_attendee_dict[attendee_email] = {}
    demo_attendee_dict[attendee_email][demo_name] = 1
    with open('track_demo_attendee.txt', 'w') as demo_a_file:
        json.dump(demo_attendee_dict, demo_a_file)
    num_session = 0
    for value in demo_attendee_dict[attendee_email].values():
        num_session += value
    return(num_session)

def track_demo_booth(demo_name):
    with open('track_demo_booth.txt') as demo_b_file:
        demo_booth_dict = json.load(demo_b_file)
    if demo_booth_dict.get(demo_name) == None:
        demo_booth_dict[demo_name] = 1
    else:
        demo_booth_dict[demo_name] += 1
    with open('track_demo_booth.txt', 'w') as demo_b_file:
        json.dump(demo_booth_dict, demo_b_file)
    return "True"

app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def teams_webhook():
    if request.method == 'GET':
        message = "<center><img src=\"https://cdn-images-1.medium.com/max/800/1*wrYQF1qZ3GePyrVn-Sp0UQ.png\" alt=\"Webex Teams Bot\" style=\"width:256; height:256;\"</center>" \
                  "<center><h2><b>Congratulations! Your <i style=\"color:#ff8000;\">%s</i> is up and running.</b></h2></center>" \
                  "<center><b><i>Don't forget to create Webhooks to start receiving events from Webex Teams!</i></b></center>" % bot_name
        logging.info('Bot Test via web browser successfully completed!')
        return message

    elif request.method == 'POST':
        msg_html = ""
        msg_text = ""
        webhook = request.get_json(silent=True)
        logging.info("Webhook Notification from Webex -")
        logging.info(webhook)
        logging.info("Message notification has been caused by email address = {}".format(webhook['actorId']))

        if webhook['data']['personEmail'].endswith('@webex.bot') == True and webhook['data']['personEmail'] != bot_email:
            logging.info("Webhook notification has been caused by ANOTHER BOT. #IGNORE.")
            return "True"

        elif webhook['resource'] == "memberships" and webhook['event'] == "created" and webhook['data']['personEmail'] == bot_email:
            if webhook['data']['roomType'] == 'group':
                logging.info("Bot has been added to a Group space.")
                msg_html = "Hello! Thank you for adding me to this group space. I'm not currently designed to have interactive conversations. However, there might be a few things I can assist you with. Please message **'help'** to understand what is it that I can do for you.\n\nDo note that this is a group space and I'd needed to be called specifically with `@%s` in order to be able to respond." % bot_name
                msg_text = "Hello! Thank you for adding me to this group space. I'm not currently designed to have interactive conversations. However, there might be a few things I can assist you with. Please message 'help' to understand what is it that I can do for you.\n\nDo note that this is a group space and I'd needed to be called specifically with `@%s` in order to be able to respond." % bot_name
                logging.info("Sending welcome message to the new group space - {}.".format(msg_text))
            elif webhook['data']['roomType'] == 'direct' and webhook['actorId'] != webhook['data']['personId']:
                logging.info("Bot has been added to a Private/Direct space.")
                msg_html = "Hello! Thank you for contacting me. I'm currently not designed to have interactive conversations. However, there might be a few things I can assist you with. Please message **'help'** to understand what is it that I can do for you."
                msg_text = "Hello! Thank you for contacting me. I'm currently not designed to have interactive conversations. However, there might be a few things I can assist you with. Please message **'help'** to understand what is it that I can do for you."
                logging.info("Sending welcome message to the new direct space - {}.".format(msg_text))
            try:
                send_post = api.messages.create(roomId=webhook['data']['roomId'], markdown=msg_html, text=msg_text)
                logging.info("Welcome message sent!")
            except ApiError as e:
                logging.error(e)
            return "True"

        elif webhook['resource'] == "messages" and webhook['event'] == "created" and webhook['data']['personEmail'].endswith('@webex.bot') == True:
            logging.info("Message notification has been initiated by a Bot - {}. #IGNORE.".format(webhook['data']['personEmail']))
            return "True"

        elif webhook['resource'] == "messages" and webhook['event'] == "created" and webhook['data']['personEmail'].endswith('@webex.bot') == False:
            logging.info("Incoming message from {}. ".format(webhook['data']['personEmail']) + "Is the sender a Bot? - {}.".format(webhook['data']['personEmail'].endswith('@webex.bot')))
            try:
                result_message = api.messages.get(messageId=webhook['data']['id'])
            except ApiError as e:
                logging.error(e)
            logging.info("Incoming Message abstracted from Webex -")
            logging.info(result_message)
            handle_incoming_messages(webhook, result_message, msg_html, msg_text)
            return "True"
    return "True"


def main():
    global bot_name, bot_nickname, bot_email
    logging.basicConfig(level=logging.DEBUG, filename='app_'+curr_dtf()+'.log', filemode='w', format=curr_dtl()+' %(name)s - %(levelname)s - %(message)s')
    if len(access_token) != 0:
        try:
            test_auth = api.people.me()
            bot_name = test_auth.displayName
            bot_nickname = test_auth.nickName
            bot_email = test_auth.emails[0]
        except ApiError as e:
            print("An error has occurred. Please try again.")
            sys.exit()
    else:
        print("Access Token is empty! \n"
              "Please populate it with bot's access token and run the script again.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token.")
        sys.exit()

    if "@webex.bot" not in bot_email:
        print("You have provided an access token which does not relate to a Bot Account.\n"
              "Please change for a Bot Account access token, view it and make sure it belongs to your bot account.\n"
              "Do not worry if you have lost the access token. "
              "You can always go to https://developer.webex.com/my-apps "
              "and generate a new access token for your Bot.")
        sys.exit()
    else:
        print("Initializing {}...".format(bot_name))
        del_ngrok_public_url()
        public_url = create_ngrok_public_url('CPAE_Tunnel', 'http', '9000')
        delete_existing_webhooks(api)
        try:
            webhook_name_mes = api.people.me().displayName + " Messages WebHook"
            webhook_name_mem = api.people.me().displayName + " Memberships WebHook"
        except ApiError as e:
            logging.error(e)
        if public_url is not None:
            filter_memberships = "personEmail=" + api.people.me().emails[0]
            create_webhook_messages_created(api, webhook_name_mes, public_url)
            create_webhook_memberships_created(api, webhook_name_mem, public_url, filter_memberships)
        logging.info("Webhooks Created!")
        print(".\n..\n...\n....\n.....\n{} is now running!!\n".format(bot_name))
        app.run(host='localhost', port=9000)

if __name__ == "__main__":
    main()
