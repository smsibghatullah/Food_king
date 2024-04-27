odoo.define('food_king.custom_js', function (require) {
    var core = require('web.core');
    var WebClient = require('web.WebClient');
    var _t = core._t;

    WebClient.include({
        onclick_sticky_notification: function(){ 
            this.do_notify("Error", "Please Check the values before save");
        }
    });
});
