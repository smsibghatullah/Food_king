// odoo.define('food_king.PaymentScreen', function(require) {
//     'use strict';
//     const PaymentScreen = require('point_of_sale.PaymentScreen');
//     const Registries = require('point_of_sale.Registries');
//     const session = require('web.session');

//     const InvoicePaymentScreen = PaymentScreen =>
//         class extends PaymentScreen {
//             setup() {
//                 super.setup();
//             }

//             async validateOrder(isForceValidate) {
//                 await super.validateOrder(isForceValidate);
//                 const order = this.env.pos.get_order();
//                 this.rpc({
//                     model: 'pos.order',
//                     method: 'accept_order',
//                     args: [[order.id]],
//                 }).then(function(result) {
//                     console.log("accept_order result:", result);
//                 }).guardedCatch(function(error) {
//                     console.error("accept_order error:", error);
//                 });
            
//                 this.rpc({
//                     model: 'pos.order',
//                     method: 'accept_online_order',
//                     args: [[order.id]],
//                 }).then(function(result) {
//                     console.log("accept_online_order result:", result);
//                 }).guardedCatch(function(error) {
//                     console.error("accept_online_order error:", error);
//                 });

//                 }
//             }
      

//     Registries.Component.extend(PaymentScreen, InvoicePaymentScreen);

//     return PaymentScreen;
// });