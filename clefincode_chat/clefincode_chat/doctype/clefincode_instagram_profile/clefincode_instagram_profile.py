# Copyright (c) 2024, ClefinCode L.L.C-FZ and contributors
# For license information, please see license.txt

from clefincode_chat.api.api_1_2_1.api import get_last_active_sub_channel, send
from clefincode_chat.webhook import (
    format_html_string,
    get_instagram_sender_info,
    get_or_create_instagram_chat_profile,
    get_pending_messages,
    get_receiver_id,
    handle_instagram_chat_channel,
    validate_instagram_receiver_profile,
)
import frappe
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password
from klaviyo_integration.meta.instagram.message import (
    fetch_meta_conversations,
    fetch_meta_messages,
    get_sent_or_received,
)

class ClefinCodeInstagramProfile(Document):
    pass


@frappe.whitelist()
def sync_instagram_messages(profile_name):
	instagram_app_id = frappe.db.get_value(
		"ClefinCode Instagram Profile", profile_name, "instagram_app_id"
	)
	ig_user_id = frappe.db.get_value(
		"ClefinCode Instagram Profile", profile_name, "instagram_profile_id"
	)
	user = frappe.db.get_value("ClefinCode Instagram Profile", profile_name, "user")

	page_token = get_decrypted_password("Meta Settings", "Meta Settings", "page_access_token", raise_exception=False)
	page_id = frappe.db.get_single_value("Meta Settings", "page_id")

	data = {"page_token": page_token, "ig_user_id": ig_user_id, "page_id": page_id}
	print("\n\n sync instagram messages data", data)
	if not page_token or not ig_user_id or not page_id:
		frappe.throw(
			"Missing tokens. Please connect via start_oauth and oauth_callback first."
		)

	# Step 1: Get conversations
	convos = fetch_meta_conversations(
		ig_user_id, page_token, page_id, "Instagram", limit=1
	)
	# convos = test_conversation
	frappe.log_error("IG Conversations", convos)

	if "data" not in convos:
		frappe.throw("Failed to fetch IG conversations: " + str(convos))

	for convo in convos["data"]:
		convo_id = convo.get("id")
		try:
			messages = fetch_meta_messages(
				convo_id, page_token, page_id, "Instagram", limit=1
			)
			for msg in reversed(messages.get("data", [])):
				send_or_receive = get_sent_or_received(msg, ig_user_id, "Instagram")
				message = {
					"value": {
						"recipient": {
							"id": (
								convo.get("participants", {})
								.get("data", [])[0]
								.get("id")
								if convo.get("participants", {}).get("data")
								else "Unknown"
							)
						},
						"sender": {
							"id": (
								convo.get("participants", {})
								.get("data", [])[1]
								.get("id")
								if convo.get("participants", {}).get("data")
								else "Unknown"
							)
						},
					}
				}
				

				sender_id, sender_profile_name = get_instagram_sender_info(message)

				receiver_id = get_receiver_id(message)

				if not validate_instagram_receiver_profile(receiver_id):
					frappe.log_error(
						"Invalid Receiver Profile", f"Receiver ID: {receiver_id}"
					)

				instagram_profile_doc = None

				if not frappe.db.exists("ClefinCode Instagram Profile", receiver_id):
					instagram_profile_doc = frappe.db.get_value(
						"ClefinCode Chat Profile Contact Details",
						{"contact_info": receiver_id},
						"parent",
					)
				else:
					instagram_profile_doc = frappe.get_doc(
						"ClefinCode Instagram Profile", receiver_id
					)

				frappe.log_error("sync ig messages", messages)

				message_content = msg.get("message")
				message = {
					"value": {
						"message": {"text": message_content},
					}
				}

				chat_profile = get_or_create_instagram_chat_profile(
					sender_id, sender_profile_name
				)

				chat_channel_info = handle_instagram_chat_channel(
					sender_id,
					receiver_id,
					chat_profile,
					instagram_profile_doc,
					[message],
				)
				chat_channel, pending_messages = chat_channel_info
				last_sub_channel = get_last_active_sub_channel(chat_channel)["results"][
					0
				]["last_active_sub_channel"]


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
							platform="Instagram",
						)
					elif send_or_receive == "Sent":
						send(
							content=format_html_string(message_content),
							user=instagram_profile_doc.name,
							room=chat_channel,
							email=user,
							sub_channel=last_sub_channel,
							sync=1,
							msg_id=msg.get("id"),
							time=convert_iso_to_frappe_datetime(msg.get("created_time")),
							send_or_received="Sent",
							platform="Instagram",
						)

		except Exception as e:
			frappe.log_error(
				f"Error processing IG conversation:", f"{convo['id']}: {str(e)}"
			)

def convert_iso_to_frappe_datetime(iso_time):
	from datetime import datetime

	# Convert ISO timestamp to Python datetime
	dt = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M:%S%z")

	# Convert to Frappe / MariaDB format
	frappe_datetime = dt.strftime("%Y-%m-%d %H:%M:%S")
	# frappe_date = dt.strftime("%Y-%m-%d")

	return frappe_datetime

