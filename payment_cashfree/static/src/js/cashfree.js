/* global Cashfree */
odoo.define('payment_cashfree.cashfree', require => {
    'use strict';

    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const cashfreeMixin = {
        _processRedirectPayment: function (code, paymentOptionId, processingValues) {
            if (code !== 'cashfree') {
                return this._super(...arguments);
            }

            var paymentMode = processingValues.paymentMode;
            var paymentSessionId = processingValues.paymentSessionId;
            var  returnUrl = processingValues.returnUrl;

            const cashfree = Cashfree({
				mode: paymentMode
            });
            let checkoutOptions = {
                paymentSessionId: paymentSessionId,
                returnUrl: returnUrl
            }
            cashfree.checkout(checkoutOptions).then(function(result){
                if(result.error){
                    alert(result.error.message)
                }
                if(result.redirect){
                }
            });
        },
    };

    checkoutForm.include(cashfreeMixin);
    manageForm.include(cashfreeMixin);

});
