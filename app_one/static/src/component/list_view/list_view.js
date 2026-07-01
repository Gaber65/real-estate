/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class ListView extends Component {

    static template = "app_one.ListView";

    setup() {
        this.state = useState({
            records: [],
            isRecordsLoaded: false
        });
        this.allRecords = [];

        this.orm = useService("orm");
        this.loadRecords();
    }

    async loadRecords() {
        await this.orm.searchRead('property', [], [])
            .then((records) => {
                this.state.records = records;
                this.allRecords = records;
            });
    }

    onSearch(ev) {
    const searchValue = ev.target.value.toLowerCase();

    if (!searchValue) {
        this.state.records = [...this.allRecords];
        return;
    }

    this.state.records = this.allRecords.filter(record =>
        Object.values(record).some(value =>
            String(value).toLowerCase().includes(searchValue)
        )
    );
}

}

registry.category("actions").add(
    "app_one.action_list_view",
    ListView
);
