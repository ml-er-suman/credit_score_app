from django.shortcuts import render, redirect
from stock.forms import RegistrationForm
from django.http import HttpResponse
# For machine learning

import pandas as pd
import numpy as np
import math, datetime
from sklearn import preprocessing, model_selection
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import NearestNeighbors
from sklearn import neighbors, svm
import matplotlib.pyplot as plt
from matplotlib import style
import pickle
from .districts import zone,allzone

import json
import pandas as pd
import pickle
from sklearn.externals import joblib

# checking if plotly is installed; install otherwise
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
import plotly

#extract acct_details from neps daily
import pyodbc
conn = pyodbc.connect('DRIVER={SQL Server};SERVER=10.0.4.42,1433;DATABASE=MBLATM;UID=BIservice;PWD=BI@123')

#extract credit card customer of latest month
import datetime
today = datetime.date.today()
first = today.replace(day=1)
lastMonth = first - datetime.timedelta(days=1)
date_to_extract = today.strftime('%Y')+ "-"+ lastMonth.strftime('%m') +"-"+ today.strftime('%d')

credit_customer = pd.read_sql("SELECT * FROM CREDIT_CARD_NEPS_DETAILS" , conn)
credit_customer.drop_duplicates("CARD_NUMBER",inplace = True)
total_customer = len(credit_customer)
last_month = len(credit_customer[credit_customer['ISSUE_DATE'] > date_to_extract])
percentage_growth = round((last_month/(total_customer-last_month))*100,2)

yesterday = datetime.datetime.strftime(datetime.datetime.now() - datetime.timedelta(1), '%Y-%m-%d')
yesterday_cust = len(credit_customer[credit_customer['ISSUE_DATE'] == yesterday])

overdue = pd.read_sql("SELECT * from overdue where MAX_AGING >2",conn)
total_default_cust = len(overdue)
default_percentage = round((total_default_cust/(total_customer))*100,2)

# For visualization
credit_customer['ISSUE_DATE'] = credit_customer['ISSUE_DATE'].apply(lambda x:str(x)[0:7])
credit_customer["No_of_issue_card"] = credit_customer.groupby("ISSUE_DATE")["CARD_NUMBER"].transform("count")
c=  go.Scatter(
                x=credit_customer.ISSUE_DATE,
                y=credit_customer.No_of_issue_card,
                textposition = 'top right',
                mode ="lines+markers+text",
                line = dict(color = '#17BECF'),
                opacity = 0.6)

data = [c]

layout = dict(
    legend=dict(x=-.1, y=1.2),
    showlegend=True,
    title = "NO_OF_CARDS",
    xaxis = dict(
            title='DATE',
            tickangle= 35,
            showticklabels= True,
            titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'),        
            type= 'category'
    ),

    yaxis=dict(
        showticklabels= True,
        title='NO of Cards',
        titlefont=dict(
            family='Courier New, monospace',
            size=18,
            color='#7f7f7f'
        )),

)

fig = dict(data=data, layout=layout)
graph_div = plotly.offline.plot(fig, auto_open = False, output_type="div")



lr = joblib.load('D:/dump_model/model.pkl')
model_columns=joblib.load("D:/dump_model/columns_model.pkl")
style.use('ggplot')
allzone=json.dumps(allzone)

def index(request):
    return render(request, 'accounts/home.html',{'zone':zone,"allzone":allzone,
        'total_customer':total_customer,'percentage_growth':percentage_growth,
        'default_percentage':default_percentage,'total_default_cust':total_default_cust,
        'yesterday_cust':yesterday_cust,'graph_div':graph_div})

def test(request):
    return render(request, 'accounts/test.html',{'zone':zone,"allzone":allzone})

def get_prediction(request):
    if request.method == 'POST':
        test_json = request.POST
        print(test_json)
        data = pd.DataFrame(test_json,index=[0])
        data.columns = [x.upper() for x in data.columns]
        data['DISTRICT'] = data['DISTRICT'].apply(lambda x:"INSIDE_VALLEY" if x =="KATHMANDU" else "OUT_OF_VALLEY")
        df = data.drop(columns = ["YR_OF_EMP","MONTHLY_INCOME_RANGE"])
        test = pd.get_dummies(df)
        MONTHLY_INCOME_RANGE = data['MONTHLY_INCOME_RANGE']
        YR_OF_EMP = data['YR_OF_EMP']
        test["MONTHLY_INCOME_RANGE"] = MONTHLY_INCOME_RANGE
        test["YR_OF_EMP"] = YR_OF_EMP
        # #make all columns uppercase
        test.columns = [x.upper() for x in test.columns]
        final_data = test.copy()
        print(final_data.to_string())
        query=final_data.reindex(columns=model_columns,fill_value=0)
        print(query.to_string())
        print(data["FULL_NAME"])

        #prediction
        prediction=lr.predict_proba(query)
        prediction = np.round(prediction,3)
        print(prediction)
        result = pd.DataFrame(data = prediction, columns =["non_default","default"])
        result['score'] = result["non_default"].apply(lambda x:"Eligible" if x > 0.90 else "Not Eligible")
        customer_name = list(data["FULL_NAME"])
        score = list(result['score'])
        non_default = list(result['non_default'])
        default = list(result['default'])
        final = zip(customer_name,non_default,default,score)

        print("The model has been loaded...doing predictions now...")
        print(result)
        # predictions = lr.predict(test_json)
        return render(request, 'accounts/predict.html', {'final':final})



