import streamlit as st
import modules as m
import request_tools

# report = 'dicts'
m.report_name('Справочники')

st.write('Раздел НСИ')
# simple_multiselect(report, filter_name, filter_df, field_to_select, field_to_filter, dependence_field=None):
# m.simple_multiselect(report, 'Группа', item_group, 'ItemGroup', 'ItemGroup')
item_group = request_tools.get_dict('item_group')
dictionaries = {
    'Магазины': {'report': 'shops', 'description': 'Справочник магазинов', 'pin_columns': ['Объединение']}
    , 'Товары': {'report': 'items', 'description': 'Номенклатурный справочник'
                 , 'filters': [
            {"filter": m.country, "use_report": True, "args": {}}
            , {"filter": m.items_input, "use_report": True, "args": {}}
            , {"filter": m.brands, "use_report": True, "args": {}}
            , {"filter": m.items_categories, "use_report": True, "args": {}}
            , {"filter": m.simple_multiselect, "use_report": True, "args": {"filter_name": "Группа", "filter_df": item_group, "field_to_select": "ItemGroup", "field_to_filter": "ItemGroup"}}
        ]
                 }
    , 'Центральный': {'report': 'handle', 'description': 'Центральный справочник синхронизации систем'}
}
selected_dictionary = st.pills('Доступные справочники', dictionaries.keys())

if selected_dictionary is not None:
    dictionary = dictionaries[selected_dictionary]
    report = dictionary['report']
    m.init_report(report)
    if 'filters' in dictionary:
        report_state = st.session_state['reports'][report]
        report_state['metrics'] = ['default']
        filter_column1, filter_column2 = st.columns([1, 4])
        with filter_column1:
            for filter in dictionary['filters']:
                args = {'report': report} | filter['args']
                if filter['use_report']:
                    args = {'report': report} | filter['args']
                else:
                    args = filter['args']
                filter['filter'](**args)
        with filter_column2:
            m.excel_loader(report, 'devs')
    else:
        filters = ''
        df = m.connect_and_show(report, dictionary['report'], filters, 'prod')
        if 'pin_columns' in dictionary:
            pin_columns = dictionary['pin_columns']
        else:
            pin_columns = []
        st.subheader(dictionary['description'])
        m.pretty_df(df, df.columns, pin_columns, filterable=True)
