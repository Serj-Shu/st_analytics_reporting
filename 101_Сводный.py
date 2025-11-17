import streamlit as st
import modules as m
import datetime
import streamlit.components.v1 as components
import pandas as pd
import json

pd.options.display.max_colwidth = 200

report = 'pivot_metrics'
m.report_name('Сводный')
m.init_report(report)
if m.user_allowed(report):
    tab_pivot_shops, tab_pivot_shops_brands = st.tabs(["Магазины", "Коммерция"])
    with tab_pivot_shops:
        metric_class = m.invoke_metric()
        report_months_dict = m.create_date_dict('2024-01')
        column1, column2 = st.columns([1, 6])
        with column1:
            selected_month = st.selectbox('Месяц', reversed(list(report_months_dict.keys())))
        st.write('Из показателей исключен опт и специальные категории.')
        with st.spinner('Считаем показатели...'):
            filters = ""
            if selected_month:
                filters = filters + f"and ReportMonth='{report_months_dict[selected_month]}'"
            df = m.connect_and_show(report, 'pivot_shops', filters, 'devs')
            df['ProcessedValue'] = df.apply(lambda x: x['Value'][0] if x['ColumnName'] != 'История' else x['Value'],
                                            axis=1)
            pivot_df = df.pivot_table(index='Показатель', columns='ColumnName', values='ProcessedValue', aggfunc='first')
            pivot_df = pivot_df.convert_dtypes()
            # Упорядочивание столбцов
            columns_order = df['ColumnName'].unique()
            pivot_df = pivot_df[columns_order]
            # Упорядочивание показателей
            metrics_order = [metric_class.get_metric(x, False)['name'] for x in metric_class.metrics_order.keys()]
            pivot_df = pivot_df.reindex(metrics_order)
            df_column_config = {
                "История": st.column_config.LineChartColumn(
                    "По дням", y_min=0
                )
            }
            m.format_df(pivot_df, df_column_config, 800)

    with tab_pivot_shops_brands:
        report_years = []
        start_year = 2023

        while start_year <= datetime.datetime.now().year:
            report_years.append(start_year)
            start_year = start_year + 1

        column1, column2 = st.columns([1, 6])
        with column1:
            selected_year = st.selectbox('Год', reversed(report_years))
        st.write('Из показателей исключены специальные категории.')
        filters = str(selected_year)
        df = m.connect_and_show(report, 'pivot_commerce_yoy', filters, 'devs')
        data = df.copy()
        data["Выручка (текущий год), млрд руб."] = (data["Выручка (текущий год), руб."] / 1_000_000_000).round(1)
        data["Выручка (предыдущий год), млрд руб."] = (data["Выручка (предыдущий год), руб."] / 1_000_000_000).round(1)
        data["Выручка (офлайн), млрд руб."] = (data["Выручка (офлайн), руб."] / 1_000_000_000).round(1)
        data["Выручка (онлайн), млрд руб."] = (data["Выручка (онлайн), руб."] / 1_000_000_000).round(1)
        data["Выручка (опт), млн руб."] = (data["Выручка (опт), руб."] / 1_000_000).round(1)
        with st.container(border=True):
            st.subheader('Основные показатели')
            metrics_data = data.loc[data['Месяц'] == 'Итого']
            metric1, metric2, metric3, metric4, metric5, metric6, metric7, metric8 = st.columns([1, 1, 1, 1, 1, 1, 1, 1])
            with metric1:
                st.metric('Выручка, млрд руб.', metrics_data["Выручка (текущий год), млрд руб."], '{:.1%}'.format(metrics_data["Изменение выручки YoY, %"][0]/100))
            with metric2:
                st.metric('Маржа', '{:.1%}'.format(metrics_data["Маржа (текущий год), %"][0]/100), '{:.1%}'.format(metrics_data["Изменение маржи, пп."][0]/100))
            with metric3:
                st.metric('Рост LFL YoY', '{:.1%}'.format(metrics_data["Изменение выручки YoY (LfL), %"][0]/100))
            with metric4:
                st.metric('Доля онлайн', '{:.1%}'.format(metrics_data["Доля (онлайн), %"][0]/100))
            with metric5:
                st.metric('Рост онлайн YoY', '{:.1%}'.format(metrics_data["Изменение выручки (онлайн) YoY, %"][0]/100))
            with metric6:
                st.metric('Выручка (офлайн), млрд руб.', metrics_data["Выручка (офлайн), млрд руб."][0])
            with metric7:
                st.metric('Выручка (онлайн), млрд руб.', metrics_data["Выручка (онлайн), млрд руб."][0])
            with metric8:
                st.metric('Выручка (опт), млн руб.', metrics_data["Выручка (опт), млн руб."][0])
        # Построение таблицы
        numbers_columns = ["Выручка (текущий год), руб.", "Выручка (предыдущий год), руб.", "Выручка (офлайн), руб.", "Выручка (онлайн), руб.", "Выручка (опт), руб."]
        pinned_columns = ['Год', 'Месяц']
        with_totals = True
        m.pretty_df(df, numbers_columns, pinned_columns, with_totals)
        st.info('Таблицу можно выгрузить в Excel, нажав на любую ячейку и выбрав Export ► Excel Export. ')

        # Hierarchy metrics (start)
        st.divider()
        with st.expander('🌳 Иерархия показателей'):
            st.subheader('Иерархия показателей')
            st.info('Из показателей исключен опт.')
            hierarchy_column1, hierarchy_column2 = st.columns([1, 6])
            with hierarchy_column1:
                filters_text = ''
                months_dict = m.get_months()
                hierarchy_months = list(months_dict.keys())
                hierarchy_selected_month = st.selectbox(f'Месяц сравнения {selected_year}/{selected_year-1}', hierarchy_months)
                if hierarchy_selected_month:
                    filters_text = filters_text + f"and MonthNum='{months_dict[hierarchy_selected_month]}'"
            shop_level = st.toggle('По магазинам')

            try:
                with st.spinner('Построение дерева показателей...'):
                    filters_text = filters_text + f"and ReportYear in ('{selected_year}', '{selected_year - 1}')"
                    hierarchy_metrics = ['10005', '10024', '10022']
                    hierarchy_metrics_ids = ",".join(hierarchy_metrics)
                    hierarchy_depth = {
                        1: "СЕТЬ",
                        2: "Country",
                        3: "SaleChannel",
                        4: "ShopName"
                    }
                    hierarchy_depth_max = list(hierarchy_depth.keys())[-1]
                    hierarchy_filters = {'@metrics': hierarchy_metrics_ids, '@filters': filters_text, '@year': str(selected_year)}
                    df = m.connect_and_show(report, 'commerce_metrics_tree', hierarchy_filters, 'devs')
                    children_count = 0

                    # СЕТЬ
                    data_df = df.loc[df['HierarchyDepth'] == 1]
                    result = {
                        "name": hierarchy_depth[1]
                    }
                    metrics = []
                    values = []
                    children = []
                    for metric in hierarchy_metrics:
                        metric_data = data_df.loc[data_df['MetricId'] == int(metric)].reset_index()
                        metrics.append(metric_data['Metric'][0])
                        metrics.append('YoY')
                        values.append(metric_data['CurrentYearValue'][0])
                        values.append(metric_data['YoY'][0])
                    result['metrics'] = metrics
                    result['value'] = values
                    result['children'] = children

                    # СТРАНА
                    data_df = df.loc[df['HierarchyDepth'] == 2]
                    countries = data_df['Country'].unique()
                    children = []
                    for country in countries:
                        country_object = {"name": country, "value": []}
                        for metric in hierarchy_metrics:
                            metric_data = data_df.loc[data_df['MetricId'] == int(metric)].reset_index()
                            metric_data = metric_data.loc[metric_data['Country'] == country].reset_index()
                            country_object['value'].append(metric_data['CurrentYearValue'][0])
                            country_object['value'].append(metric_data['YoY'][0])
                        children.append(country_object)
                        children_count = children_count + 1
                    result['children'] = children

                    # КАНАЛ ПРОДАЖ
                    data_df = df.loc[df['HierarchyDepth'] == 3]
                    country_children = []
                    for country in result['children']:
                        country_df = data_df.loc[data_df['Country'] == country['name']].reset_index()
                        sale_channels = country_df['SaleChannel'].unique()
                        children = []
                        for sale_channel in sale_channels:
                            sale_channel_object = {"name": sale_channel, "value": []}
                            for metric in hierarchy_metrics:
                                metric_data = country_df.loc[country_df['MetricId'] == int(metric)].reset_index(drop=True)
                                metric_data = metric_data.loc[metric_data['SaleChannel'] == sale_channel].reset_index()
                                sale_channel_object['value'].append(metric_data['CurrentYearValue'][0])
                                sale_channel_object['value'].append(metric_data['YoY'][0])
                            children.append(sale_channel_object)
                            children_count = children_count + 1
                        country['children'] = children
                        country_children.append(country)
                    result['children'] = country_children

                    # МАГАЗИН
                    if shop_level:
                        data_df = df.loc[df['HierarchyDepth'] == 4]
                        data_df = data_df.loc[data_df['SaleChannel'] == 'Офлайн']
                        net_children = []
                        for country in result['children']:
                            country_df = data_df.loc[data_df['Country'] == country['name']].reset_index()
                            country_children = []
                            for sale_channel in country['children']:
                                sale_channel_children = []
                                if sale_channel['name'] == 'Офлайн':
                                    shops = country_df['ShopName'].unique()
                                    for shop in shops:
                                        shop_object = {"name": shop, "value": []}
                                        for metric in hierarchy_metrics:
                                            metric_data = country_df.loc[country_df['MetricId'] == int(metric)].reset_index(drop=True)
                                            metric_data = metric_data.loc[metric_data['ShopName'] == shop].reset_index()
                                            shop_object['value'].append(metric_data['CurrentYearValue'][0])
                                            shop_object['value'].append(metric_data['YoY'][0])
                                        sale_channel_children.append(shop_object)
                                        children_count = children_count + 1
                                sale_channel['children'] = sale_channel_children
                                country_children.append(sale_channel)
                            country['children'] = country_children
                            net_children.append(country)
                        result['children'] = net_children

                    # Чтение HTML-шаблона
                    with open("./addons/commerce_metrics_tree.html", "r", encoding="utf-8") as f:
                        html_template = f.read()

                    html_content = html_template.replace("{{ data|tojson }}", json.dumps(result))

                    # Отображение HTML в Streamlit
                    components.html(html_content, height=children_count * 36, scrolling=True)
            except Exception:
                st.warning('Ошибка загрузки данных. Если ошибка регулярно повторяется - обратитесь, пожалуйста, к разработчикам.')
        # Hierarchy metrics (end)

        with st.expander('📈 Динамика показателей'):
            st.subheader('Динамика показателей')
            # Построение графика с выручкой
            data_proceeds = data.loc[data['Месяц'] != 'Итого', ["Месяц", "Выручка (текущий год), млрд руб.", "Выручка (предыдущий год), млрд руб."]]
            title = 'Выручка за предыдущий и текущий год по месяцам, млрд руб.'
            m.simple_altair_line_chart(data_proceeds, title, ["Выручка (текущий год), млрд руб.", "Выручка (предыдущий год), млрд руб."])

            # Построение графика с выручкой YoY
            data_proceeds_yoy = data.loc[data['Месяц'] != 'Итого', ["Месяц", "Изменение выручки YoY, %"]]
            title = 'Рост выручки к предыдущему году, %'
            m.simple_altair_line_chart(data_proceeds_yoy, title, ["Изменение выручки YoY, %"])

            # Построение графика с выручкой YoY
            data_ecom_partition = data.loc[data['Месяц'] != 'Итого', ["Месяц", "Доля (онлайн), %", "Изменение выручки (онлайн) YoY, %"]]
            title = 'Доля (онлайн), %'
            m.simple_altair_line_chart(data_ecom_partition, title, ["Доля (онлайн), %", "Изменение выручки (онлайн) YoY, %"])
