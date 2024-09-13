import frappe

@frappe.whitelist()
def get_wa_link(customer_name, wa_template_name):

    wa_url = "https://wa.me/";    

    linked_contacts = frappe.get_all(
        'Dynamic Link',
        filters={
            'link_doctype': 'Customer',
            'link_name': customer_name
        },
        fields=['parent'],
        ignore_permissions=True
    )

    if linked_contacts:
        # Get the contact name from the result
        contact_name = linked_contacts[0]['parent']

        # Fetch the contact details (phone, mobile_no)
        contact_details = frappe.get_value(
            'Contact',
            contact_name,
            ['mobile_no'],
            as_dict=True
        )
        wa_template = frappe.get_doc("WA Template", {"name": wa_template_name})
        wa_url = wa_url + contact_details.mobile_no
        wa_url = wa_url + "?text=" + wa_template.message_template

        return wa_url
    return None