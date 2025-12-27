import frappe
import logging
import urllib.parse

#logger = logging.getLogger(__name__)
#logging.basicConfig(filename='ls-erp/logs/karp_communication.log', level=logging.INFO)

@frappe.whitelist()
def get_wa_link(customer_name, wa_template_name=None,order_id=None,):

    wa_url = "https://web.whatsapp.com/send/?type=phone_number&app_absent=0&";    
    contact_doc = get_contact_for_customer(customer_name)
    wa_url = wa_url + "phone="+contact_doc.mobile_no

    if(wa_template_name) : 
        message = construct_message(wa_template_name, customer_name, order_id, contact_doc)
        wa_url = wa_url + "&text=" + message

    return wa_url



def construct_message(wa_template_name, customer_name, order_id, contact_doc):

    wa_template = frappe.get_doc("WA Template", {"name": wa_template_name})

    context = build_context(wa_template_name, customer_name, order_id, contact_doc)



    message = urllib.parse.quote(frappe.render_template(wa_template.message_template, context))

    return message

def build_context(wa_template_name, customer_name, order_id, contact_doc):
   
    if(wa_template_name == "Thankyou Msg"):
        loyalty_points = int(get_total_loyalty_points_for_customer(customer_name))
        context = {
            "first_name": contact_doc.first_name if (len(contact_doc.first_name) != 0) else "Customer",
            "loyalty_points": loyalty_points
        }
        return context
    if(wa_template_name == "Welcome Msg"):
        context = {
            "first_name": contact_doc.first_name if (len(contact_doc.first_name) != 0) else "Customer",
            "order_id": order_id
        }
        return context
    else: 
        context = {
            "first_name": contact_doc.first_name if (len(contact_doc.first_name) != 0) else "Customer"
        }
        return context


def get_contact_for_customer(customer_name):
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
        contact_doc = frappe.get_doc('Contact', contact_name)
        return contact_doc
    else:
        return None

def get_total_loyalty_points_for_customer(customer_name):
    query = """
        SELECT SUM(loyalty_points) as total_loyalty_points
        FROM `tabLoyalty Point Entry`
        WHERE customer = %s
    """ 
    # Execute the query with customer_name as the parameter
    result = frappe.db.sql(query, customer_name)

    # Return the total loyalty points, or 0 if no record is found
    return result[0][0] if result and result[0][0] else 0

@frappe.whitelist()
def get_wa_link_for_eye_camp_marketing(id):

    wa_url = "https://web.whatsapp.com/send/?type=phone_number&app_absent=0&";    
    eye_camp_lead = frappe.get_doc("Eye Camp Lead", id)
    #logger.info('Gettting WA Message')
    wa_url = wa_url + "phone="+eye_camp_lead.mobile_number
    wa_template = frappe.get_doc("WA Template", {"name": "Eye Camp Outreach Message"})
    context = {
        "first_name": eye_camp_lead.first_name if (len(eye_camp_lead.first_name) != 0) else "Customer",
    }

    message = urllib.parse.quote(frappe.render_template(wa_template.message_template, context))
    wa_url = wa_url + "&text=" + message

    return wa_url
