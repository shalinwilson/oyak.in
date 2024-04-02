odoo.define('cash_on_delivery.payment', function (require) {
'use strict';

var core = require('web.core');
var publicWidget = require('web.public.widget');
var checkout = require('website_sale_delivery.checkout');

var _t = core._t;
var concurrency = require('web.concurrency');

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    publicWidget.registry.carried_id = publicWidget.Widget.extend({
        selector: '#delivery_carrier',
        events: {
            'click .o_delivery_carrier_select': '_o_delivery_carrier_select',
        },
        start: function () {
            console.log("$$$$$$$$$$$")
            var self = this;
            self.reload = true
        },
        _o_delivery_carrier_select: function () {
            var self = this;

             if (self.reload) {
             self._block_ui();
                window.location.reload();
             }
        },
        _block_ui: function(){
             $('body').block();
        },

        _un_block_ui: function (){
            setTimeout(function () {
                $('body').unblock();
            }, 1000);
        },
    });

});
