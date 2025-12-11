# Copyright (c) 2025, ClefinCode L.L.C-FZ and contributors
# For license information, please see license.txt

from clefincode_chat.api.api_1_2_1.api import get_last_active_sub_channel, send

from clefincode_chat.webhook import format_html_string, get_messenger_sender_info, get_or_create_messenger_chat_profile, get_receiver_id, handle_messenger_chat_channel, validate_messenger_receiver_profile
import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password
from klaviyo_integration.meta.instagram.message import (
    fetch_meta_conversations,
    fetch_meta_messages,
    get_sent_or_received,
)
class ClefinCodeFacebookMessengerProfile(Document):
	pass



@frappe.whitelist()
def sync_facebook_messages(profile_name):

	ig_user_id = frappe.db.get_value(
		"ClefinCode Facebook Messenger Profile", profile_name, "messenger_profile_id"
	)
	user = frappe.db.get_value("ClefinCode Facebook Messenger Profile", profile_name, "user")

	page_token = get_decrypted_password("Meta Settings", "Meta Settings", "page_access_token", raise_exception=False)
	page_id = frappe.db.get_single_value("Meta Settings", "page_id")

	data = {"page_token": page_token, "ig_user_id": ig_user_id, "page_id": page_id}

	print("\n\n sync facebook messages data", data)
	if not page_token or not ig_user_id or not page_id:
		frappe.throw(
			"Missing tokens. Please connect via start_oauth and oauth_callback first."
		)

	# Step 1: Get conversations
	convos = fetch_meta_conversations(
		ig_user_id, page_token, page_id, "Facebook", limit=1
	)
	# convos = test_conversation
	frappe.log_error("FB Conversations", convos)

	if "data" not in convos:
		frappe.throw("Failed to fetch FB conversations: " + str(convos))

	for convo in convos["data"]:
		convo_id = convo.get("id")
		# try:
		if 1 == 1:
			messages = fetch_meta_messages(
				convo_id, page_token, page_id, "Facebook", limit=1
			)
			for msg in reversed(messages.get("data", [])):
				send_or_receive = get_sent_or_received(msg, ig_user_id, "Facebook")
				message = {
					"value": {
						"recipient": {
							"id": (
								convo.get("participants", {})
								.get("data", [])[1]
								.get("id")
								if convo.get("participants", {}).get("data")
								else "Unknown"
							)
						},
						"sender": {
							"id": (
								convo.get("participants", {})
								.get("data", [])[0]
								.get("id")
								if convo.get("participants", {}).get("data")
								else "Unknown"
							)
						},
					}
				}
				

				sender_id, sender_profile_name = get_messenger_sender_info(message)
				receiver_id = get_receiver_id(message)

				if not validate_messenger_receiver_profile(receiver_id):
					frappe.log_error("Invalid Receiver Profile", f"Receiver ID: {receiver_id}")

				messenger_profile_doc = None
						
				if not frappe.db.exists("ClefinCode Facebook Messenger Profile", receiver_id):
					messenger_profile_doc = frappe.db.get_value(
					"ClefinCode Chat Profile Contact Details",
					{"contact_info": receiver_id},
					"parent" 
					)
				else:
					messenger_profile_doc = frappe.get_doc("ClefinCode Facebook Messenger Profile", receiver_id)
				
				frappe.log_error("sync fb messages", messages)

				message_content = msg.get("message")
				message = {
					"value": {
						"message": {"text": message_content},
					}
				}
				print("\n\n mess pro", messenger_profile_doc)
				print("\n\n mess pro", type(messenger_profile_doc))

				chat_profile = get_or_create_messenger_chat_profile(sender_id, sender_profile_name)
				print("\n\n chat profile", chat_profile)
				chat_channel_info = handle_messenger_chat_channel(sender_id, receiver_id, chat_profile, messenger_profile_doc, [message])
				print("\n\n chat channel info", chat_channel_info)
				chat_channel, pending_messages = chat_channel_info
				last_sub_channel = get_last_active_sub_channel(chat_channel)["results"][0]["last_active_sub_channel"]
				

				if message_content:
					if send_or_receive == "Received":
						send(
							content=format_html_string(message_content),
							user=sender_profile_name,
							room=chat_channel,
							email=sender_id,
							sub_channel=last_sub_channel,
							sync=1,
							msg_id=msg.get("id"),
							time=convert_iso_to_frappe_datetime(msg.get("created_time")),
							send_or_received="Received",
							platform="Facebook",
						)
					elif send_or_receive == "Sent":
						send(
							content=format_html_string(message_content),
							user=messenger_profile_doc.name,
							room=chat_channel,
							email=user,
							sub_channel=last_sub_channel,
							sync=1,
							msg_id=msg.get("id"),
							time=convert_iso_to_frappe_datetime(msg.get("created_time")),
							send_or_received="Sent",
							platform="Facebook",
						)

		# except Exception as e:
		# 	frappe.log_error(
		# 		f"Error processing FB conversation:", f"{convo['id']}: {str(e)}"
		# 	)

def convert_iso_to_frappe_datetime(iso_time):
	from datetime import datetime

	# Convert ISO timestamp to Python datetime
	dt = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S%z")

	# Convert to Frappe / MariaDB format
	frappe_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
	# frappe_date = dt.strftime("%Y-%m-%d")

	return frappe_datetime

