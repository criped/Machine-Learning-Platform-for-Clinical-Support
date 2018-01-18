#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.db.models.fields import FloatField, IntegerField, CharField
from django.forms.fields import ChoiceField, BooleanField
from arff import load
import pandas as pd
from sklearn.ensemble.forest import RandomForestClassifier
from sklearn.cross_validation import cross_val_score
from sklearn.externals import joblib
from django.core.files.uploadedfile import InMemoryUploadedFile
from numpy import zeros, asarray
import os
from tempfile import mkstemp
import matplotlib.pyplot as plt; plt.rcdefaults()
import matplotlib.pyplot as plt
import numpy as np
from cStringIO import StringIO
from pylab import get_current_fig_manager
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.pyplot import savefig, figure
from django.conf import settings
from treeinterpreter import treeinterpreter


def field_from_attr(attr):
    attr_type = attr[1]
    attr_name = str(attr[0])
    
    if (str(attr_type).upper() == "NUMERIC" or attr_type == 'REAL'):
        return FloatField(label='%s' % attr_name)
    
    elif (str(attr_type).upper() == "INTEGER"):
        return IntegerField(label='%s' % attr_name)   
                        
    elif (str(attr_type).upper() ==  "STRING"):
        return CharField(label='%s' % attr_name)
    
    elif (type(attr_type) is list):
        boolean_attr = False
        for value in attr_type:
            if str(value).upper() == 'TRUE':
                boolean_attr = True
        
        if (len(attr_type) == 2 and boolean_attr):
            return BooleanField(label='%s' % attr_name, required=False)
        else:
            return ChoiceField(choices=[ (str(value), str(value)) for value in attr_type ])
        
    else:
        return None
    
def get_attr_names(list_attr):
    #data = load(open(file_path, 'rb'))
    #list_attr = data['attributes']
    attr_names = [] 
    for attr in list_attr:
        attr_names.append(attr[0])
    return attr_names

def evaluacion_validacion_cruzada(carpetas, clf, X, y):
    scores = cross_val_score(clf, X, y, cv=carpetas) #scores sera un vector de longitud igual a carpetas
    return scores.mean()

def pkl_from_arff(arff_file):
    data = load(arff_file)
    df = pd.DataFrame(data['data'])
    #df.columns(data['attributes'])
    dfY = df.ix[:,len(df.columns)-1:len(df.columns)].squeeze()
    dfX = df.ix[:,0:len(df.columns)-2]
    print dfX, 'CLASSSS ', dfY
    clf = RandomForestClassifier()
    clf.fit(dfX, dfY)
    temp_path = joblib.dump(clf, 'C:/Users/Cristian/workspace/MLPredictor/MLPredictorPlatform/models/%s.pkl' % data['relation'], compress=1)
    pkl_file = open(temp_path[0], 'rb')
    return pkl_file, evaluacion_validacion_cruzada(10, clf, dfX, dfY)

def pkl_test_prediction(arffFile, pklModel):
    data = load(arffFile)
    ### write the data to a temp file
    tup = mkstemp() # make a tmp file
    f = os.fdopen(tup[0], 'w') # open the tmp file for writing
    f.write(pklModel.read()) # write the tmp file
    f.close()
    ### return the path of the file
    filepath = tup[1] # get the filepath
    
    pkl = joblib.load(filepath)
    print pkl
    sample = None
    if data['data']:
        df = pd.DataFrame(data['data'])
        XSample = df.ix[0,0:len(df.columns)-2]
        
        XSample = asarray(XSample) 
        XSample = XSample.reshape(1,-1)
        
        test_prediction = asarray(XSample).reshape(1,-1)
        sample = XSample
    
        pred = pkl.predict(XSample)
        print 'PREDICTION ', pred
    else:
        zarray = zeros(shape=(1,len(data['attributes'])-1), order='F')
        
        test_prediction = pkl.predict(zarray)
        sample = zarray
        print 'PREDICTION ',test_prediction, pkl.predict_proba(zarray)*100
    
    dec_path = True
    try:
        print 'sample for ti', sample
        treeinterpreter.predict(pkl, sample)
    except:
        print 'Exception treeinterpreter'
        dec_path = False
    os.remove(filepath)
    
    return dec_path
    
def treeinterpreter_test_prediction(arffFile, pklModel):
    data = load(arffFile)
    ### write the data to a temp file
    tup = mkstemp() # make a tmp file
    f = os.fdopen(tup[0], 'w') # open the tmp file for writing
    f.write(pklModel.read()) # write the tmp file
    f.close()
    ### return the path of the file
    filepath = tup[1] # get the filepath
    
    pkl = joblib.load(filepath)
    print pkl
    if data['data']:
        df = pd.DataFrame(data['data'])
        XSample = df.ix[0,0:len(df.columns)-2]
        asarray(XSample).reshape(1,-1)
        treeinterpreter.predict(pkl, XSample)
        #pkl.predict(XSample)
    else:
        zarray = zeros(shape=(1,len(data['attributes'])-1), order='F')
        test_prediction = pkl.predict(zarray)
        treeinterpreter.predict(pkl, XSample)
        
        print test_prediction, pkl.predict_proba(zarray)*100

    os.remove(filepath)

def zero_to_nan(values):
    """Replace every 0 with 'nan' and return a copy."""
    return [float('nan') if x==0 else x for x in values]

def get_pie_plot(attr_names, contributions, yLabel):

    print 'BASE ',contributions
    contributions = contributions + abs(min(contributions))
    print 'ALL VALUES POSITIVE', contributions
    contributions = (contributions / np.sum(contributions))*100
    print 'PERCENTAGE ', contributions
    print type(contributions)
    
    plt.pie(contributions, labels=attr_names,
            autopct='%1.1f%%', shadow=True, startangle=90)
    plt.axis('equal')
    
    #plt.title('Programming language usage')
    savefig('C:/Users/Cristian/workspace/MLPredictor/MLPredictorPlatform/static/charts/grafico.png')
    #canvas = FigureCanvasAgg(plt)
    plt.close()


def get_plot(x, y, yLabel):
    print x,y
    
    width = .35
 
    y_pos = np.arange(len(x))
    plt.ylim([ min(y),max(y)])
    plt.bar(y_pos, y, align='center', alpha=0.5)
    plt.xticks(y_pos, x, rotation='vertical')
    plt.ylabel(yLabel)
    plt.gcf().tight_layout()
    #plt.title('Programming language usage')
    savefig('C:/Users/Cristian/workspace/MLPredictor/MLPredictorPlatform/static/charts/grafico.png')
    #canvas = FigureCanvasAgg(plt)
    plt.close()
