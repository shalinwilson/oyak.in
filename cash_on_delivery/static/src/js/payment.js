
odoo.define('cash_on_delivery.payment', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    require('website_sale_delivery.checkout');

    publicWidget.registry.websiteSaleDelivery.include({

        _handleCarrierUpdateResult: function (result) {

    this._super.apply(this, arguments);

    if (!result.allowed_provider_ids) {
        return;
    }

    // Hide and disable everything
    $('.o_payment_option_card').hide();

    $('input[name="o_payment_radio"]')
        .prop('checked', false)
        .prop('disabled', true);

    // Show and enable allowed providers
    result.allowed_provider_ids.forEach(function(id) {

        var $radio = $('input[data-payment-option-id="' + id + '"]');

        $radio
            .prop('disabled', false);

        $radio
            .closest('.o_payment_option_card')
            .show();

    });
    var $allowed = $('input[name="o_payment_radio"]:enabled');

if ($allowed.length) {
    $allowed.first()
        .prop('checked', true)
        .trigger('change');
}

},
    });

});

//odoo.define('cash_on_delivery.payment', function (require) {
//'use strict';
//
//var core = require('web.core');
//var publicWidget = require('web.public.widget');
//var checkout = require('website_sale_delivery.checkout');
//
//var _t = core._t;
//var concurrency = require('web.concurrency');
//
//    var publicWidget = require('web.public.widget');
//    var ajax = require('web.ajax');
//    publicWidget.registry.carried_id = publicWidget.Widget.extend({
//        selector: '#delivery_carrier',
//        events: {
//            'click .o_delivery_carrier_select': '_o_delivery_carrier_select',
//        },
//        start: function () {
//            console.log("$$$$$$$$$$$")
//            var self = this;
//            self.reload = true;
////             console.log("$$$$$$$$$$$",self.reload)
//        },
//        _o_delivery_carrier_select: function () {
//            var self = this;
//
//             if (self.reload) {
//                self._block_ui();
//             }
//        },
//        _block_ui: function(){
//             $('body').block();
//        },
//
//        _un_block_ui: function (){
//            setTimeout(function () {
//                $('body').unblock();
//            }, 1000);
//        },
//    });
//
//
//publicWidget.registry.websiteSaleDelivery.include({
//        start: function () {
//            var self = this;
//            this._super();
//            self.delivery_type = $('#delivery_carrier input[name="delivery_type"]:checked').val();
//        },
//        _handleCarrierUpdateResultBadge: function (result) {
//        var $carrierBadge = $('#delivery_carrier input[name="delivery_type"][value=' + result.carrier_id + '] ~ .o_wsale_delivery_badge_price');
//
//        if (result.status === true) {
//             // if free delivery (`free_over` field), show 'Free', not '$0'
//             if (result.is_free_delivery) {
//                 $carrierBadge.text(_t('Free'));
//             } else {
//                 $carrierBadge.html(result.new_amount_delivery);
//             }
//             $carrierBadge.removeClass('o_wsale_delivery_carrier_error');
//        } else {
//            $carrierBadge.addClass('o_wsale_delivery_carrier_error');
//            $carrierBadge.text(result.error_message);
//        }
//        var self = this;
//        var selected_delivery = $('#delivery_carrier input[name="delivery_type"]:checked').val();
//        if (self.delivery_type != selected_delivery) {
//            window.location.reload();
//        }
//    },
//
//});
//});
