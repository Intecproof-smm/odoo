odoo.define('pos_product_by_lot_number.EditListPopup', function (require) {
    'use strict';
    const rpc = require('web.rpc');
    const Registries = require('point_of_sale.Registries');
    const EditListPopup = require('point_of_sale.EditListPopup');
    var Qweb = require('web.core').qweb;
    var SuperConfirm = EditListPopup.prototype.confirm;
    const { onMounted}  = owl;

  
    const PosEditListPopup = (EditListPopup) =>
        class extends EditListPopup {
            setup() {
                super.setup();
			    onMounted(this.onMounted);
            }
            onMounted(){
                var self = this;
                self.index = -1;
                $('.popup').on('focus', '.list-line-input', function (event) {
                    const product = self.props.product;
                    var currentElement = $(event.currentTarget);
                    $(event.currentTarget).removeClass('wk-error');
                    $('.duplicate-serial').hide();
                    var lot_name = currentElement.val()
                    if(product)
                        self.render_lot_holder(event, product, lot_name, currentElement);
                });
                $('.popup').on('keyup', '.list-line-input', function (event) {
                    const product = self.props.product;
                    var currentElement = $(event.currentTarget);
                    var lot_name = ""
                    if (event)
                        lot_name = currentElement.val()
                    if(product){
                        self.render_lot_holder(event, product, lot_name, currentElement);
                    }
                })
            }
            async confirm(){
                this.on_click_confirm(this.props.product);
            }
			on_click_confirm(product){
				var self = this;
				this.validate_lots(product);
                    setTimeout(function(){
                        var has_error = false;
                        $('.list-line-input').each(function(index,el){
                            if($(el).hasClass('wk-error'))
                            has_error = true;
                        });
                        var selection = $('.select-input option:selected').val();
                    if(!has_error){
                        SuperConfirm.call(self);
                    }
                    else if(has_error && selection == 'yes'){
                        SuperConfirm.call(self);
                        // super.confirm();
                    }
                },500)
			}
			async validate_lots(product){
				var self = this;
				var count = 0;
                var lot_inputs = {};
                var wrong_elements = [];
                $('.list-line-input').removeClass('wk-error');
                $('.duplicate-serial').hide();
                $('.error-message').hide();
				$('.list-line-input').each(function(index,ev){
					var lot_name = $(ev).val();
                    if(product && product.tracking == 'serial')
                        if(Object.keys(lot_inputs).indexOf(lot_name) == -1)
                            lot_inputs[lot_name] = 1;
                        else
                            lot_inputs[lot_name]++;
                    this.has_error = false;
					if(product && self.env.pos.db.lot_no[lot_name] && self.env.pos.db.lot_no[lot_name].product_id[0] == product.id){
                        this.has_error = true;
                        // count++
                    }
					else{
                        rpc.query({
                            model: 'stock.lot',
							method: 'check_lot_by_rpc',
							args: [{
                                'name': lot_name,
                                'product_id': product.id
							}]
						})
						.then(function(result) {
							if(result){
                                // count++;
							}
							else{
								$(ev).addClass('wk-error');
                                wrong_elements.push($(ev))
							}
						}).catch(function(e){
                            if(this.has_error)
                                $(ev).addClass('wk-error');
                        });
					}
                });
                var is_duplicate = false;
                var duplicate = Object.values(lot_inputs).filter(e => e > 1);
                if(duplicate.length)
                    // setTimeout(function(){
                    _.each(wrong_elements,function(ele){
                        ele.addClass('wk-error')
                    })
                    // },1000);
                    // $('.list-line-input').removeClass('wk-error');
                
                if(product && product.tracking == 'serial')
                _.each(lot_inputs,function(index,val){
                    if(lot_inputs[val] > 1){
                        is_duplicate = true;
                        $('.list-line-input').each(function(i,e){
                            if($(e).val() == val)
                            $(e).addClass('wk-error');
                        }); 
                    }
                })
                setTimeout(function(){
                    var has_error = false;
                    $('.list-line-input').each(function(index,el){
                        if($(el).hasClass('wk-error'))
                        has_error = true;
                    });
                if(!is_duplicate && has_error){
                    $('.duplicate-serial').hide();
                    $('.error-message').show();
                }
                else if(is_duplicate && has_error){
                    $('.duplicate-serial').show();
                    $('.error-message').hide();
                }
                else{
                    $('.duplicate-serial').hide();
                    $('.error-message').hide();
                }
            },1000);
			}
           
            render_lot_holder(event, product, lot_name, currentElement) {
                var self = this;
                var product_lot = {};
                var all_lots = self.env.pos.db.product_by_id_lot_no[product.id];
                _.each(all_lots, function (lot) {
                    var lot_data = self.env.pos.db.lot_no[lot]
                    var count = 0;
                    count += self.env.pos.get_order().product_total_by_lot(lot.name);
                    if (lot_data.product_qty > count) {
                        let lot_name = lot_data.name;
                        product_lot[lot_name] = lot_data;
                    }
                });

                $('.list-line-input').each(function (index, el) {
                    var text = $(el).val();
                    if ($(el) != currentElement)
                        if (Object.keys(product_lot).indexOf(text) != -1)
                            delete product_lot[text];
                })
                var lot_holder = Qweb.render('LotHolder', {});
                var updown_press;
                $('.selection-lot').remove();
                currentElement.siblings().after(lot_holder);
                self.parent = $('.lot-holder');
                currentElement.parent(1).find('.lot-holder ul').empty();
                if (lot_name != '') {
                    lot_name = new RegExp(lot_name.replace(/[^0-9a-z_]/i), 'i');

                    
                    for (var index in product_lot) {
                        if (product_lot[index].name.match(lot_name)) {
                            currentElement.parent(1).find('.lot-holder ul').append($("<li><span class='lot-name'>" + product_lot[index].name + "</span></li>"));
                        }
                    }
                } else {
                    for (var index in product_lot) {
                        currentElement.parent(1).find('.lot-holder ul').append($("<li><span class='lot-name'>" + product_lot[index].name + "</span></li>"));
                    }
                }
                currentElement.parent(1).find('.lot-holder, .lot-holder ul').show();

                // *************For movement in lot holder********************
                if(event && event.which == 38){
                    // Up arrow
                    self.index--;
                    var len = $('.lot-holder li').length;
                    if(self.index < 0)
                        self.index = len-1;
                    self.parent.scrollTop(36*self.index);
                    updown_press = true;
                }else if(event && event.which == 40){
                    // Down arrow
                    self.index++;
                    if(self.index > $('.lot-holder li').length - 1)
                        self.index = 0;
                    self.parent.scrollTop(36*self.index);
                       updown_press = true;
                }
                if(event && event.which == 27){
                    // Esc key
                    $('.lot-holder ul').hide();
                }else if(event && event.which == 13 && self.index >=0 && $('.lot-holder li').eq(self.index)[0]){
                    var selcted_li_quote_id = $('.lot-holder li').eq(self.index)[0].innerText;
                    currentElement.val(selcted_li_quote_id);
                    currentElement.keyup();
                    var ele;
                    $('.list-line-input').each(function(index,el){
                        if($(el).index() == currentElement.index()){
                            ele = index
                        }
                    })
                    var count = 0;
                    _.each(self.state.array,function(state){
                        if(ele == count)
                        state.text = selcted_li_quote_id;
                        count++;
                    })
                    $('.lot-holder').hide();
                    self.index = -1;
                }
                $('.lot-holder ').on('click','li', function(event) {
                var lot_name = $(event.currentTarget).text();
                    currentElement.val(lot_name)
                    $('.selection-lot').hide();
                    if(currentElement.length)
                        currentElement.focus();
                    else
                        $('.list-line-input').focus();
                        var ele;
                    $('.list-line-input').each(function(index,el){
                        if($(el).index() == currentElement.index()){
                            ele = index
                        }
                    })
                    var count = 0;
                    _.each(self.state.array,function(state){
                        if(ele == count)
                        state.text = lot_name;
                        count++;
                    })
                });
                if (updown_press) {

                    $('.lot-holder li.active').removeClass('active');
                    $('.lot-holder li').eq(self.index).addClass('active');
                    $('.lot-holder li.active').select();
                }
                if (event && event.which == 27) {
                    // Esc key
                    $('.lot-holder ul').hide();
                }
            }
        }
    Registries.Component.extend(EditListPopup, PosEditListPopup);
    return EditListPopup;

});