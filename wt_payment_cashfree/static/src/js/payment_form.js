/** @odoo-module */
import checkoutForm from "@payment/js/checkout_form";
import manageForm from "@payment/js/manage_form"

const CashfreeMixin = {
	/**
     * Redirect the customer to Cashfree hosted payment page.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} code - The code of the payment option
     * @param {number} paymentOptionId - The id of the payment option handling the transaction
     * @param {object} processingValues - The processing values of the transaction
     * @return {undefined}
     */
	_processRedirectPayment: function (code, paymentOptionId, processingValues) {
		if (code !== 'cashfree') {
			return this._super(...arguments);
		}
		if(processingValues.status === "enabled"){
			var mode = "production"
		}else{
			var mode = "sandbox"
		}

		const cashfree = Cashfree({
				mode: mode
		});
		let checkoutOptions = {
			paymentSessionId: processingValues.payment_session_id,
			returnUrl: processingValues.order_meta.return_url
		}
		cashfree.checkout(checkoutOptions).then(function(result){
			if(result.error){
				alert(result.error.message)
			}
			if(result.redirect){
				console.log('success')
			}
		});
	},
};

checkoutForm.include(CashfreeMixin);
manageForm.include(CashfreeMixin);
