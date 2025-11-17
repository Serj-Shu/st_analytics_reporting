import streamlit as st
import modules as m
import request_tools

report = 'sales'
m.report_name('Продажи')
m.init_report(report)
if m.user_allowed(report):
    st.write('Данные доступны с 01.01.2022')
    with st.expander('🎥 Видеоинструкция', expanded=False):
        st.info('Выбирайте параметры выгрузки в Excel.')
        video_file = open(f".\\videos\\manual_sales_ru.webm", "rb")
        video_bytes = video_file.read()
        st.video(video_bytes)

    with st.expander("Свернуть/Развернуть фильтры", expanded=True):
        st.subheader('Фильтры')
        filters_column1, filters_column2, filters_column3, filters_column4 = st.columns([3, 3, 3, 3])

        with filters_column1:
            m.calendar(report, 'ReportDate')
            st.write('**Общие фильтры**')
            m.country(report)
            m.angle(report)
            m.company()
            m.manager()
            m.sale_channel()
            m.provider()

        with filters_column2:
            m.shops(report)
            st.write('**Товарная группа**')
            item_style = request_tools.get_dict('item_style')
            item_department = request_tools.get_dict('item_department')
            item_group = request_tools.get_dict('item_group')
            product_group = request_tools.get_dict('product_group')
            m.simple_multiselect(report, 'Состояние', item_style, 'ItemWasteState', 'ItemWasteStateIndex')
            m.simple_multiselect(report, 'Отдел', item_department, 'ItemDepartment', 'ItemDepartment')
            m.simple_multiselect(report, 'Группа', item_group, 'ItemGroup', 'ItemGroup')
            m.simple_multiselect(report, 'Вид', product_group, 'ProductGroupId', 'ProductGroupId')

        with filters_column3:
            m.brands(report)
            m.items_input(report)

        with filters_column4:
            m.items_categories(report)

    with st.expander("Свернуть/Развернуть настройки", expanded=True):
        st.subheader('Настройки')
        options_column1, options_column2, options_column3, options_column4, options_column5 = st.columns([3, 2, 2, 2, 3])

        with options_column1:
            st.write('**Опции**')
            currency = st.toggle('Конвертировать в валюту')
            m.filter_gift_flag(report)
            m.filter_wholesale_flag(report)
            m.filter_not_wholesale_flag(report)
            m.filter_entity_flag(report)
            m.simple_filter(report, 'filter_import_flag', 'ItemImportFlag', '1')
            m.simple_filter(report, 'filter_elite_flag', 'ItemEliteFlag', '1')
            m.simple_filter(report, 'filter_mass_flag', 'ItemEliteFlag', '0')
            m.simple_filter(report, 'filter_need_tester_flag', 'NeedTesterFlag', '1')
            m.simple_filter(report, 'filter_plastic_flag', 'ItemPlasticCardFlag', '1')
            m.filter_amount_of_check(report)
            m.filter_amount_of_check_with_filters(report)

        with options_column2:
            st.write('**Измерения 1**')
            m.dimension('Канал продаж', 'SaleChannel', report)
            m.dimension('Год', 'ReportYear', report)
            m.dimension('Месяц', 'ReportMonth', report)
            m.dimension('Неделя', 'ReportWeek', report)
            m.dimension('Дата', 'ReportDate', report)
            m.dimension('Час', 'ReportDateHour', report)
            m.dimension('Страна', 'Country', report)
            m.dimension('Город', 'City', report)
            m.dimension('Магазин', 'ShopName', report)
            m.dimension('Объединение', 'UnionId', report)
            m.dimension('Курс конвертации', 'ExchangeRate', report)
            st.divider()
            st.write('**Кросс-измерения**')
            st.caption('Кросс-измерения используют справочники, которые могут приводить к дублированию результата.')
            m.cross_dimension('Ракурс', 'RacursName', report)
            # st.write(st.session_state)

        with options_column3:
            st.write('**Измерения 2**')
            m.dimension('Код бренда', 'BrandId', report)
            m.dimension('Бренд', 'BrandName', report)
            m.dimension('Линейка товаров 1', 'BrandLine1', report)
            m.dimension('Код товара', 'ItemId', report)
            m.dimension('Товар', 'ItemName', report)
            m.dimension('Штрихкод продажи', 'ItemBarcode', report)
            m.dimension('Штрихкод основной', 'ItemDefaultBarcode', report)
            m.dimension('Артикул', 'ItemArticul', report)
            m.dimension('Аналитическая категория', 'AnalyticsCategory', report)
            m.dimension('Категория цены 1', 'PriceCategory1', report)
            m.dimension('Категория цены 2', 'PriceCategory2', report)
            m.dimension('Категория цены 3', 'PriceCategory3', report)
            m.dimension('Категория цены 4', 'PriceCategory4', report)
            m.dimension('Состояние', 'ItemWasteState', report)
            m.dimension('ЭлитМасс', 'MarketSegment', report)
            m.dimension('Отдел', 'ItemDepartment', report)
            m.dimension('Группа', 'ItemGroup', report)
            m.dimension('Вид', 'ProductGroupId', report)

        with options_column4:
            st.write('**Измерения 3**')
            m.dimension('ABC', 'ABC', report)
            m.dimension('Статус ассортимента', 'AssortmentStatus', report)
            m.dimension('Консультант (тип)', 'EmployeeType', report)
            m.dimension('Консультант (таб.номер)', 'EmployeeTableNumber', report)
            m.dimension('Консультант (ФИО)', 'EmployeeName', report)
            m.dimension('Клиент (CRM)', 'ClientIdCRM', report)
            m.dimension('Номер заказа', 'SalesId', report)
            m.dimension('Компенсация (компания)', 'CompensationGroupName', report)
            m.dimension('Компенсация (правило)', 'CompensationName', report)

        with options_column5:
            st.write('**Показатели**')
            metrics_class = m.invoke_metric()
            for metric in metrics_class.metrics.keys():
                metric_self = metrics_class.get_metric(metric, False)
                if report in metric_self['links']:
                    m.metric(metrics_class, metric, report, currency)

    with st.container(border=True):
        st.subheader('Аналитика')
        tab_constructor, tab_dynamics = st.tabs(["🏗️ Конструктор", "📊 Динамика"])
        with tab_constructor:
            st.subheader('Конструктор')
            st.write('**Выбранные фильтры**')
            selected_filters = ''
            for filter in st.session_state['reports'][report]['filters']:
                if filter['type'] == 'dates':
                    if len(filter['values']) == 1 or filter['values'][0] == filter['values'][1]:
                        selected_filters += f"Выбран день {filter['values'][0]}"
                    else:
                        selected_filters += f"Период с {filter['values'][0]} по {filter['values'][1]}"
                else:
                    selected_filters += f" / {filter['name']}"
            st.write(selected_filters)
            if m.get_global_filters_count() > 0:
                st.write('**Глобальные фильтры**')
                selected_global_filters = ''
                for global_filter in st.session_state['global_filters']:
                    if global_filter['is_set']:
                        selected_global_filters += f" / {global_filter['name']}"
                st.write(selected_global_filters)
            st.divider()
            m.excel_loader(report, 'devs')
            st.divider()
            m.show_sql(report)

        with tab_dynamics:
            st.subheader('Динамика')
            report_state = st.session_state['reports'][report]
            if len(report_state['selected_dates']) != 2:
                st.warning('Не выбран период')
                st.stop()
            st.write(f"Выбран период с {report_state['selected_dates'][0]} по {report_state['selected_dates'][1]}")
            if len(report_state['metrics']) == 0:
                st.warning('Не выбран показатель')
            else:
                metric_string = report_state['metrics'][0]
                dynamic_x_dict = {
                    "День": {"field": "ReportDate", "format": '%Y-%m-%d'}
                    , "Месяц": {"field": "ReportMonth", "format": '%Y-%m'}
                    , "Год": {"field": "ReportYear", "format": '%Y'}
                }
                m.draw_dynamic(report, dynamic_x_dict, 'sales', metric_string)


# debug
# st.write(st.session_state)
