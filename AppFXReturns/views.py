import matplotlib

# disable TK
matplotlib.use('agg')

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse, JsonResponse
from django.template import loader

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
import sqlite3
import pandas as pd
import numpy as np
import json
import os


DB = 'Validus/Data/validus.db'

# utility function
import string
import random
def rand_string_generator(size=8, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


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
        curr_condition = "AND base_curr = '{curr}'".format(curr=currency.upper())

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

    if report in ['rolling_covariance', 'rolling correlation']:
        curr_condition = ''
    
    conn = sqlite3.connect(DB)
    crs = conn.cursor()

    file_name = '{report}_{rand}.pdf'.format(report=report, rand=rand_string_generator())
    file_path = os.path.join('Validus/Data/temp', file_name)

    response = HttpResponse()

    query = """
    SELECT value_date, base_curr AS currency, fx_rate
    FROM m_fx_rate
    WHERE value_date BETWEEN '{start_date}' AND '{end_date}'
        {curr_condition}
    ORDER BY base_curr, value_date
    """.format(
        curr_condition=curr_condition,
        start_date=dt.datetime.strftime(start_date, '%Y-%m-%d'),
        end_date=dt.datetime.strftime(end_date, '%Y-%m-%d'),
    )
    crs.execute(query)

    data = crs.fetchall()
    # convert to python date from string
    data = [(dt.datetime.strptime(x[0], '%Y-%m-%d'), x[1], x[2]) for x in data]
    cols = ['value_date', 'currency', 'fx_rate']

    df_data = pd.DataFrame(data, columns=cols)

    df_data.set_index(['currency', 'value_date'], inplace=True)

    # assumption: 261 approx business days in a year
    num_business_days = 261
    years = mdates.YearLocator()
    months = mdates.MonthLocator()
    yearsFmt = mdates.DateFormatter('%Y')

    if report == 'daily_return':
        df_data['daily_return'] = df_data.pct_change(fill_method='pad')

        fig, ax = plt.subplots()

        for key, grp in df_data.reset_index().groupby(['currency']):
            ax = grp.plot(ax=ax, kind='line', x='value_date', y='daily_return',
                figsize=(6, 4), title='Daily Return',
                label=key, linewidth='0.5')

            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(yearsFmt)
            ax.xaxis.set_minor_locator(months)

    elif report == 'rolling_average':
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(5, 5), sharex=True)

        for i in range(1, 4):
            for key, grp in df_data.reset_index().groupby(['currency']):
                ax = grp.set_index(['value_date']).rolling(num_business_days*(i)).mean().plot(
                    ax=axes[i-1], kind='line',
                    y='fx_rate',
                    title='Rolling Average {i} Year'.format(i=str(i)),
                    label=key, linewidth='0.5')

                ax.set_xlim(start_date, end_date)
                ax.xaxis.set_major_locator(years)
                ax.xaxis.set_major_formatter(yearsFmt)
                ax.xaxis.set_minor_locator(months)

    elif report == 'rolling_standard_deviation':
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(5, 5), sharex=True)

        for i in range(1, 4):
            for key, grp in df_data.reset_index().groupby(['currency']):
                ax = grp.set_index(['value_date']).rolling(num_business_days*(i)).std().plot(
                    ax=axes[i-1], kind='line',
                    y='fx_rate',
                    title='Rolling Standard Deviation {i} Year'.format(i=str(i)),
                    label=key, linewidth='0.5')

                ax.set_xlim(start_date, end_date)
                ax.xaxis.set_major_locator(years)
                ax.xaxis.set_major_formatter(yearsFmt)
                ax.xaxis.set_minor_locator(months)
        
    elif report == 'rolling_covariance':
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(5, 5), sharex=True)
        for i in range(1, 4):
            # assume only two groups: USD and EUR
            grps = [grp for _, grp in df_data.reset_index().groupby(['currency'])]
            ax = grps[0][['value_date', 'fx_rate']].set_index(['value_date']).rolling(
                    num_business_days*i).cov(grps[1][['value_date', 'fx_rate']].set_index(['value_date'])).plot(
                    ax=axes[i-1], kind='line',
                    y='fx_rate',
                    title='Rolling Covariance EUR vs USD {i} Year'.format(i=str(i)),
                    linewidth='0.5')
        
    elif report == 'rolling_correlation':
        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(5, 5), sharex=True)
        for i in range(1, 4):
            # assume only two groups: USD and EUR
            grps = [grp for _, grp in df_data.reset_index().groupby(['currency'])]
            ax = grps[0][['value_date', 'fx_rate']].set_index(['value_date']).rolling(
                    num_business_days*i).corr(grps[1][['value_date', 'fx_rate']].set_index(['value_date'])).plot(
                    ax=axes[i-1], kind='line',
                    y='fx_rate',
                    title='Rolling Correlation EUR vs USD {i} Year'.format(i=str(i)),
                    linewidth='0.5')
        
    else:
        plt.close()
        raise ValueError("Invalid Report Type.")

    plt.legend(loc='best')
    fig.autofmt_xdate()
    plt.savefig(file_path)
    plt.close()
    
    # response['Content-Disposition'] = 'attachment; filename={file_path}'.format(file_path=file_path)
    conn.close()
    return response

