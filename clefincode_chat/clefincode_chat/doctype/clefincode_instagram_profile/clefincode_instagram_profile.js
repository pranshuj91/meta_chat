// Copyright (c) 2024, ClefinCode L.L.C-FZ and contributors
// For license information, please see license.txt

frappe.ui.form.on('ClefinCode Instagram Profile', {
	refresh: function(frm) {
		frm.add_custom_button(__('Sync Instagram Messages'), () => {
			frappe.call({
				method: 'clefincode_chat.clefincode_chat.doctype.clefincode_instagram_profile.clefincode_instagram_profile.sync_instagram_messages',
				args: {
					profile_name: frm.doc.name
				},
				callback: function(response) {
					if (response.message) {
						frappe.msgprint(__('Instagram messages synced successfully.'));
					} else {
						frappe.msgprint(__('Failed to sync Instagram messages.'));
					}
				}
			})
		});
	}
});
