/*
    Copyright 2020 Akretion France (http://www.akretion.com/)
    @author: Alexis de Lattre <alexis.delattre@akretion.com>
    @author: Stéphane Bidoul <stephane.bidoul@acsone.eu>
    License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
*/

var kekrpc;

odoo.define("pos_vevent_terminal.payment", function (require) {
    "use strict";

    var core = require("web.core");
    var rpc = require("web.rpc")
    kekrpc = rpc;

    var PaymentInterface = require("point_of_sale.PaymentInterface");
    const {Gui} = require("point_of_sale.Gui");

    var _t = core._t;

    var VeventPaymentTerminal = PaymentInterface.extend({
        init: function () {
            this._super.apply(this, arguments);
        },

        send_payment_request: function () {
            this._super.apply(this, arguments);
            return this._vevent_payment_terminal_pay();
        },

        send_payment_cancel: function () {
            this._super.apply(this, arguments);
            this._show_error(
                _t(
                    "Utilice la terminal para cancelar la orden."
                )
            );
            return Promise.reject();
        },

        _vevent_payment_terminal_pay: async function () {
            var order = this.pos.get_order();
            var pay_line = order.selected_paymentline;

            var currency = this.pos.currency;
            
            var data = {
                amount: pay_line.amount,
                currency_iso: currency.name,
                currency_decimals: currency.decimals,
                payment_mode: this.payment_method.vevent_payment_terminal_mode,
                payment_id: pay_line.cid,
                order_id: order.name,
            };
            if (this.payment_method.vevent_payment_terminal_id) {
                data.terminal_id = this.payment_method.vevent_payment_terminal_id;
            }
            
            //pay_line.set_payment_status("done");
            pay_line.transaction_id = Date.now();
            pay_line.card_type = 'Vevent';
                      
            var currentMessages = await rpc.query({
                model: 'pos.vevent.message',
                method: 'search',
                args: [[["pos_name", "=", order.pos.config.name]]]
            })

            await rpc.query({
                model: 'pos.vevent.message',
                method: 'unlink',
                args: [currentMessages]
            })

            var newMessage = await rpc.query({
                model: 'pos.vevent.message',
                method: 'create',
                args: [{
                    "session_id": order.pos.pos_session.id,
                    "pos_name": order.pos.config.name,
                    "json_request": order.uid + "\nPaciente: " + order.partner.name + "\nCama: " + order.x_cama + "\nAmbulancia: " + order.x_no_ambulancia + "\nTurno: " + order.x_turno, 
                    "transaction_id": pay_line.transaction_id }]
            })

            console.log(newMessage)

            pay_line.set_payment_status("waitingCard");
            
            return new Promise((resolve, reject) => {

                var timerId = setInterval(async () => {
                    var currentMessages = await rpc.query({
                        model: 'pos.vevent.message',
                        method: 'search_read',
                        args: [[
                            ["pos_name", "=", order.pos.config.name],
                            ["transaction_id", "=", pay_line.transaction_id],
                            ["json_response", "<>", null]
                            ]]
                    })
                    if (currentMessages.length > 0)
                    {
                        clearInterval(timerId);
                        console.log(currentMessages[0])
                        var data = JSON.parse(currentMessages[0].json_response)
                        if(data.Success){
                            order.x_solicitante = { "id" : data.Contact.id }
                            pay_line.set_receipt_info(
                                "Recibido por: " + data.Contact.name + 
                                "\nPaciente: " + order.partner.name + 
                                "\nCama: " + order.x_cama + 
                                "\nAmbulancia: " + order.x_no_ambulancia + 
                                "\nTurno: " + order.x_turno)
                            pay_line.cardholder_name = data.Contact.name;
                            pay_line.set_payment_status("done");
                            resolve(true);    
                        }
                        else {
                            resolve(false);
                        }                        
                    }
                    console.log("tick")
                }, 1000)

            })

            

            return Promise.resolve(false);
            //return Promise.resolve(true);
            
            return this._vevent_payment_terminal_proxy_request(data).then((response) => {
                if (response === false) {
                    this._show_error(
                        _t(
                            "Failed to send the amount to pay to the payment terminal. Press the red button on the payment terminal and try again."
                        )
                    );
                    // There was an error, let the user retry.
                    return false;
                } else if (response instanceof Object && "transaction_id" in response) {
                    // The response has a terminal transaction identifier:
                    // return a promise that polls for transaction status.
                    pay_line.set_payment_status("waitingCard");
                    this._vevent_update_payment_line_terminal_transaction_status(
                        pay_line,
                        response
                    );
                    return new Promise((resolve, reject) => {
                        this._vevent_poll_for_transaction_status(
                            pay_line,
                            resolve,
                            reject
                        );
                    });
                }

                // The transaction was started, but the terminal driver
                // does not report status, so we won't know the
                // transaction result: we let the user enter the
                // outcome manually. This is done by rejecting the
                // promise as explained in the send_payment_request()
                // documentation.
                pay_line.set_payment_status("force_done");
                return Promise.reject();
            });
        },

        // _poll: function(pay_line) {

        // }

        _vevent_poll_for_transaction_status: function (pay_line, resolve, reject) {
            var timerId = setInterval(() => {
                // Query the driver status more frequently than the regular POS
                // proxy, to get faster feedback when the transaction is
                // complete on the terminal.
                var status_params = {};
                if (this.payment_method.vevent_payment_terminal_id) {
                    status_params.terminal_id =
                        this.payment_method.vevent_payment_terminal_id;
                }
                this.pos.env.proxy.connection
                    .rpc("/hw_proxy/status_json", status_params, {
                        shadow: true,
                        timeout: 1000,
                    })
                    .then((drivers_status) => {
                        for (var driver_name in drivers_status) {
                            // Look for a driver that is a payment terminal and has
                            // transactions.
                            var driver = drivers_status[driver_name];
                            if (!driver.is_terminal || !("transactions" in driver)) {
                                continue;
                            }
                            for (var transaction_id in driver.transactions) {
                                var transaction = driver.transactions[transaction_id];
                                if (
                                    transaction.transaction_id ===
                                    pay_line.terminal_transaction_id
                                ) {
                                    // Look for the transaction corresponding to
                                    // the payment line.
                                    this._vevent_update_payment_line_terminal_transaction_status(
                                        pay_line,
                                        transaction
                                    );
                                    if (
                                        pay_line.terminal_transaction_success !== null
                                    ) {
                                        resolve(pay_line.terminal_transaction_success);
                                        // Stop the loop
                                        clearInterval(timerId);
                                    }
                                }
                            }
                        }
                    })
                    .catch(() => {
                        console.error("Error querying terminal driver status");
                        // We could not query the transaction status so we
                        // won't know the transaction result: we let the user
                        // enter the outcome manually. This is done by
                        // rejecting the promise as explained in the
                        // send_payment_request() documentation.
                        pay_line.set_payment_status("force_done");
                        reject();
                        // Stop the loop
                        clearInterval(timerId);
                    });
            }, 1000);
        },

        _vevent_update_payment_line_terminal_transaction_status: function (
            pay_line,
            order
        ) {
            pay_line.terminal_transaction_id = Date.now();
            pay_line.terminal_transaction_success = true;
            pay_line.terminal_transaction_status = 'Chido';
            pay_line.set_payment_status("done");
            
            //pay_line.terminal_transaction_status_details = transaction.status_details;
            // Payment transaction reference, for accounting reconciliation purposes.
            //pay_line.transaction_id = transaction.reference;
        },

        _vevent_payment_terminal_proxy_request: function (data) {
            return this.pos.env.proxy
                .message("payment_terminal_transaction_start", {
                    payment_info: JSON.stringify(data),
                })
                .then((response) => {
                    return response;
                })
                .catch(() => {
                    console.error("Error starting payment transaction");
                    return false;
                });
        },

        _show_error: function (msg, title) {
            Gui.showPopup("ErrorPopup", {
                title: title || _t("Payment Terminal Error"),
                body: msg,
            });
        },
    });
    return VeventPaymentTerminal;
});
