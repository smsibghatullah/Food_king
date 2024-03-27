odoo.define('food_king.custom_script', function (require) {
    var core = require('web.core');
    var _t = core._t;

    function showSuccessNotification() {
        core.bus.trigger('notification', 'success', {
            title: _t('Success'),
            message: _t('Data successfully submitted.'),
            sticky: false
        });
    }

    return {
        showSuccessNotification: showSuccessNotification
    };
});
