# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    is_cash_on_delivery = fields.Boolean(default=False)

    @api.model
    def get_delivery_charge_product(self, order_id):
        order_lines = self.env['sale.order.line'].search([('order_id', '=', order_id)])
        for line in order_lines:
            if line.product_id.default_code == 'Delivery_1000':  # Assuming delivery charges are represented as service type products
                return line.product_id
        return False


# a = [{
#     "add": "M25,NelsonMarg", (mandatory)
#         "address_type": "home" / "office", (optional)
# "phone": "1234567890", (mandatory)
# "payment_mode": "Prepaid/COD/Pickup/REPL", (mandatory)
# "name": "name-of-the-consignee", (mandatory)
# "pin": 325007, (mandatory)
# "order": "orderid", (mandatory)
# "consignee_gst_amount": "for ewaybill-incase of intra-state required only",
# "integrated_gst_amount": "for ewaybill-incase of intra-state required only",
# "ewbn": "if ewbn is there no need to send additional keys for generating ewaybill only if the total package amount is greater than or equal to 50k",
# "consignee_gst_tin": "consignee_gst_tin",
# "seller_gst_tin": "seller_gst_tin",
# "client_gst_tin": "client_gst_tin",
# "hsn_code": "Required for ewaybill-hsn_code",
# "gst_cess_amount": "for ewaybill-gst_cess_amount",
# "shipping_mode": "Surface/Express",
# "client": "client-name-as-registered-with-delhivery", (optional)
# "tax_value": "taxvalue", (optional)
# "seller_tin": "sellertin", (optional)
# "seller_gst_amount": "for ewaybill-incase of intra-state required only", (optional)
# "seller_inv": "sellerinv", (optional)
# "city": "Kota", (optional)
# "commodity_value": "commodityvalue", (optional)
# "weight": "weight(gms)", (optional)
# "return_state": "returnstate", (optional)
# "document_number": "for ewaybill-document_number,only mandatory in case of ewbn", (optional)
# "od_distance": "ditance between origin and destination", (optional)
# "sales_tax_form_ack_no": "ackno.", (optional)
# "document_type": "for ewaybill-document_type,only mandatory in case of ewbn", (optional)
# "seller_cst": "sellercst", (optional)
# "seller_name": "sellername", (optional)
# "fragile_shipment": "true", (Optional, If content is fragile, Key Value must be true else false)
# "return_city": "returncity", (optional)
# "return_phone": "returnphone", (optional)
# "qc": {(optional) // qc
# field
# only
# required
# for RVP packages for QC check      "item": [{
#     "images": "img1-static image url",
#     "color": "Color of the product",
#     "reason": "Damaged Product/Return reason of the product",
#     "descr": "description of the product",
#     "ean": "EAN no. that needs to be checked for a product (apparels)",
#     "imei": "IMEI no. that needs to be checked for a product (mobile phones)",
#     "brand": "Brand of the product",
#     "pcat": "Product category like mobile, apparels etc.",
#     "si": "special instruction for FE",
#     "item_quantity": 2}]},
# "shipment_height": 10, (optional)
# "shipment_width": 11, (optional)
# "shipment_length": 12, (optional)
# "category_of_goods": "categoryofgoods", (optional)
# "cod_amount": 2125, (optional)
# "return_country": "returncountry", (optional)
# "shipment_width": "shipmentwidth", (optional)
# "document_date": "for ewaybill-datetime,mandatory in case of ewbn", (optional)
# "taxable_amount": "for ewaybill-taxable_amount in case of multiple items only", (optional)
# "products_desc": "for ewaybill-mandatory,incase of intra-state required only", (optional)
# "state": "Rajasthan", (optional)
# "dangerous_good": "True/False", (optional)
# "waybill": "waybillno.(trackingid)", (optional)
# "consignee_tin": "consigneetin", (optional)
# "order_date": "2017-05-20 12:00:00", (optional)
# "return_add": "returnaddress", (optional)
# "total_amount": 21840, (optional)
# "seller_add": "selleradd", (optional)
# "country": "India", (optional) // It
# will
# be
# mandatory
# for Bangladesh and value should be "BD"    "return_pin": "returnpin", (optional)
# "extra_parameters": {(optional)
# "return_reason": "string"},
# "return_name": "name", (optional)
# "supply_sub_type": "for ewaybill-supply_sub_type,mandatory in case of ewbn", (optional)
# "plastic_packaging": "true/false", (optional)
# "quantity": "quantity"(optional)}],
# "pickup_location": {
#     "name": "client-warehouse-name-as-registered-with-delhivery", (mandatory)
#         "city": "city",
# "pin": "pin-code",
# "country": "country",
# "phone": "phoneno.",
# "add": "address-of-warehouse"}}]
