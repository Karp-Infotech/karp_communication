import frappe
import logging
import json
import urllib.parse

logger = logging.getLogger(__name__)
logging.basicConfig(filename='ls-erp/logs/karp_communication.log', level=logging.INFO)

@frappe.whitelist()
def get_cust_for_welcome_msg():

    welcome_wa_template =  contact_doc = frappe.get_doc('WA Template', "Welcome Message")
    message_template =  welcome_wa_template.message_template
    customer_data = build_customer_json()
    response_json = {
        "message_template": message_template,
        "customer_data": customer_data
    }
    return response_json


    
def build_customer_json():
    customers = get_customers_with_pending_sales_orders()
    
    customer_list = []
    
    # Iterate over the customers and fetch the Mobile Number from the 'Customer' document
    for customer in customers:
        
        contact_doc = get_contact_for_customer(customer.get("customer"))
        
        # Assume mobile number is stored in 'mobile_no' field in the customer document
        mobile_number = contact_doc.mobile_no if contact_doc.mobile_no else "N/A"
        
        # Build the JSON object for each customer
        customer_data = {
            "First Name": contact_doc.first_name,
            "Mobile Number": mobile_number,
            "Sales Order": customer.get("sales_order")
        }
        
        # Add to the list
        customer_list.append(customer_data)
    
    # Convert the list to JSON format
    customer_json = json.dumps(customer_list, indent=4)
    
    return customer_json

def get_customers_with_pending_sales_orders():
    # Query to get customers with Sales Orders in "To Deliver and Bill" or "To Bill" status
    customers_sales_order = frappe.db.sql("""
        SELECT so.customer, so.name
        FROM `tabSales Order` so, `tabCommunication Status` cs
        WHERE so.name = cs.sales_order and so.status IN ('To Deliver and Bill', 'To Bill') and cs.welcome_msg_status = 'Not Sent'
    """, as_dict=True)
    
    return [{'customer': cust_so['customer'], 'sales_order': cust_so['name']} for cust_so in customers_sales_order]

#This method creates initial communication status with default values in db when new Sales Order is created.
def create_communication_status(doc, method):
    
    communication_statuses = frappe.get_doc({
        "doctype": "Communication Status",
        "sales_order": doc.name,  
    })
    communication_statuses.insert(ignore_permissions=True)  # Insert the document into the database


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
    


@frappe.whitelist()
def update_communication_status():
        
    # Parse the incoming JSON data
    json_com_status_list = frappe.request.get_json()
    print(frappe.request.get_json())

    return_status = []
    

    for com_status in json_com_status_list:
        sales_order = com_status.get("sales_order")
        try:
            # Extract fields from the JSON         
            print("Sales Order" + sales_order)

            # Fetch the Customer Communication document using communication_id
            communication_doc = frappe.get_doc(
                'Communication Status',
                {'sales_order': sales_order}  # Filter criteria
            )
            if(communication_doc):
                
                if(com_status.get("welcome_msg_status")):
                    
                    communication_doc.welcome_msg_status = com_status.get("welcome_msg_status")

                # Save the changes to the database
                communication_doc.save()

                # Commit the transaction to ensure it's saved
                frappe.db.commit()

                success_status = {'sales_order': sales_order, "status": "Success", "message": "Communication status updated successfully"}
                return_status.append(success_status)
            else :

                failure_status = {'sales_order': sales_order, "status": "Failure", "message": "Communication status associated to Sales Order could not be found" }
                return_status.append(failure_status)

        except Exception as e:
            # Handle exceptions and return an error message
            frappe.log_error(frappe.get_traceback(), "Update to Communication Status Failed")
            error_status = {'sales_order': sales_order, "status": "Error", "message": str(e) }
            return_status.append(error_status)

    return return_status

    
