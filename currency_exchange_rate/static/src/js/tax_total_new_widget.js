/** @odoo-module alias=currency_exchange_rate.tax_group_owl **/
"use strict";

const { Component } = owl;
const { useState, useRef } = owl.hooks;
import session from 'web.session';
import AbstractFieldOwl from 'web.AbstractFieldOwl';
import fieldUtils from 'web.field_utils';
import field_registry from 'web.field_registry_owl';


class ExchangeTaxGroupComponent extends Component {
    constructor(parent, props) {
        super(parent, props);
        this.inputTax = useRef('taxValueInput');
        this.state = useState({ value: 'readonly' });
        this.allowTaxEdition = this.__owl__.parent.mode === 'edit' ? props.allowTaxEdition : false;
    }

    willUpdateProps(nextProps) {
        this.setState('readonly');
    }

    patched() {
        if (this.state.value === 'edit') {
            let newValue = this.props.taxGroup.tax_group_amount;
            let currency = session.get_currency(this.props.record.data.currency_id.data.id);

            newValue = fieldUtils.format.float(newValue, null, { digits: currency.digits });
            this.inputTax.el.focus();
            this.inputTax.el.value = newValue;
        }
    }

    setState(value) {
        if (['readonly', 'edit', 'disable'].includes(value)) {
            this.state.value = value;
        } else {
            this.state.value = 'readonly';
        }
    }

    _onChangeTaxValue() {
        this.setState('disable');
        let newValue = this.inputTax.el.value;
        let currency = session.get_currency(this.props.record.data.currency_id.data.id);
        try {
            newValue = fieldUtils.parse.float(newValue);
            newValue = fieldUtils.format.float(newValue, null, { digits: currency.digits });
            newValue = fieldUtils.parse.float(newValue);
        } catch (err) {
            $(this.inputTax.el).addClass('o_field_invalid');
            this.setState('edit');
            return;
        }
        if (newValue === this.props.taxGroup.tax_group_amount || newValue === 0) {
            this.setState('readonly');
            return;
        }
        this.props.taxGroup.tax_group_amount = newValue;
        this.trigger('change-tax-group', {
            oldValue: this.props.taxGroup.tax_group_amount,
            newValue: newValue,
            taxGroupId: this.props.taxGroup.tax_group_id
        });
    }
}
ExchangeTaxGroupComponent.props = ['taxGroup', 'allowTaxEdition', 'record'];
ExchangeTaxGroupComponent.template = 'currency_exchange_rate.ExchangeTaxGroupComponent';

class ExchangeTaxTotalsComponent extends AbstractFieldOwl {
    constructor(...args) {
        super(...args);
        this.totals = useState({ value: this.value ? JSON.parse(this.value) : null });
        this.allowTaxEdition = this.nodeOptions['allowTaxEdition'];
    }

    willUpdateProps(nextProps) {
        this.totals.value = JSON.parse(nextProps.record.data[this.props.fieldName]);
        console.log("willUpdateProps", this.totals.value);

    }

    _onKeydown(ev) {
        switch (ev.which) {
            case $.ui.keyCode.ENTER:
            case $.ui.keyCode.TAB:
                $(ev.target).blur();
        }
    }

    _onChangeTaxValueByTaxGroup(ev) {
        this.trigger('field-changed', {
            dataPointID: this.record.id,
            changes: { tax_totals_json: JSON.stringify(this.totals.value) }
        });
        console.log("_onChangeTaxValueByTaxGroup", this.totals.value);
    }
}
ExchangeTaxTotalsComponent.template = 'currency_exchange_rate.ExchangeTaxTotalsField';
ExchangeTaxTotalsComponent.components = { ExchangeTaxGroupComponent };

field_registry.add('account-exchange-tax-totals-field', ExchangeTaxTotalsComponent);

export default ExchangeTaxTotalsComponent;
