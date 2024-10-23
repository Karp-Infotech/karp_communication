import frappe
import logging
import json
import urllib.parse
from datetime import date

#logger = logging.getLogger(__name__)
#logging.basicConfig(filename='ls-erp/logs/karp_communication.log', level=logging.INFO)

@frappe.whitelist()
def get_data_for_welcome_msg():

    welcome_wa_template = frappe.get_doc('WA Template', "Welcome Message")
    message_template =  welcome_wa_template.message_template
    customers = get_customers_with_pending_sales_orders()
    customer_data = build_customer_json(customers)
    response_json = {
        "message_template": message_template,
        "customer_data": customer_data
    }
    return response_json

@frappe.whitelist()
def get_data_for_thankyou_msg():
    thankyou_wa_template = frappe.get_doc('WA Template', "Thankyou Msg")
    message_template =  thankyou_wa_template.message_template
    customers = get_customers_with_completed_sales_orders()
    customer_data = build_customer_json(customers)
    response_json = {
        "message_template": message_template,
        "customer_data": customer_data
    }
    return response_json

@frappe.whitelist()
def get_data_for_order_ready_msg():
    order_ready_wa_template = frappe.get_doc('WA Template', "Order Ready Msg")
    message_template =  order_ready_wa_template.message_template
    customers = get_customers_with_order_ready_sales_orders()
    customer_data = build_customer_json(customers)
    response_json = {
        "message_template": message_template,
        "customer_data": customer_data
    }
    return response_json

def build_customer_json(customers):

    frappe.logger().debug("Customers : ")
    frappe.logger().debug(customers)
    
    customer_list = []
    
    # Iterate over the customers and fetch the Mobile Number from the 'Customer' document
    for customer in customers:
        
        contact_doc = get_contact_for_customer(customer.get("customer"))
        if contact_doc is not None:
            # Assume mobile number is stored in 'mobile_no' field in the customer document
            mobile_number = contact_doc.mobile_no if contact_doc.mobile_no else "N/A"

            # Build the JSON object for each customer
            customer_data = {
                "First Name": contact_doc.first_name,
                "Mobile Number": mobile_number,
                "Loyalty Points":get_total_loyalty_points_for_customer(customer.get("customer")),
                "Sales Order": customer.get("sales_order"),
                "Store": customer.get("store")
            }
            
            # Add to the list
            customer_list.append(customer_data)
    
    # Convert the list to JSON format
    customer_json = json.dumps(customer_list, indent=4)
    
    return customer_json

def get_customers_with_pending_sales_orders():
    # Query to get customers with Sales Orders in "To Deliver and Bill" or "To Bill" status
    customers_sales_order = frappe.db.sql("""
        SELECT so.customer, so.name, so.set_warehouse
        FROM `tabSales Order` so, `tabCommunication Status` cs
        WHERE so.name = cs.sales_order and so.status IN ('To Deliver and Bill', 'To Bill') and cs.welcome_msg_status = 'Not Sent'
    """, as_dict=True)
    
    return [{'customer': cust_so['customer'], 'sales_order': cust_so['name'], 'store': cust_so['set_warehouse'], } for cust_so in customers_sales_order]

def get_customers_with_completed_sales_orders():
    # Query to get customers with Sales Orders in "To Deliver and Bill" or "To Bill" status
    customers_sales_order = frappe.db.sql("""
        SELECT so.customer, so.name, so.set_warehouse
        FROM `tabSales Order` so, `tabCommunication Status` cs
        WHERE so.name = cs.sales_order and so.status = 'Completed' and cs.thankyou_msg_status = 'Not Sent'
    """, as_dict=True)
    
    return [{'customer': cust_so['customer'], 'sales_order': cust_so['name'], 'store': cust_so['set_warehouse']} for cust_so in customers_sales_order]

def get_customers_with_order_ready_sales_orders():
    # Query to get customers with Sales Orders in "To Deliver and Bill" or "To Bill" status
    customers_sales_order = frappe.db.sql("""
        SELECT so.customer, so.name, so.set_warehouse
        FROM `tabSales Order` so, `tabCommunication Status` cs
        WHERE so.name = cs.sales_order and so.status = 'To Bill' and cs.order_ready_msg_status = 'Not Sent'
    """, as_dict=True)
    
    return [{'customer': cust_so['customer'], 'sales_order': cust_so['name'], 'store': cust_so['set_warehouse']} for cust_so in customers_sales_order]



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

    return_status = []
    
    for com_status in json_com_status_list:
        sales_order = com_status.get("sales_order")
        try:

            # Fetch the Customer Communication document using communication_id
            communication_doc = frappe.get_doc(
                'Communication Status',
                {'sales_order': sales_order}  # Filter criteria
            )
            if(communication_doc):
                
                if(com_status.get("welcome_msg_status")):
                    
                    communication_doc.welcome_msg_status = com_status.get("welcome_msg_status")

                if(com_status.get("thankyou_msg_status")):
                    
                    communication_doc.thankyou_msg_status = com_status.get("thankyou_msg_status")
                
                if(com_status.get("order_ready_msg_status")):
                    
                    communication_doc.order_ready_msg_status = com_status.get("order_ready_msg_status")



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

    
def get_total_loyalty_points_for_customer(customer_name):
    query = """
        SELECT SUM(loyalty_points) as total_loyalty_points
        FROM `tabLoyalty Point Entry`
        WHERE customer = %s
    """ 
    # Execute the query with customer_name as the parameter
    result = frappe.db.sql(query, customer_name)

    # Return the total loyalty points, or 0 if no record is found
    return int(result[0][0] if result and result[0][0] else 0)



@frappe.whitelist()
def get_active_wa_marketing_campaigns():
    wa_campaigns = frappe.get_all(
        'WA Campaign',
        filters={
            'status': 'Active'
        },
        fields=['*'],
        ignore_permissions=True
    )
    campaign_list = []
    for campaign in wa_campaigns:
       campaign_list.append(build_campaign_json(campaign))
    return campaign_list


def build_campaign_json(campaign):
    wa_template = frappe.get_doc('WA Template', campaign.get("wa_msg_template"))
    return {
        "Campaign Name": campaign.get("name"),
        "WA Message": wa_template.get("message_template"),
        "Store": campaign.get("store"),
        "Customers": build_customer_data_json(campaign)
	}

def build_customer_data_json(campaign):

    customer_query = campaign.get("cust_selection_query")
    customers = []

    query_params = [
            campaign.get("name"), 
            campaign.get("start_date")
        ]
    if campaign.get("store"):
        query_params.append(campaign.get("store"))

    query_params.append(campaign.get("msg_count_per_run"))
    
    customers = frappe.db.sql(customer_query, query_params, as_dict=True)

    return build_customers_json_for_marketing_campaign(customers)



def build_customers_json_for_marketing_campaign(customers):

    customer_list = []
    
    # Iterate over the customers and fetch the Mobile Number from the 'Customer' document
    for customer in customers:
        
        contact_doc = get_contact_for_customer(customer.get("name"))

        if contact_doc is not None:
            # Assume mobile number is stored in 'mobile_no' field in the customer document
            mobile_number = contact_doc.mobile_no if contact_doc.mobile_no else "N/A"

            # Build the JSON object for each customer
            customer_data = {
                "First Name": contact_doc.first_name,
                "Mobile Number": mobile_number,
                "Customer Name": customer.get("name")
            }
            
            # Add to the list
            customer_list.append(customer_data)
    
    # Convert the list to JSON format
    customers_json = json.dumps(customer_list, indent=4)
    
    return customers_json


@frappe.whitelist()
def update_cust_campaign_inc_on_server():
        
    # Parse the incoming JSON data
    json_cust_campaign_inc_list = frappe.request.get_json()
    return_status = None
    for cust_campaign_inc in json_cust_campaign_inc_list:

        cust = cust_campaign_inc.get("Customer")
        campaign = cust_campaign_inc.get("Campaign")

        try:

            
            # Fetch the Customer Communication document using communication_id
            cust_campaign_inc_doc_name = frappe.get_value('Cust WA Campaign Inclusion', {
                'wa_campaign': campaign,
                'customer': cust
            })
            cust_campaign_inc_doc = None
            if cust_campaign_inc_doc_name:
                cust_campaign_inc_doc = frappe.get_doc('Cust WA Campaign Inclusion', cust_campaign_inc_doc_name)

            if(cust_campaign_inc_doc):
                
                contacted_counts = cust_campaign_inc_doc.get("total_contacted_count")

                contacted_counts = contacted_counts + 1

                cust_campaign_inc_doc.total_contacted_count = contacted_counts

                cust_campaign_inc_doc.last_contacted = date.today()

                # Save the changes to the database
                cust_campaign_inc_doc.save()

            else:
                cust_campaign_inc_doc = frappe.get_doc({
                    "doctype": "Cust WA Campaign Inclusion",
                    "customer": cust,  
                    "wa_campaign": campaign,
                    "last_contacted": date.today(),
                    "total_contacted_count": 1
                })
                cust_campaign_inc_doc.insert(ignore_permissions=True) 
            # Commit the transaction to ensure it's saved
            
            return_status = {'Status': "Success", "message": "Customer Campaign Inclusion updated/inserted successfully"}
        except Exception as e:
            # Handle exceptions and return an error message
            frappe.log_error(frappe.get_traceback(), "Update / Insert to Cust WA Campaign Inclusion Failed")
            print(frappe.get_traceback() + "Update / Insert to Cust WA Campaign Inclusion Failed")
            return_status = {'Status': "Failure", "message": "Customer Campaign Inclusion updated/inserted failed"}
    frappe.db.commit()

    return return_status