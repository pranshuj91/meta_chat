// Copyright (c) 2025, ClefinCode L.L.C-FZ and contributors
// For license information, please see license.txt

frappe.ui.form.on('ClefinCode Facebook Messenger Profile', {
	refresh: function(frm) {
		frm.add_custom_button(__('Sync Facebook Messages'), () => {
			frappe.call({
				method: 'clefincode_chat.clefincode_chat.doctype.clefincode_facebook_messenger_profile.clefincode_facebook_messenger_profile.sync_facebook_messages',
				args: {
					profile_name: frm.doc.name
				},
				callback: function(response) {
					if (response.message) {
						frappe.msgprint(__('Facebook messages synced successfully.'));
					} else {
						frappe.msgprint(__('Failed to sync Facebook messages.'));
					}
				}
			})
		});
	}
});
