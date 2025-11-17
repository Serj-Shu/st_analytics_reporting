import streamlit as st
import datetime
from dateutil.relativedelta import relativedelta
import request_tools
import queries
import config
import metrics
from clickhouse_driver import Client
from clickhouse_connect import get_client
import plotly.express as px
import time
import pg_manager
import json
import pandas as pd
import localization as l
import plotly.graph_objects as go
from st_aggrid import AgGrid, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import altair as alt


def check_time(func, report, user_login,  request):
    pg_connect = pg_manager.connect_to_pg()
    pg_q = pg_manager.PGQ(pg_connect)
    start_time = time.time()
    func()
    end_time = time.time()
    elapsed_seconds = end_time - start_time
    pg_q.save_request_log(report, user_login, request, elapsed_seconds)


def user_allowed(report):
    page = "user_allowed"
    localize = l.pages["modules"][page]
    if 'language' not in st.session_state:
        st.session_state["language"] = "EN"
    lang = st.session_state["language"]
    result = False
    if 'user' not in st.session_state:
        st.warning(localize["message_goto_start"][lang])
    elif not st.session_state['user']['logged_in']:
        st.warning(localize["message_not_logged"][lang])
    elif report not in st.session_state['current_user']['user_properties']['reports']:
        st.warning(localize["message_auth_failed"][lang])
    else:
        result = True
    return result


def init_report(name):
    st.session_state['reports'] = {
        name: {
            'filters': []
            , 'dimensions': []
            , 'cross_dimensions': []
            , 'metrics': []
        }
    }


def report_name(name):
    """
    Заголовок отчета и вкладки в браузере.
    :param name: Название отчета.
    :return: Объект title.
    """
    st.logo("images/reports_logo.png", size="large", icon_image="images/logo_icon.png")
    st.set_page_config(page_title=name, layout="wide", page_icon="./images/reports_icon.ico")
    custom_css = """
    <style>
        body {
            font-size: 14px;
        } 
        .stAppDeployButton {
            visibility: hidden;
        }
        footer {visibility: hidden;}
        div[style*="cursor: col-resize"] {
            display: none !important;
        }      
    </style>
    """
    # Применение пользовательского CSS
    st.markdown(custom_css, unsafe_allow_html=True)
    st.title(name)


def filter_gift_flag(report):
    page = "filter_gift_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'ItemSpecialCategoryFlag', "type": "list", "values": '0'})
    return result


def filter_not_wholesale_flag(report):
    page = "filter_not_wholesale_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'WholesaleFlag', "type": "list", "values": '0'})
    return result


def filter_wholesale_flag(report):
    page = "filter_wholesale_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'WholesaleFlag', "type": "list", "values": '1'})
    return result


def filter_net_flag(report):
    page = "filter_net_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'NetFlag', "type": "list", "values": '1'})
    return result


def filter_spec_flag(report):
    page = "filter_spec_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'SpecFlag', "type": "list", "values": '1'})
    return result


def filter_exception_brands_flag(report):
    page = "filter_exception_brands_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'ExceptionBrands', "type": "list", "values": '0'})
    return result


def filter_entity_flag(report):
    page = "filter_entity_flag"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": 'ClientEntityFlag', "type": "list", "values": '1'})
    return result


def filter_amount_of_check(report):
    min_filter_text = max_filter_text = ''
    min_filter_amount = st.toggle('Минимальная сумма чека', help='Оставить чеки, которые выше указанной суммы.')
    if min_filter_amount:
        from_value = st.number_input('От', 0, 1000000000, 0, 100)
        min_filter_text = f"AmountSaleTotal >= {from_value}"
    max_filter_amount = st.toggle('Максимальная сумма чека', help='Оставить чеки, которые ниже указанной суммы.')
    if max_filter_amount:
        to_value = st.number_input('До', 0, 1000000000, 0, 100)
        max_filter_text = f"AmountSaleTotal <= {to_value}"
    if min_filter_amount or max_filter_amount:
        amount_filter = " and ".join([x for x in [min_filter_text, max_filter_text] if x != ''])
        # date_filter = get_filter('ReportDate', report)
        # subquery = f"SELECT SaleNumber FROM flat.sales " \
        #            f"WHERE 1=1 AND ReportDate >= '{date_filter[0]}' AND ReportDate <= '{date_filter[1]}' " \
        #            f"GROUP BY SaleNumber HAVING 1=1 {amount_filter}"
        report_state = st.session_state['reports'][report]
        # report_state['filters'].append(
        #     {"name": 'SaleNumber', "type": "subquery", "values": subquery})
        report_state['filters'].append(
            {"name": 'AmountSaleTotal', "type": "string", "values": amount_filter})
        st.info('Сумма чеков не переводится в рубли, т.е. фильтр работает на локальной валюте.')


def filter_amount_of_check_with_filters(report):
    report_state = st.session_state['reports'][report]
    filter_amount = st.toggle('Сумма чека (с учетом фильтров)',
                              help='Позволяет выбрать чеки по определенной величине выручки с учетом фильтров (диапазоны включены).'
                                   '\nНапример: Вы выбрали в фильтрах бренд Х и указали сумму чека до 1000 УЕ (в локальной валюте).'
                                   '\nВ итоге вы получите фильтрацию всех показателей на чеки, в которых бренд Х был куплен в сумме до 1000 УЕ.'
                                   '\nТ.е. показатель "Количество чеков" с брендом Х, равен 10, а с фильтром "до 1000 УЕ" - 3.')
    if filter_amount:
        from_value = st.number_input('От', 0, 1000000000, 0, 100)
        to_value = st.number_input('До', 100, 1000000000, 1000, 100)
        report_filters = request_tools.get_filters(report_state['filters'])
        subquery = f"SELECT SaleNumber FROM flat.sales " \
                   f"WHERE 1=1 {report_filters} " \
                   f"GROUP BY SaleNumber HAVING Sum(AmountSale) " \
                   f"BETWEEN {from_value} AND {to_value}"
        report_state['filters'].append(
            {"name": 'SaleNumber', "type": "subquery", "values": subquery})
        st.info('Сумма чеков не переводится в рубли, т.е. фильтр работает на локальной валюте.')


def simple_filter(report, loc_page, field_to_filter, filter_value):
    page = loc_page
    lang = st.session_state["language"]
    localize = {"filter_title": {}, "filter_description": {}}
    if page in l.pages["modules"]:
        localize = l.pages["modules"][page]
    else:
        localize["filter_title"][lang] = 'NO TITLE!'
        localize["filter_description"][lang] = 'NO DESCRIPTION!'
    report_state = st.session_state['reports'][report]
    result = st.toggle(localize["filter_title"][lang],
                       help=localize["filter_description"][lang])
    if result:
        report_state['filters'].append(
            {"name": field_to_filter, "type": "list", "values": filter_value})
    return result


def metrics_list(report):
    """
    Список метрик.
    :param report: Текущий отчет.
    :return: Единичный выбор метрики.
    """
    st.write('**Показатели**')
    report_state = st.session_state['reports'][report]
    request_result = request_tools.get_dict('metrics')
    selected_metric = st.selectbox('Показатель', request_result, key='Metric')


def calendar(report, field, title=None, key=0):
    """
    Календарь с указанным в настройках диапазоном дат.
    :param report: Указание на отчет.
    :param field: Поле, которое отвечает за дату.
    :param title: Словарь локализации заголовка.
    :param key: Ключ календаря (если нужно больше одного календаря).
    :return: Объект date_input.
    """
    page = "calendar"
    localize = l.pages["modules"][page]
    lang = st.session_state["language"]
    if title is not None:
        st.write(f'**{title[lang]}**')
    else:
        st.write(f'**{localize["title"][lang]}**')
    report_state = st.session_state['reports'][report]
    min_date = datetime.date.today().replace(day=1) - relativedelta(months=36)
    min_date_default = datetime.date.today().replace(day=1) - relativedelta(months=1)
    max_date = datetime.date.today().replace(day=1) + relativedelta(months=12)
    start_current_month = datetime.date.today().replace(day=1)
    date_range = st.date_input(localize["period_title"][lang]
                                       , (min_date_default, max_date)
                                       , min_value=min_date
                                       , max_value=max_date
                                       , help=localize["period_description"][lang]
                               , key=key)
    if len(date_range) == 0:
        date_range = (datetime.date.today() - relativedelta(days=1),)
    report_state['selected_dates'] = date_range
    report_state['filters'].append(
        {"name": field, "type": "dates", "values": report_state['selected_dates']})


def create_date_dict(start_date_str):
    # Парсим начальную дату
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m")
    # Текущая дата
    current_date = datetime.datetime.now()
    # Словарь для хранения результатов
    result_dict = {}
    # Итерируем от начальной даты до текущей даты
    while start_date <= current_date:
        # Добавляем запись в словарь
        result_dict[start_date.strftime("%B %Y")] = start_date.strftime("%Y-%m")
        # Переходим к следующему месяцу
        if start_date.month == 12:
            start_date = start_date.replace(year=start_date.year + 1, month=1)
        else:
            start_date = start_date.replace(month=start_date.month + 1)
    return result_dict


def get_months():
    result = {
        "January": 1
        , "Febrary": 2
        , "March": 3
        , "April": 4
        , "May": 5
        , "June": 6
        , "July": 7
        , "August": 8
        , "September": 9
        , "October": 10
        , "November": 11
        , "December": 12
    }
    return result


def sale_channel():
    """
    Канал продаж.
    :return: Объект с выбором.
    """
    sale_channels = ["Все", "Онлайн", "Офлайн"]
    if 'SaleChannel' in st.session_state:
        saved_value = sale_channels.index(st.session_state['SaleChannel'])
        # print(saved_value)
    else:
        saved_value = 0
    selected_channel = st.selectbox('Канал продаж', sale_channels, key='SaleChannel', index=saved_value)
    if selected_channel == 'Все':
        update_global_filter("SaleChannel", "", 'Все', False, 0)
    else:
        filter_text = f" and SaleChannel in ('{selected_channel}')"
        index = sale_channels.index(st.session_state['SaleChannel'])
        update_global_filter("SaleChannel", filter_text, selected_channel, True, index)


def update_global_filter(filter_name, filter_value, saved_value, is_set, index):
    global_filters_list = st.session_state['global_filters']
    if len(global_filters_list) == 0:
        global_filters_list.append({"name": filter_name,
                                    "text": filter_value,
                                    "values": saved_value,
                                    "is_set": is_set,
                                    "index": index
                                    })
    else:
        global_filters_list = [x for x in global_filters_list if x['name'] != filter_name]
        global_filters_list.append({"name": filter_name,
                                    "text": filter_value,
                                    "values": saved_value,
                                    "is_set": is_set,
                                    "index": index
                                    })
    st.session_state['global_filters'] = global_filters_list


def get_global_filters_count():
    i = 0
    for global_filter in st.session_state['global_filters']:
        if global_filter['is_set']:
            i = i + 1
    return i


def get_global_filter(filter_name):
    for global_filter in st.session_state['global_filters']:
        if global_filter['name'] == filter_name and global_filter['is_set']:
            return {"response": True, "filter": global_filter}
    return {"response": False, "filter": None}


def get_user_filter(filter_name, origin_dataframe):
    user_filter = [x for x in st.session_state['current_user']['user_properties']['filters'] if filter_name in x]
    if len(user_filter) > 0:
        request_result = origin_dataframe.loc[origin_dataframe[filter_name].isin(json.loads(user_filter[0][filter_name]))]
        request_result = request_result.reset_index(drop=True)
    else:
        request_result = None
    return request_result


def get_filter(filter_name, report):
    report_state = st.session_state['reports'][report]
    for filter in report_state['filters']:
        if filter['name'] == filter_name:
            return filter['values']


def angle(report):
    report_state = st.session_state['reports'][report]
    request_result = request_tools.get_dict('racurses')
    user_filter = get_user_filter('RacursId', request_result)
    if user_filter is not None:
        request_result = user_filter
    # if 'RacursId' in st.session_state:
    #     saved_value = request_result[request_result['RacursId'] == st.session_state['RacursId']].index.item()
    # else:
    #     saved_value = 0
    # selected_angle = st.selectbox('Ракурс', request_result, key='RacursId', index=saved_value)
    selected_angle = st.multiselect('Ракурс', request_result, key='RacursId')
    if len(selected_angle) > 1:
        st.warning('Вы выбрали более 1 ракурса. Учтите, что номенклатура может повторяться в ракурсах.')
    if 'Все ракурсы' in selected_angle or selected_angle == []:
        update_global_filter("RacursId", "", 'Все ракурсы', False, 0)
    else:
        selected_countries = get_filter('Country', report)
        company_filter = "1=1"
        if selected_countries is not None:
            selected_companies = [x[1] for x in report_state['countries'].items() if x[0] in selected_countries]
            company_filter = "Company in ('"
            company_filter += "','".join(selected_companies) + "')"
        selected_angle = "'" + "','".join(selected_angle) + "'"
        filter_text = f" and (Company, ItemId) in (SELECT DISTINCT Company, ItemId FROM flat.angle WHERE " \
                      f"(Company, Ver) in (SELECT Company, max(Ver) as Ver FROM flat.angle GROUP BY Company)" \
                      f"and {company_filter} and RacursName in ({selected_angle}))"
        # index = request_result[request_result['RacursId'] == selected_angle].index.item()
        # update_global_filter("RacursId", filter_text, selected_angle, True, index)
        update_global_filter("RacursId", filter_text, selected_angle, True, 0)


def company():
    request_result = pd.DataFrame({'Company': ["Все области", "СНГ", "ME"]})
    request_dict = {
        "Все области": ""
        , "СНГ": ["ekb", "blr", "kaz"]
        , "ME": ["qat", "drc", "src"]
    }
    user_filter = get_user_filter('Company', request_result)
    if user_filter is not None:
        request_result = user_filter
    if 'Company' in st.session_state:
        saved_value = request_result[request_result['Company'] == st.session_state['Company']].index.item()
    else:
        saved_value = 0
    selected_company = st.selectbox('Область данных', request_result, key='Company', index=saved_value)
    if selected_company == 'Все области':
        update_global_filter("Company", "", 'Все области', False, 0)
    else:
        company_iter = '\',\''.join(request_dict[selected_company])
        filter_text = f" and Company in ('{company_iter}')"
        index = request_result[request_result['Company'] == selected_company].index.item()
        update_global_filter("Company", filter_text, selected_company, True, index)


def manager():
    request_result = request_tools.get_dict('managers')
    if 'ManagerName' in st.session_state:
        saved_value = request_result[request_result['ManagerName'] == st.session_state['ManagerName']].index.item()
    else:
        saved_value = 0
    selected_manager = st.selectbox('Менеджер', request_result, key='ManagerName', index=saved_value)
    if selected_manager == 'Все менеджеры':
        update_global_filter("ManagerName", "", 'Все ракурсы', False, 0)
    else:
        filter_text = f" and BrandId in (SELECT DISTINCT BrandId FROM flat.managers WHERE ManagerName = '{selected_manager}')"
        index = request_result[request_result['ManagerName'] == selected_manager].index.item()
        update_global_filter("ManagerName", filter_text, selected_manager, True, index)


def provider():
    request_result = request_tools.get_dict('providers')
    if 'ProviderId' in st.session_state:
        saved_value = request_result[request_result['ProviderId'] == st.session_state['ProviderId']].index.item()
    else:
        saved_value = 0
    selected_provider = st.selectbox('Поставщик', request_result, key='ProviderId', index=saved_value)
    if selected_provider == 'Все поставщики':
        update_global_filter("ProviderId", "", 'Все поставщики', False, 0)
    else:
        selected_provider_id = selected_provider.split(' - ')[0]
        filter_text = f" and (BrandId, UnionIndex) in (SELECT DISTINCT BrandId, arrayJoin(UnionId) as UnionId FROM flat.providers WHERE ProviderId = '{selected_provider_id}')"
        index = request_result[request_result['ProviderId'] == selected_provider].index.item()
        update_global_filter("ProviderId", filter_text, selected_provider, True, index)


def simple_multiselect(report, filter_name, filter_df, field_to_select, field_to_filter, dependence_field=None):
    report_state = st.session_state['reports'][report]
    if dependence_field is not None:
        dependence_values = request_tools.parse_filter(report_state['filters'], dependence_field)
        if dependence_values is not None:
            filter_df = filter_df.loc[filter_df[dependence_field].isin(dependence_values)]
    filter_list = st.multiselect(filter_name, filter_df)
    if len(filter_list) > 0:
        filter_values = filter_df.loc[filter_df[field_to_select].isin(filter_list)]
        report_state['filters'].append(
            {"name": field_to_filter, "type": "list", "values": filter_values[field_to_filter].tolist()})


def simple_selectbox(report, filter_name, filter_df, field_to_filter):
    report_state = st.session_state['reports'][report]
    filter_list = st.selectbox(filter_name, filter_df)
    if len(filter_list) > 0:
        report_state['filters'].append(
            {"name": field_to_filter, "type": "list", "values": filter_list})


def simple_input(report, filter_field, filter_name, filter_title, filter_placeholder):
    report_state = st.session_state['reports'][report]
    st.write(f'**{filter_name}**')
    input_list = st.text_input(filter_title, placeholder=filter_placeholder,
                                     help='Впишите одно или несколько значений (напр.: 101, 102 и т.д.).')
    if len(input_list) > 0:
        report_state['filters'].append(
            {"name": filter_field, "type": "list", "values": process_string(input_list)})


def country(report):
    report_state = st.session_state['reports'][report]
    countries = {
        'Россия': 'ekb'
        , 'Беларусь': 'blr'
        , 'Казахстан': 'kaz'
        , 'Qatar': 'qat'
        , 'UAE': 'drc'
        , 'SA': 'src'
    }
    report_state['countries'] = countries
    country_select = st.multiselect('Страна', countries)
    if country_select:
        report_state['filters'].append(
            {"name": 'Country', "type": "list", "values": country_select})


def company_entity(report):
    report_state = st.session_state['reports'][report]
    companies = {
        'EKB': 'ekb'
        , 'BLR': 'blr'
        , 'KAZ': 'kaz'
        , 'QAT': 'qat'
        , 'DRC': 'drc'
        , 'SA': 'src'
        , 'DPC': 'dpc'
        , 'DDC': 'ddc'
        , 'WSBL': 'wsbl'
        , 'IPP': 'ipp'
        , 'GGR': 'ggr'
    }
    report_state['companies'] = companies
    country_select = st.multiselect('Юрлицо', companies)
    if country_select:
        country_select = [x.lower() for x in country_select]
        report_state['filters'].append(
            {"name": 'Company', "type": "list", "values": country_select})


def shops(report):
    """
    Список магазинов (зависит от выбора страны).
    :param report: Текущий отчет.
    :return: Объект multiselect.
    """
    country_select = get_filter('Country', report)  # country(report)
    # selected - пользователь что-то выбрал и это идет в фильтр sql-запроса
    report_state = st.session_state['reports'][report]
    user_has_filter = False  # необходимо проставлять для мультиселектов

    report_state = st.session_state['reports'][report]
    # shop_name_key = f"{report}_ShopName_filter"

    # if shop_name_key not in st.session_state:
    #     st.session_state[shop_name_key] = []
    # filter_keys = [shop_name_key]
    # clear_button = st.button('Очистить', icon=":material/backspace:", key='shops_clear')
    # if clear_button:
    #     clear_filter(filter_keys)

    # with st.popover('Магазины'):
    st.write('**Магазины**')
    # filtered - фильтрация интерфейса пользователя (напр.: фильтр магазинов от выбора страны)
    # report_state['country_filtered'] = []
    report_state['shops_name_filtered'] = []
    report_state['union_filtered'] = []
    report_state['cities_filtered'] = []

    # формирование основного набора значений для выпадающих списков
    if 'shops_dataframe' not in report_state:
        request_result = request_tools.get_dict('shops')
        user_filter = get_user_filter('UnionIndex', request_result)
        if user_filter is not None:
            user_has_filter = True
            report_state['shops_dataframe'] = user_filter
        else:
            report_state['shops_dataframe'] = request_result

    shops_df = report_state['shops_dataframe']
    # report_state['country_filtered'] = shops_df['country'].unique()
    report_state['shops_name_filtered'] = shops_df['shop_name'].unique()
    report_state['union_filtered'] = shops_df['shop_id'].unique()
    report_state['cities_filtered'] = shops_df['city'].unique()

    countries_list = country_select  # st.multiselect('Страна', report_state['country_filtered'])
    st.session_state['selected_country'] = countries_list
    report_state['selected_country'] = countries_list

    if countries_list is not None:
        report_state['shops_dataframe_filtered'] = shops_df.loc[shops_df['country'].isin(countries_list)]
        # report_state['union_filtered'] = report_state['shops_dataframe_filtered']['shop_id']
        report_state['shops_name_filtered'] = report_state['shops_dataframe_filtered']['shop_name']
        report_state['cities_filtered'] = report_state['shops_dataframe_filtered']['city'].unique()

    cities_list = st.multiselect('Город', report_state['cities_filtered'])
    report_state['selected_city'] = cities_list

    if len(cities_list) > 0:
        report_state['shops_dataframe_filtered'] = shops_df.loc[shops_df['city'].isin(cities_list)]
        report_state['union_filtered'] = report_state['shops_dataframe_filtered']['shop_id']
        report_state['shops_name_filtered'] = report_state['shops_dataframe_filtered']['shop_name']

    shops_list = st.multiselect('Магазин', report_state['shops_name_filtered'])  #, key=shop_name_key)
    report_state['selected_shops'] = shops_list

    if len(shops_list) > 0:
        report_state['shops_dataframe_filtered'] = shops_df.loc[shops_df['shop_name'].isin(shops_list)]
        report_state['union_filtered'] = report_state['shops_dataframe_filtered']['shop_id']

    union_list = st.multiselect('Объединение', report_state['union_filtered'])
    report_state['selected_union'] = union_list

    if len(union_list) > 0:
        report_state['shops_dataframe_filtered'] = shops_df.loc[shops_df['shop_id'].isin(union_list)]
        report_state['union_filtered'] = report_state['shops_dataframe_filtered']['shop_id']

    if len(report_state['union_filtered']) != len(report_state['shops_dataframe']['shop_id']) or user_has_filter:
        report_state['filters'].append(
            {"name": "UnionIndex", "type": "list", "values": report_state['union_filtered']})


def check_if_selected(selection_list, state, report):
    report_state = st.session_state['reports'][report]
    if len(selection_list) > 0:
        report_state[state] = True
    else:
        report_state[state] = False


def single_brand(report):
    st.write('**Бренды**')
    report_state = st.session_state['reports'][report]
    report_state['brand_name_filtered'] = []

    # формирование основного набора значений для выпадающих списков
    if 'brands_dataframe' not in report_state:
        report_state['brands_dataframe'] = request_tools.get_dict('brands')

    brands_df = report_state['brands_dataframe']
    brands_name_list = st.multiselect('Бренд', report_state['brands_dataframe']['BrandName'])
    check_if_selected(brands_name_list, 'brand_name_selected', report)

    if report_state['brand_name_selected']:
        report_state['brands_dataframe_filtered'] = brands_df.loc[brands_df['BrandName'].isin(brands_name_list)]
        report_state['filters'].append(
            {"name": "BrandId", "type": "list", "values": report_state['brands_dataframe_filtered']['BrandId']})


def escape_apostrophes(strings):
    return [s.replace("'", "\\'") for s in strings]


def process_string(input_string):
    # Заменяем запятые на пробелы
    input_string = input_string.replace(',', ' ')
    # Разделяем строку по пробелам и убираем пустые строки
    numbers = input_string.split()
    # Преобразуем числа в целые и убираем дубликаты
    unique_numbers = list(set(str(number) for number in numbers))
    # Сортируем полученные уникальные числа
    unique_numbers.sort()
    return unique_numbers


def items_categories(report):
    """
    Категории товаров.
    :param report: Текущий отчет.
    :return: Несколько объектов multiselect.
    """
    st.write('**Категории товаров**')
    report_state = st.session_state['reports'][report]

    # filtered - фильтрация интерфейса пользователя (напр.: фильтр магазинов от выбора страны)
    report_state['analytics_category_filtered'] = []
    report_state['price_category_1_filtered'] = []
    report_state['price_category_2_filtered'] = []
    report_state['price_category_3_filtered'] = []
    report_state['price_category_4_filtered'] = []

    # формирование основного набора значений для выпадающих списков
    if 'categories_dataframe' not in report_state:
        report_state['categories_dataframe'] = request_tools.get_dict('categories')

    categories_df = report_state['categories_dataframe']
    report_state['analytics_category_filtered'] = categories_df['AnalyticsCategory'].unique()
    report_state['price_category_1_filtered'] = categories_df['PriceCategory1'].unique()
    report_state['price_category_2_filtered'] = categories_df['PriceCategory2'].unique()
    report_state['price_category_3_filtered'] = categories_df['PriceCategory3'].unique()
    report_state['price_category_4_filtered'] = categories_df['PriceCategory4'].unique()

    analytics_category_list = st.multiselect('Аналитическая категория', report_state['analytics_category_filtered'])
    if analytics_category_list:
        report_state['categories_dataframe_filtered'] = categories_df.loc[categories_df[
            'AnalyticsCategory'].isin(analytics_category_list)]
        report_state['price_category_1_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory1'].unique()
        report_state['price_category_2_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory2'].unique()
        report_state['price_category_3_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory3'].unique()
        report_state['price_category_4_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory4'].unique()

    price_category_1_list = st.multiselect('Категория 1', report_state['price_category_1_filtered'])
    if price_category_1_list:
        report_state['categories_dataframe_filtered'] = categories_df.loc[
            categories_df['PriceCategory1'].isin(price_category_1_list)]
        report_state['price_category_2_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory2'].unique()
        report_state['price_category_3_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory3'].unique()
        report_state['price_category_4_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory4'].unique()

    price_category_2_list = st.multiselect('Категория 2', report_state['price_category_2_filtered'])
    if price_category_2_list:
        report_state['categories_dataframe_filtered'] = categories_df.loc[
            categories_df['PriceCategory2'].isin(price_category_2_list)]
        report_state['price_category_3_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory3'].unique()
        report_state['price_category_4_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory4'].unique()

    price_category_3_list = st.multiselect('Категория 3', report_state['price_category_3_filtered'])
    if price_category_3_list:
        report_state['categories_dataframe_filtered'] = categories_df.loc[
            categories_df['PriceCategory3'].isin(price_category_3_list)]
        report_state['price_category_4_filtered'] = report_state['categories_dataframe_filtered'][
            'PriceCategory4'].unique()
    price_category_4_list = st.multiselect('Категория 4', report_state['price_category_4_filtered'])
    if analytics_category_list:
        report_state['filters'].append(
            {"name": "AnalyticsCategory", "type": "list", "values": analytics_category_list})
    if price_category_1_list:
        report_state['filters'].append(
            {"name": "PriceCategory1", "type": "list", "values": escape_apostrophes(price_category_1_list)})
    if price_category_2_list:
        report_state['filters'].append(
            {"name": "PriceCategory2", "type": "list", "values": escape_apostrophes(price_category_2_list)})
    if price_category_3_list:
        report_state['filters'].append(
            {"name": "PriceCategory3", "type": "list", "values": escape_apostrophes(price_category_3_list)})
    if price_category_4_list:
        report_state['filters'].append(
            {"name": "PriceCategory4", "type": "list", "values": escape_apostrophes(price_category_4_list)})


def brands(report):
    st.write('**Бренды**')
    report_state = st.session_state['reports'][report]
    report_state['brand_id_filtered'] = []
    report_state['brand_name_filtered'] = []

    # формирование основного набора значений для выпадающих списков
    if 'brands_dataframe' not in report_state:
        report_state['brands_dataframe'] = request_tools.get_dict('brands')

    brands_df = report_state['brands_dataframe']
    brands_list = st.multiselect('Код бренда', report_state['brands_dataframe']['BrandId'], help='Второй приоритет')
    brands_name_list = st.multiselect('Бренд', report_state['brands_dataframe']['BrandName'], help='Первый приоритет')

    check_if_selected(brands_list, 'brand_id_selected', report)
    check_if_selected(brands_name_list, 'brand_name_selected', report)

    # Если выбран код бренда - он идет в фильтр данных. Нивелируется фильтром ниже.
    if report_state['brand_id_selected']:
        report_state['brands_dataframe_filtered'] = brands_df.loc[brands_df['BrandId'].isin(brands_list)]

    # Т.к. условия идут одно за другим, фильтр по названию бренда идет в приоритет.
    if report_state['brand_name_selected']:
        report_state['brands_dataframe_filtered'] = brands_df.loc[brands_df['BrandName'].isin(brands_name_list)]

    brands_input_list = st.text_input('Код бренда (ручной ввод)', placeholder='Укажите код бренда',
                                      help='Наивысший приоритет. '
                                           'Впишите один или несколько кодов брендов (напр.: 100189, 103145 и т.д.).')
    if len(brands_input_list) > 0:
        # brands_list = brands_input_list.split(",")
        # brands_list = [f"{brand.strip()}" for brand in brands_list]
        report_state['filters'].append(
            {"name": "BrandId", "type": "list", "values": process_string(brands_input_list)})
    else:
        # Формирование списка фильтра по брендам.
        if report_state['brand_id_selected'] or report_state['brand_name_selected']:
            report_state['filters'].append(
                {"name": "BrandId", "type": "list", "values": report_state['brands_dataframe_filtered']['BrandId']})


def items(report):
    """
    Номенкратурные фильтры.
    :param report: Текущий отчет.
    :return: Набор элементов для фильтрации полей.
    """
    st.write('**Товары**')
    report_state = st.session_state['reports'][report]


def clear_filter(filter_keys: list):
    for filter_key in filter_keys:
        st.session_state[filter_key] = []  #: = ""


def items_input(report, with_barcodes=True):
    """
    Ручной ввод товаров.
    :param report: Текущий отчет.
    :param with_barcodes: Добавить штрикоды.
    :return: Несколько полей для ввода значений.
    """
    report_state = st.session_state['reports'][report]
    item_key = f"{report}_ItemId_filter"
    if 'item_filter' not in report_state:
        report_state['item_filter'] = False
    if item_key not in st.session_state:
        st.session_state[item_key] = ''
    # filter_keys = [item_key]
    # clear_button = st.button('Очистить', icon=":material/backspace:", key='items_clear')
    # if clear_button:
    #     clear_filter(filter_keys)

    # with st.popover('Товары'):
    st.write('**Товары**')

    items_input_list = st.text_input('Код товара (ручной ввод)', placeholder='Укажите код товара',
                                     help='Впишите один или несколько товарных кодов (напр.: 16874500008, 19000117252 и т.д.).'
                                     # , key=f"{report}_ItemId_filter"
                                     )
    if len(items_input_list) > 0:
        report_state['filters'].append(
            {"name": "ItemId", "type": "list", "values": process_string(items_input_list)})
        # report_state['item_filter'] = True

    if with_barcodes:
        barcodes_input_list = st.text_input('Штрихкод продажи (ручной ввод)', placeholder='Укажите штрихкод продажи',
                                            help='Впишите один или несколько штрихкодов (напр.: 4630007831244, 4630007831305 и т.д.).'
                                            # , key='ItemBarcode_filter'
                                            )
        if len(barcodes_input_list) > 0:
            report_state['filters'].append(
                {"name": "ItemBarcode", "type": "list", "values": process_string(barcodes_input_list)})
            # report_state['item_filter'] = True

        default_barcodes_input_list = st.text_input('Основной штрихкод (ручной ввод)', placeholder='Укажите основной штрихкод',
                                            help='Впишите один или несколько штрихкодов (напр.: 4630007831244, 4630007831305 и т.д.).')
        if len(default_barcodes_input_list) > 0:
            report_state['filters'].append(
                {"name": "ItemDefaultBarcode", "type": "list", "values": process_string(default_barcodes_input_list)})
            # report_state['item_filter'] = True
    # if report_state['item_filter']:
    #     st.badge('Есть фильтр', icon=":material/check:", color="green")


def get_db_client(connection_type: str = 'devs'):
    client = None
    if connection_type == 'devs':
        # client = Client(host=config.CH_HOST, user=config.CH_USER, password=config.CH_PASSWORD)
        client = get_client(host=config.CH_HOST, port=8123, username=config.CH_USER,
                            password=config.CH_PASSWORD, connect_timeout=3000)
    if connection_type == 'prod':
        # client = Client(host=config.CH_HOST_PROD, user=config.CH_USER_PROD, password=config.CH_PASSWORD_PROD)
        client = get_client(host=config.CH_HOST_PROD, port=8123, username=config.CH_USER_PROD, password=config.CH_PASSWORD_PROD, connect_timeout=3000)
    return client


def format_df(df, additional_config=None, height=None):
    column_config = {}
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            column_config[column] = st.column_config.NumberColumn(format="localized")
    if additional_config is not None:
        column_config = column_config | additional_config
    return st.dataframe(df, column_config=column_config, height=height)


def connect_and_show(report, sql, filters, connection_type):
    """
    Функция запроса к БД.
    :param report: Текущий отчет.
    :param sql: SQL-запрос.
    :param filters: Фильтры (строка или словарь, где ключи - ключевые слова в запросе, которые надо заменить на значения)
    :param connection_type: Тип подключения (для разных ДБ).
    :return: Датафрейм - результат запроса.
    """
    client = get_db_client(connection_type)  # Client(host=config.CH_HOST, user=config.CH_USER, password=config.CH_PASSWORD)
    report_sql = queries.report_query[f'{sql}']
    if isinstance(filters, str):
        report_sql = report_sql.replace('@filters', filters)
    if isinstance(filters, dict):
        for sql_filter in filters.keys():
            report_sql = report_sql.replace(sql_filter, filters[sql_filter])
    request_result = request_tools.send_report_request(report_sql, report, client)
    return request_result


def connect_and_load(report, connection_type):
    user_login = st.session_state['user']['login']
    with st.spinner('Выгружаем данные. Ожидайте, пожалуйста...', show_time=True):
        start_time = time.time()
        client = get_db_client(connection_type)  # Client(host=config.CH_HOST, user=config.CH_USER, password=config.CH_PASSWORD)
        sql_header = '/* {"app":"reports", "report":"' + report + '", "user":"' + user_login + '"} */'
        report_sql = f'{sql_header}\n' + queries.report_query[f'{report}']
        sql = request_tools.get_report_sql(report_sql, report)
        rows_count = request_tools.rows_count_request(sql, client)
        # st.write(f'Количество строк: {rows_count}')
        if rows_count < config.EXCEL_ROWS_LIMIT:
            st.badge(f'Количество строк: {rows_count}', icon=":material/check:", color="green")
            request_result = request_tools.send_report_request(report_sql, report, client)
            st.download_button(icon=":material/download:", label="Скачать Excel-файл", data=request_tools.to_excel(request_result, sql),
                               file_name=f'{report}_download_{datetime.datetime.now().strftime("%Y-%m-%d %H%M%S")}.xlsx')
            st.write(f'Пример выгрузки (первые {config.EXAMPLE_ROWS_LIMIT} зап.):')
            column_first, column_second = st.columns(2)
            with column_first:
                request_result_example = request_result.head(config.EXAMPLE_ROWS_LIMIT)
                format_df(request_result_example)
            st.toast('Выгрузка завершена. Можно скачать Excel-файл.', icon=":material/check:")
        else:
            # st.warning(f'Количество строк более {config.EXCEL_ROWS_LIMIT}. Уменьшите объем запрашиваемых данных.')
            st.badge(f'⚠️ Количество строк ({rows_count}) превышает лимит ({config.EXCEL_ROWS_LIMIT}). Уменьшите объем запрашиваемых данных.', color="orange")
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        try:
            pg_connect = pg_manager.connect_to_pg()
            pg_q = pg_manager.PGQ(pg_connect)
            pg_q.save_request_log(report, user_login, sql, elapsed_seconds)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            pass


def input_is_correct(report):
    report_state = st.session_state['reports'][report]
    result = False
    if len(report_state['metrics']) == 0:
        st.warning("Не выбран показатель.")
    else:
        result = True
    return result


def excel_loader(report, connection_type):
    st.write('Выберите показатели и детализацию (измерения) таблицы. '
             'Нажмите кнопку "Посчитать количество строк", чтобы определить объем запрошенных данных.')

    sample_button = st.button('Посчитать количество строк', icon=":material/calculate:")
    if sample_button:
        if input_is_correct(report):
            connect_and_load(report, connection_type)


def show_sql(report):
    st.write('🛠️ Инструменты разработчика')
    with st.expander('SQL-запрос', expanded=False):
        if input_is_correct(report):
            query = queries.report_query[f'{report}']
            st.code(request_tools.get_report_sql(query, report))


def invoke_metric():
    return metrics.Metric()


def metric(metric_class, name, report, currency_flag):
    report_state = st.session_state['reports'][report]
    target_metric = metric_class.get_metric(name, currency_flag)
    # metric_id = target_metric['id']
    metric_selected = st.checkbox(target_metric['name'], help=target_metric['description'])
    if metric_selected:
        report_state['metrics'].append(target_metric['value'])


def dimension(name, field, report):
    report_state = st.session_state['reports'][report]
    dimension_value = f'{field} as "{name}"'
    dimension_selected = st.checkbox(name)
    if dimension_selected:
        report_state['dimensions'].append(dimension_value)


def cross_dimension(name, field, report):
    report_state = st.session_state['reports'][report]
    dimension_value = f'{field} as "{name}"'
    dimension_selected = st.checkbox(name)
    if dimension_selected:
        report_state['cross_dimensions'].append(dimension_value)
        angle_filter = get_global_filter('RacursId')
        if angle_filter['response']:
            filter_text = f"and RacursName in ({angle_filter['filter']['values']})"
        else:
            filter_text = ''
        report_state['join_condition'] = queries.join_query['angle'].replace('@angle_filter', filter_text)


def draw_dynamic(report, x_dict, query_report, y_values):
    report_state = st.session_state['reports'][report]
    dynamic_x_dict = x_dict
    st.write('Выберите детализацию графика')
    dynamic_x = st.radio("Ось X", dynamic_x_dict.keys(), horizontal=True)
    if len(report_state['metrics']) == 0:
        st.warning('Не выбран показатель')
    else:
        show_dynamic = st.button('Показать динамику')
        if show_dynamic:
            with st.spinner('Рисуем графики...'):
                report_state['dynamic_x'] = dynamic_x
                report_state = st.session_state['reports'][report]
                client = get_db_client()  # Client(host=config.CH_HOST, user=config.CH_USER, password=config.CH_PASSWORD)
                report_sql = queries.report_query[f'{query_report}']
                period_name = report_state['dynamic_x']
                period_field = dynamic_x_dict[report_state['dynamic_x']]['field']
                period_format = dynamic_x_dict[report_state['dynamic_x']]['format']
                report_state['dimensions'] = [f'{period_field} as "{period_name}"']
                metric_object = {}
                metric_split = report_state['metrics'][0].split(' as ')
                metric_object['name'] = metric_split[1].replace('"', '')
                metric_object['formula'] = metric_split[0]
                report_state['order_by'] = f'ORDER BY {period_field} ASC'
                if report_state['brand_name_selected']:
                    if len(report_state['brands_dataframe_filtered']['BrandName']) == 1:
                        title = report_state['brands_dataframe_filtered']['BrandName'].iloc[0]
                    else:
                        title = 'Несколько брендов'
                else:
                    title = ''
                request_result = request_tools.send_report_request(report_sql, report, client)
                fig = px.line(request_result, x=period_name, y=metric_object['name'], markers=True, title=title)
                fig.update_layout(
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=16
                    )
                )
                fig.update_xaxes(
                    tickformat=period_format
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(request_result)
    #  st.write(st.session_state)


def draw_map_polygon(coordinates_df, weight_df, map_center, tooltip):
    def create_polygon(polygon_id, polygon_coordinates):
        polygons = []
        for polygon in polygon_coordinates:
            single_polygon = []
            for coordinates in polygon:
                single_polygon.append([float(coordinates[0]), float(coordinates[1])])
            polygons.append(single_polygon)
        return {'type': 'Feature',
                'geometry': {'type': 'Polygon',
                             'coordinates': polygons},
                'id': polygon_id}

    target_polygons = []
    for index, row in coordinates_df.iterrows():
        target_polygons.append(create_polygon(row[0], row[1]))

    # если значение одно, то x надо завернуть в []
    custom_data = [x for x in weight_df[tooltip['columns']].values.tolist()]
    geojson = {"type": "FeatureCollection", "features": target_polygons}
    fig = go.Figure(data=dict(type='choroplethmapbox', geojson=geojson, locations=weight_df.locations, z=weight_df.z_weight,
                                        colorscale="Viridis", zmin=0, zmax=weight_df.z_weight.max(),
                                        marker_opacity=0.5, marker_line_width=0, customdata=custom_data,
                              hovertemplate=tooltip['text']))
    fig.update_layout(mapbox_style="carto-positron", mapbox_zoom=9, mapbox_center=map_center, hovermode='closest')
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=800)
    st.plotly_chart(fig, use_container_width=True)


def pretty_df(df, numbers_columns, pinned_columns, with_totals=None, filterable=False):
    # gridOptions - словарь настроек
    # builder - редактор словаря настроек (https://streamlit-aggrid.readthedocs.io/en/docs/GridOptionsBuilder.html)
    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_default_column(sorteable=False, filterable=filterable)
    builder.configure_columns(numbers_columns, valueFormatter="x.toLocaleString()")
    builder.configure_columns(pinned_columns, width=150, pinned='left')
    builder.configure_grid_options(alwaysShowHorizontalScroll=True)
    if with_totals is not None:
        cellstyle_jscode = JsCode("""
        function(params) {
            if (params.node.rowIndex === 0) {
                return { backgroundColor: 'rgb(220, 255, 0)', fontFamily: 'Graphik LCG', fontWeight: 'bold' };  // Устанавливаем серый фон для первой строки
            }
            return {fontFamily: 'Graphik LCG'};  // Для остальных строк стиль не изменяется
        }
        """)
    else:
        cellstyle_jscode = JsCode("""
                function(params) {                    
                    return {fontFamily: 'Graphik LCG'};  // Для остальных строк стиль не изменяется
                }
                """)
    builder.configure_columns(df, cellStyle=cellstyle_jscode)
    custom_css = {
        ".ag-theme-streamlit": {
            "--ag-row-hover-color": "rgba(220, 255, 0, 0.5) !important",
            "--ag-range-selection-border-color": "#4f00ff !important"
        }
    }
    # Добавляем стиль и колонные определения в gridOptions
    gob = builder.build()
    # st.write(gob)
    return AgGrid(df, gridOptions=gob, allow_unsafe_jscode=True, custom_css=custom_css)


def simple_altair_line_chart(df, title, metrics_list):
    df_long = df.melt(id_vars=["Месяц"],
                      value_vars=metrics_list,
                      var_name="Показатель", value_name="Значение")
    chart = alt.Chart(df_long).mark_line().encode(
        x=alt.X('Месяц:O', sort=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], axis=alt.Axis(labelAngle=0, labelFontSize=14)),
        y=alt.Y('Значение:Q', axis=alt.Axis(labelFontSize=14, titleFontSize=16)),
        color=alt.Color('Показатель:N', legend=alt.Legend(orient='top', labelLimit=300))
    ).properties(
        title=title
    ) + alt.Chart(df_long).mark_circle(size=100).encode(
        x=alt.X('Месяц:O', sort=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
        y='Значение:Q',
        color=alt.Color('Показатель:N', legend=alt.Legend(orient='top', labelLimit=300))
    ) + alt.Chart(df_long).mark_text(align='center', dy=15, fontSize=14).encode(
        x=alt.X('Месяц:O', sort=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]),
        y=alt.Y('Значение:Q', title=None),
        text='Значение:N'
    )
    st.altair_chart(chart, use_container_width=True)

