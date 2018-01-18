#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.shortcuts import render, get_list_or_404, get_object_or_404
from django.http import HttpResponseRedirect

from django.contrib.auth import authenticate, login
from django.contrib.auth.views import logout
from django.views.decorators.csrf import csrf_protect
from MLPredictorPlatform.forms import RegistrationForm, LoginForm, ModelForm,\
    UploadModelForm, SelectModelsForm, EditModelForm
from django.contrib.auth.models import User, Group
from MLPredictorPlatform.models import Model
from django.contrib.auth.decorators import login_required
from django.conf.global_settings import LOGIN_URL
from sklearn.externals import joblib
from arff import load
from django.http.response import HttpResponseBadRequest
from numpy import asarray
import numpy as np
from django.utils.datastructures import MultiValueDictKeyError
import pandas as pd
from MLPredictorPlatform.utils import pkl_from_arff, get_plot, get_pie_plot
from MLPredictorPlatform.utils import pkl_test_prediction
from django.core.files import File
from treeinterpreter import treeinterpreter
from django.contrib import messages


# Create your views here.

def login_user(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LoginForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            
            if user is not None:
                if user.is_active:
                    print("User is valid, active and authenticated")
                    login(request, user)
                    return HttpResponseRedirect('/MLPredictorPlatform/modelos')
                else:
                    print("The password is valid, but the account has been disabled!")
                    
            else:
                print ("The username or password were incorrect.")
        else:
            print("The form is invalid")
            # redirect to a new URL:

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

@csrf_protect
def register(request):
    if request.method == 'POST':
        
        form = RegistrationForm(request.POST)
        if form.is_valid():
            userCreated = User.objects.create( 
                    username=form.cleaned_data['username'],
                    first_name = form.cleaned_data['firstName'],
                    last_name = form.cleaned_data['lastName'],
                    email=form.cleaned_data['email'],
                    is_active = False
                )  
            userCreated.set_password(form.cleaned_data['password1'])
            userCreated.save()
            if userCreated is not None:
                if int(form.cleaned_data['researcher'])==1:
                
                    g = Group.objects.get(name='Researchers')
                    g.user_set.add(userCreated)
            
            chosen_models = form.cleaned_data['chosen_models']
            if (len(chosen_models)>0):
                for model_name in chosen_models:
                    model = Model.objects.get(name=model_name)
                    model.users.add(userCreated)
            return HttpResponseRedirect('./completado')
    else:
        form = RegistrationForm()
    return render(request, 'registration.html', {'form': form})


def register_success(request):
    return render(request, 'registration_success.html')

@login_required(redirect_field_name=None)
def index(request):
    user = request.user
    
    user_models = Model.objects.filter(users = user)
    uploaded_models = Model.objects.filter(uploader__id=user.id)
    
    is_researcher = user.groups.filter(name='Researchers').exists()
    return render(request, 'user_main.html', {'user_models': user_models, 'user':user, 'uploaded_models':uploaded_models, 'is_researcher':is_researcher})

@login_required(redirect_field_name=None)
def logout_view(request):
    logout(request)
    messages.add_message(request, messages.INFO, "Sesión cerrada correctamente.")                    
    return HttpResponseRedirect('/MLPredictorPlatform/login')

@login_required(redirect_field_name=None)
def model_view(request, model_id):
    if request.method == 'GET':
        model = get_object_or_404(Model, pk=model_id)
        form = ModelForm(attributes_path = model.attributesFile.path)
        return render(request, 'model_template.html', {'form': form, 'model_name':model.name})

@login_required(redirect_field_name=None)   
def model_result(request, model_id):
    model = get_object_or_404(Model, pk=model_id)
    pkl_path = model.modelFile.path
    if '.pkl' in str(pkl_path).lower():
        
        attr_path = model.attributesFile.path
        #print attr_path, pkl_path
        data = load(open(str(attr_path), 'rb'))
        list_attr = data['attributes']
        
        cls = list_attr[len(list_attr)-1][0]
        list_attr = list_attr[0:len(list_attr)-1]
        
        req_sample = []
        attr_names = []
        
        for attr in list_attr:
            attr_names.append(attr[0])
            
            sample_feat = request.GET.get('%s' % attr[0], False)
            if sample_feat is not False:
                req_sample.append(sample_feat)
            elif (type(attr[1]) is list and len(attr[1]) == 2):
                req_sample.append(0)

        print req_sample
        if(len(req_sample)==len(list_attr)): 
            clf = joblib.load(pkl_path) 
            
            np_sample = asarray(req_sample) 
            np_sample = np_sample.reshape(1,-1)
            prediction=clf.predict(np_sample)
            
            proba = np.amax(clf.predict_proba(np_sample))*100
            pred, bias, contributions = treeinterpreter.predict(clf, np_sample)
            print "Prediction", pred
            print "Bias (trainset prior)", bias
            print "Feature contributions:"
            
            contrib = []
            for c, feature in zip(contributions[0], attr_names):
                contrib.append(c[np.argmax(pred)])
                print feature, c
            
            #print prediction[0]
            get_pie_plot(tuple(attr_names), contrib, 'Contribucion')
            
            #temp_path = get_plotTest(tuple(attr_names), contrib, 'Contribucion')
            
            return render(request, 'model_result.html', {'prediction_value': (prediction[0]), 'class': cls, 'proba':proba})
        else: 
            return HttpResponseBadRequest("Faltan valores en la muestra a predecir")
        
@login_required(redirect_field_name=None)   
def upload_model(request):
    title = None
    if request.method == 'POST':
        form = UploadModelForm(request.POST, request.FILES)
        if form.is_valid():
            
            form_pkl_file = None
            form_arff_file = request.FILES['arffFile']
            pc = form.cleaned_data['predictive_capacity']
            form_name = form.cleaned_data['name']
            try: 
                request.FILES['pklFile']
            except MultiValueDictKeyError:
                print 'there is no pkl file'
                try:
                    pkl_created, pc_score = pkl_from_arff(form_arff_file)
                    pc = round(pc_score*100,2)
                    form_pkl_file = File(pkl_created)
                    print pkl_created, form_pkl_file
                except ValueError:
                    return HttpResponseBadRequest("Por favor, introduzca un conjunto de datos sin valores perdidos")
            else:
                form_pkl_file = request.FILES['pklFile'] 
                     
            created_model = Model.objects.create(
                name = form_name,
                date = form.cleaned_data['date'],
                description = form.cleaned_data['description'],
                modelFile = form_pkl_file,
                attributesFile = form_arff_file,
                visible = form.cleaned_data['visible'],
                predictive_capacity = pc,
                uploader = request.user
            )
            messages.add_message(request, messages.INFO, "Modelo %s creado correctamente." % created_model.name)                    
                
            return HttpResponseRedirect('./')
    else:
        user = request.user
        if user.groups.filter(name='Researchers').exists():
            form = UploadModelForm()
            title = 'Subir nuevo modelo'
        else:
            return HttpResponseRedirect('./')
    return render(request, 'upload_model_template.html', {'form': form, 'title':title})


@login_required(redirect_field_name=None)   
def edit_model(request, model_id):
    title = None
    
    if not request.user == get_object_or_404(Model, pk=model_id).uploader:
        return HttpResponseRedirect('../')
    
    if request.method == 'POST':
        form = EditModelForm(request.POST, request.FILES, mdl_id=model_id)
        if form.is_valid():
            
            form_pkl_file = None
            form_arff_file = None
            pc = form.cleaned_data['predictive_capacity']
            form_name = form.cleaned_data['name']
            
            model = get_object_or_404(Model, pk=model_id)               
            
            
            try: 
                form_arff_file = request.FILES['arffFile']
            except MultiValueDictKeyError:
                print 'there is no arff file'
                
            else:
                form_arff_file = request.FILES['arffFile']
            
            
            try: 
                request.FILES['pklFile']
            except MultiValueDictKeyError:
                print 'there is no pkl file'
                
            else:
                form_pkl_file = request.FILES['pklFile']
                
                
            if form_pkl_file is None and form_arff_file is not None:
                pkl_created, pc_score = pkl_from_arff(form_arff_file)
                pc = round(pc_score*100,2)
                form_pkl_file = File(pkl_created)
                model.modelFile = form_pkl_file 
                model.attributesFile = form_arff_file
                model.save()
                print pkl_created, form_pkl_file
         
            if form_pkl_file is not None and form_arff_file is not None: 
                model.modelFile = form_pkl_file
                model.attributesFile = form_arff_file
                model.save()
                #created_model.modelFile.save(File(form_pkl_file))
                #created_model.predictive_capacity.save()
                
            if form_pkl_file is not None and form_arff_file is None: 
                model.modelFile = form_pkl_file
                model.save()
            
            
            Model.objects.filter(pk=model_id).update(name = form_name,
                date = form.cleaned_data['date'],
                description = form.cleaned_data['description'],
                #visible = form.cleaned_data['visible'],
                )
            if pc is not None:
                Model.objects.filter(pk=model_id).update(predictive_capacity = pc)
            
            '''
            modelFile = form_pkl_file,
            attributesFile = form_arff_file,
            '''
            messages.add_message(request, messages.INFO, "Modelo %s modificado correctamente." % model.name)                    
            return HttpResponseRedirect('../')
    else:
        user = request.user
        if user.groups.filter(name='Researchers').exists():
            form = EditModelForm(mdl_id = model_id)
            model = get_object_or_404(Model, pk=model_id) 
            title = 'Modificar %s' % model.name
        else:
            return HttpResponseRedirect('./')
    return render(request, 'upload_model_template.html', {'form': form, 'title':title})



@login_required(redirect_field_name=None)
def delete_model(request, model_id):
    model = get_object_or_404(Model, pk=model_id)
    user = request.user
    if model.uploader == user:
        model.delete()  
        messages.add_message(request, messages.INFO, "Modelo %s borrado correctamente." % model.name)
    return HttpResponseRedirect('/MLPredictorPlatform/modelos')

@login_required(redirect_field_name=None)
def change_visibility(request, model_id):
    model = get_object_or_404(Model, pk=model_id)
    user = request.user
    if model.uploader == user:
        model.visible = not model.visible
        model.save(force_update=True)
        if model.visible:
            messages.add_message(request, messages.INFO, "El modelo %s es visible para para el resto de usuarios ahora." % model.name)
        else:
            messages.add_message(request, messages.INFO, "El modelo %s no es visible para el resto de usuarios ahora." % model.name)
    return HttpResponseRedirect('/MLPredictorPlatform/modelos')

@login_required(redirect_field_name=None)
def select_models(request):
    if request.method == 'POST':
        form = SelectModelsForm(request.POST, user = request.user)
        #vis_models = Model.objects.filter(visible = True)
        if form.is_valid():
            user_models = Model.objects.filter(users = request.user)
            chosen_models = form.cleaned_data['chosen_models']
            print 'user_models:', user_models
            print 'chosen_models:', chosen_models
            
            for model in chosen_models:
                if model not in user_models:
                    model_to_add = Model.objects.get(pk=model.id)
                    model_to_add.users.add(request.user)
            for model in user_models:
                if model not in chosen_models:
                    model_to_remove = Model.objects.get(pk=model.id)                    
                    model_to_remove.users.remove(request.user)
                    
            
            messages.add_message(request, messages.INFO, "Selección de modelos realizada correctamente")
            return HttpResponseRedirect('./')
    else:
        form = SelectModelsForm(user=request.user)
    return render(request, 'select_models.html', {'form': form})

def index_home(request):
    if request.user:
        return HttpResponseRedirect('/MLPredictorPlatform/modelos')
    else:       
        return HttpResponseRedirect('/MLPredictorPlatform/login')
