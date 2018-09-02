from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from django.template import loader

import datetime as dt
import sqlite3
import pandas as pd
import numpy as np
import json

DB = 'Validus/Data/validus.db'

def index(request):
    context = {
        'title': 'FX Rate Report',
    }
    return render(request, 'index.html', context)


def get_date_range(request):
    conn = sqlite3.connect(DB)
    crs = conn.cursor()

    crs.execute("""
    SELECT DISTINCT value_date
    FROM m_fx_rate
    ORDER BY value_date DESC
    """)

    data = sorted(list(set([dt.datetime.strptime(x[0], '%Y-%m-%d').year for x in crs.fetchall()])))
    conn.close()
    return JsonResponse({ 'years': data })


def get_request_param(request):
    payload_data = request.body.decode('utf-8')
    payload_data = json.loads(payload_data)

    start_year = payload_data.get('start_year', '')
    end_year = payload_data.get('end_year', '')
    currency = payload_data.get('currency', '')
    report = payload_data.get('report', 'daily_return')

    start_date = dt.datetime(year=int(start_year), month=1, day=1)
    end_date = dt.datetime(year=int(end_year), month=12, day=31)
    curr_condition = ''
    if currency.upper() in ['EUR', 'USD']:
        curr_condition = "AND base_currency = '{curr}'".format(curr=currency.upper())

    return start_date, end_date, currency, report, curr_condition

def show_data(request):
    start_date, end_date, _, _, curr_condition = get_request_param(request)

    print(end_date)
    print(curr_condition)
    print(start_date)

    conn = sqlite3.connect(DB)
    crs = conn.cursor()

    query = """
    SELECT value_date, trade_curr AS currency, base_curr AS base_currency, fx_rate
    FROM m_fx_rate
    WHERE value_date BETWEEN '{start_date}' AND '{end_date}'
        {curr_condition}
    ORDER BY base_curr, value_date DESC
    """.format(
        curr_condition=curr_condition,
        start_date=dt.datetime.strftime(start_date, '%Y-%m-%d'),
        end_date=dt.datetime.strftime(end_date, '%Y-%m-%d'),
    )
    crs.execute(query)

    data = crs.fetchall()
    cols = ['value_date', 'currency', 'base_currency', 'fx_rate']

    df_data = pd.DataFrame(data, columns=cols)
    return JsonResponse(df_data.to_dict(orient='split'))

def gen_report(request):

    start_date, end_date, currency, report, curr_condition = get_request_param(request)
    
    conn = sqlite3.connect(DB)
    crs = conn.cursor()

    if report == 'daily_return':

        query = """
        SELECT value_date, base_curr AS currency, fx_rate
        FROM m_fx_rate
        WHERE value_date BETWEEN '{start_date}' AND '{end_date}'
            {curr_condition}
        ORDER BY base_curr, value_date DESC
        """.format(
            curr_condition=curr_condition,
            start_date=dt.datetime.strftime(start_date, '%Y-%m-%d'),
            end_date=dt.datetime.strftime(end_date, '%Y-%m-%d'),
        )
        crs.execute(query)

        data = crs.fetchall()
        cols = ['value_date', 'currency', 'fx_rate']

        df_data = pd.DataFrame(data, columns=cols)
        df_data['']


    conn.close()
    return JsonResponse({})

