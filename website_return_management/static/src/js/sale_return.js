odoo.define('website_return_management.return', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

            $(document).on('click', '.cancel-order-btn', function(ev) {
            ev.preventDefault();
            console.log("workinnnnnnnnnnnnnnnnnn");

            if (confirm('Are you sure you want to cancel this order?')) {
            var orderId = $(this).data('order_id'); // Use $(this) instead of $(ev.currentTarget)
            console.log(orderId)
            ajax.jsonRpc('/cancel_order', 'call', {'order_id': orderId})
                .then(function(result) {
                    if (result.success) {
                        // Order canceled successfully, perform necessary actions
                        alert('Order canceled successfully, if its prepaid order, please call us for refund');
                        // Refresh the page or update UI as needed
                        location.reload();
                    } else {
                        // Failed to cancel order, show error message
                        alert(result.error);
                    }
                });
        }
        });

        $("#hidden_box_btn").on('click', function () {
            $('#hidden_box').modal('show');
        });

        $("#product").on('change', function(){
            var x = $('#submit');
            x.addClass('d-none');
            if ($("#product").val() == 'none') {
                if (!x.hasClass('d-none')) {
                    x.addClass('d-none');
                }
            } else {
                if (x.hasClass('d-none')) {
                    x.removeClass('d-none');
                }
            }
        });
    });


