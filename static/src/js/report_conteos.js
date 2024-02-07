import { ListController} from "@web/views/list/list_controller";
import { registry} from "@web/core/registry";
import { listView} from "@web/views/list/list_view";
export class SaleListController extends List Controller {
    setup() {
        super.setup();
    }
    On TestClick() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'test.wizard',
            name: 'Open Wizard',
            view mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: false,
        });
    }
}
registry.category("views").add("boton_imprimir_conteos", {
    ...listView,
    Controller: SaleListController,
    buttonTemplate: "boton_imprimir_conteos.ListView.Buttons",
});
