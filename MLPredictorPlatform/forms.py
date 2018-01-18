#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from arff import load, BadLayout, BadDataFormat, BadAttributeType
from django.forms.fields import FloatField, IntegerField, CharField, ChoiceField,\
    BooleanField

from MLPredictorPlatform.utils import field_from_attr, pkl_test_prediction,\
    pkl_from_arff, treeinterpreter_test_prediction
from MLPredictorPlatform.models import Model
from django.contrib.admin.widgets import AdminDateWidget
from django.shortcuts import get_object_or_404
from arff import load
import datetime
from treeinterpreter import treeinterpreter




class LoginForm(forms.Form):
    
    error_css_class = 'alert alert-success'
    
    username = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=30)), label='Nombre de usuario')
    username.widget.attrs.update({'class' : 'form-control'})
    password = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label='Contraseña')
    password.widget.attrs.update({'class' : 'form-control'})
    def clean(self):
        user = authenticate(username=self.cleaned_data['username'], password=self.cleaned_data['password'])
        if user is None:
            raise forms.ValidationError("Usuario o contraseña no válido")
        else:
            if not user.is_active:
                raise forms.ValidationError("Su cuenta está pendiente de validación.")
             
class RegistrationForm(forms.Form):
               
    username = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=30)), label='Nombre de usuario')
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label='Contraseña')
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=dict(required=True, max_length=30, render_value=False)), label='Repita la contraseña')
    
    firstName = forms.CharField(widget=forms.TextInput(attrs=dict(required=True)), max_length=40, label='Nombre')
    lastName = forms.CharField(widget=forms.TextInput(attrs=dict(required=True)), max_length=80, label='Apellidos')
    
    invalid_email = {'invalid':'Dirección de correo no válida'}
    email = forms.EmailField(widget=forms.EmailInput(attrs=dict(required=True)), max_length=30, label="Correo electrónico", error_messages=invalid_email)
    
    username.widget.attrs.update({'class' : 'form-control'})
    password1.widget.attrs.update({'class' : 'form-control'})
    password2.widget.attrs.update({'class' : 'form-control'})
    firstName.widget.attrs.update({'class' : 'form-control'})
    lastName.widget.attrs.update({'class' : 'form-control'})
    email.widget.attrs.update({'class' : 'form-control', 'placeholder':'ejemplo@ejemplo.com'})

    '''
    mod_choices = ()
    for model in vis_models:
        mod_choices = mod_choices + ((model.name,model.name),)
    '''
    vis_models = Model.objects.filter(visible = True)
    if len(vis_models)>0:
        chosen_models = forms.ModelMultipleChoiceField(label='Seleccione los modelos que desea', queryset=vis_models, required=False) 
        chosen_models.widget.attrs.update({'id' : 'my-select'})
    #invalid_nif = {'min_length':'DNI o NIF no válido', 'max_length':'DNI o NIF no válido'}
    #nif = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=10)), min_length=9, max_length=10, label='DNI/NIF', error_messages=invalid_nif)
    
    #ROLES = ((1,'Médico'), (2,'Paciente'))
    #role = forms.CharField(widget=forms.Select(choices=ROLES))
    researcher = forms.BooleanField(widget=forms.CheckboxInput(attrs=dict(value=1)), label='¿Desea permisos para subir y gestionar nuevos modelos? ', required=False)
    
    def clean_username(self):
        try:
            user = User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
        raise forms.ValidationError("El nombre de usuario ya existe. Por favor, introduzca otro.")
 
    def clean(self):
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError("Las dos contraseñas no coinciden.")
        return self.cleaned_data
    
class ModelForm(forms.Form):
    def __init__(self, *args, **kwargs):
        attributes_path = kwargs.pop('attributes_path')
        super(ModelForm, self).__init__(*args, **kwargs)
        data = load(open(attributes_path, 'rb'))
        data['attributes'] = data['attributes'][0:len(data['attributes'])-1]
        print data['attributes']
        for attr in data['attributes']:
            
            attr_type = attr[1]
            attr_name = str(attr[0])
            
            '''
            field = field_from_attr(attr)
            if field is not None:
                self.fields['%s' % attr_name] = field
            '''
            
            if (str(attr_type).upper() == "NUMERIC" or attr_type == 'REAL'):
                self.fields['%s' % attr_name] = FloatField(widget=forms.NumberInput(attrs=dict(required=True)), required=True, label='%s' % attr_name)
                self.fields['%s' % attr_name].widget.attrs.update({'class' : 'form-control', 'placeholder':'Introduzca valor numérico'})
            elif (str(attr_type).upper() == "INTEGER"):
                self.fields['%s' % attr_name] = IntegerField(widget=forms.NumberInput(attrs=dict(required=True)), required=True,label='%s' % attr_name)   
                self.fields['%s' % attr_name].widget.attrs.update({'class' : 'form-control', 'placeholder':'Introduzca valor numérico'})                                
            elif (str(attr_type).upper() ==  "STRING"):
                self.fields['%s' % attr_name] = CharField(widget=forms.TextInput(attrs=dict(required=True)), required=True, label='%s' % attr_name)
                self.fields['%s' % attr_name].widget.attrs.update({'class' : 'form-control', 'placeholder':'Introduzca texto'})            
            elif (type(attr_type) is list):
                boolean_attr = False
                for value in attr_type:
                    if str(value).upper() == 'TRUE' or str(value).upper() == 'YES':
                        boolean_attr = True
                
                ##if (len(attr_type) == 2 and boolean_attr):
                if (len(attr_type) == 2):
                    #self.fields['%s' % attr_name] = BooleanField(label='%s' % attr_name)
                    self.fields['%s' % attr_name] = IntegerField(widget=forms.CheckboxInput(attrs=dict(value=1)), label='%s' % attr_name)
                    self.fields['%s' % attr_name].widget.attrs.update({'class' : ''})

                else:
                    self.fields['%s' % attr_name] = ChoiceField(choices=[ (str(value), str(value)) for value in attr_type ], required=True)
                    
class UploadModelForm(forms.Form):
    
    error_css_class = "alert alert-success"
    
    name = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=60)), label='Nombre del modelo')
    description = forms.CharField(widget=forms.Textarea(attrs=dict(required=True)), label = 'Descripción')
    date = forms.DateField(widget=AdminDateWidget(attrs=dict(required=True)), label = 'Fecha', required=True, initial=datetime.date.today())
    arffFile = forms.FileField(widget=forms.FileInput(attrs=dict(required=True)), label='Fichero ARFF')
    pklFile = forms.FileField(required=False,label='Fichero de modelo entrenado PKL')
    predictive_capacity = forms.FloatField(widget=forms.NumberInput(attrs=dict(min=0, max=100)), required=False, label='Capacidad predictiva del modelo entrenado en % (dejar vacío si no proporciona fichero PKL)')
    visible = forms.BooleanField(widget=forms.CheckboxInput(attrs=dict(value=1, required=False)), label='¿Desea que los demás usuarios puedan realizar consultas a su modelo?:', required=False)
    
    name.widget.attrs.update({'class' : 'form-control'})
    description.widget.attrs.update({'class' : 'form-control', 'rows' : '3'})
    date.widget.attrs.update({'id' : 'datepicker', 'class':'form-control'})
    arffFile.widget.attrs.update({'class' : 'form-control'})
    pklFile.widget.attrs.update({'class' : 'form-control'})
    predictive_capacity.widget.attrs.update({'class' : 'form-control'})
    def clean(self):
        pkl = self.cleaned_data.get("pklFile", False)
        arff = self.cleaned_data.get("arffFile", False)
        pc = self.cleaned_data['predictive_capacity']
        try:
            data = load(arff)
            print data['attributes']
            print data['data']
        
        except BadDataFormat:
            raise forms.ValidationError('ARFF mal formado. Los datos no se corresponden con los atributos.')
        except BadLayout:
            raise forms.ValidationError('ARFF mal formado. Asegúrese de que el archivo sigue la notación de ARFF.')
        except BadAttributeType:
            raise forms.ValidationError('ARFF mal formado. Asegúrese de que el nombre de los atributos no contenga espacios y su tipo sea correcto.')
        except:
            raise forms.ValidationError('ARFF mal formado.')
        if not data['attributes']:
            raise forms.ValidationError('Asegúrese de que el ARFF contiene los atributos del conjunto de datos introducidos por la notación @attribute')
        elif not pkl and not data['data']:
            raise forms.ValidationError('Asegúrese de que el ARFF contiene las muestras del conjunto de datos introducidos por la notación @data')
        if not len(data['attributes'][len(data['attributes'])-1][1]) == 2:
            raise forms.ValidationError('La clase del conjunto de datos sólo puede tener dos valores')
        if not pkl:
            try:
                pkl_from_arff(arff)
            except:
                raise forms.ValidationError('Asegúrese de que el conjunto de datos no contiene valores perdidos y que los atributos estan codificados numéricamente')
        
            '''
        is_arff = str(arff).endswith('.arff')
        
        arff_lower = arff.read().lower()
        
        has_attr = '@attribute' in arff_lower
        has_rel = '@relation' in arff_lower
        has_data = '@data' in arff_lower
        
        print arff_lower
        print has_rel,has_attr,has_data
        print is_arff, 'es arff'
        print pkl
        
        if not is_arff :
            if not str(arff).endswith('.txt'):
                print arff, pkl, pc, str(arff).endswith('.txt')
                raise forms.ValidationError("Por favor, introduce un fichero ARFF con extensión .arff")
        elif not has_rel or not has_attr:
            raise forms.ValidationError("Fichero ARFF no válido. Asegúrese de que contenga la notación @relation y @attribute")
        if has_data is False and pkl is None:
                raise forms.ValidationError("Asegúrese de que el ARFF contenga la notación @data con los valores de las muestras del conjunto de datos")            
            '''          
        if pkl is not None:
            if str(pkl).endswith('.pkl') is False:
                raise forms.ValidationError("Por favor, introduce un fichero de modelo con extensión .pkl")
            elif pc is None:
                raise forms.ValidationError("Introduce la capacidad predictiva del modelo entrenado")
            elif arff is None:
                raise forms.ValidationError("Introduce el fichero ARFF con el nombre (@relation) y atributos (@attribute) del conjunto de datos")
            if arff is not None:
                dec_path = True
                try:
                    dec_path = pkl_test_prediction(arff, pkl)
                except:
                    raise forms.ValidationError("ARFF y PKL introducidos no compatibles.")
                
                if(not dec_path):
                    raise forms.ValidationError("El PKL debe contener el modelo entrenado con un algoritmo de árboles de decisión.")
        
                '''
                except:
                    raise forms.ValidationError("El PKL debe contener el modelo entrenado con un algoritmo de árboles de decisión.")
                '''
        else:
            try:
                pkl_test_prediction(arff, pkl)
            except:
                raise forms.ValidationError("El PKL introducido no es compatible con el ARFF almacenado")
        return self.cleaned_data
    
    
class EditModelForm(forms.Form):
       
    def __init__(self, *args, **kwargs):
        self.model_id = kwargs.pop('mdl_id')
        super(EditModelForm, self).__init__(*args, **kwargs)
        
        model = get_object_or_404(Model, pk=self.model_id)
        
        self.fields['name'] = forms.CharField(widget=forms.TextInput(attrs=dict(required=True, max_length=60)), label='Nombre del modelo', initial=model.name)
        self.fields['description'] = forms.CharField(widget=forms.Textarea(attrs=dict(required=True)), label = 'Descripción', initial = model.description)
        self.fields['date'] = forms.DateField(widget=AdminDateWidget(attrs=dict(required=True)), label = 'Fecha', required=True, initial = model.date)
        #self.fields['visible'] = forms.BooleanField(widget=forms.CheckboxInput(attrs=dict(value=1, required=False)), label='¿Desea que los demas usuarios puedan realizar consultas a su modelo?', required=False, initial = model.id)
        self.fields['arffFile'] = forms.FileField(required=False, label='Fichero ARFF')
        self.fields['pklFile'] = forms.FileField(required=False,label='Fichero de modelo entrenado PKL')
        self.fields['predictive_capacity'] = forms.FloatField(widget=forms.NumberInput(attrs=dict(min=0, max=100)), required=False, label='Capacidad predictiva del modelo entrenado en % (dejar vacío si no proporciona fichero PKL)')

        self.fields['name'].widget.attrs.update({'class' : 'form-control'})
        self.fields['description'].widget.attrs.update({'class' : 'form-control', 'rows' : '3'})
        self.fields['date'].widget.attrs.update({'id' : 'datepicker', 'class':'form-control'})
        self.fields['arffFile'].widget.attrs.update({'class' : 'form-control'})
        self.fields['pklFile'].widget.attrs.update({'class' : 'form-control'})
        self.fields['predictive_capacity'].widget.attrs.update({'class' : 'form-control'})
    def clean(self):
        
        #super(EditModelForm, self).__init__(*args, **kwargs)
        
        model = get_object_or_404(Model, pk=self.model_id)
        pkl = self.cleaned_data.get("pklFile", False)
        arff = self.cleaned_data.get("arffFile", False)
        pc = self.cleaned_data['predictive_capacity']
        if arff is not None:
            try:
                data = load(arff)
                print data['attributes']
                print data['data']
            except:
                raise forms.ValidationError('Archivo ARFF incorrecto. Asegurese que incluye el nombre del conjunto de datos con la notación @relation y los atributos con @attribute.')
            if not data['attributes']:
                raise forms.ValidationError('Asegúrese de que el ARFF contiene los atributos del conjunto de datos introducidos por la notación @attribute')
            
            elif not pkl and not data['data']:
                raise forms.ValidationError('Asegúrese de que el ARFF contiene las muestras del conjunto de datos introducidos por la notación @data')
            elif not len(data['attributes'][len(data['attributes'])-1][1]) == 2:
                raise forms.ValidationError('La clase del conjunto de datos solo puede tener dos valores')
            if not pkl:
                try:
                    pkl_from_arff(arff)
                except:
                    raise forms.ValidationError('Asegúrese de que el conjunto de datos no contiene valores perdidos y que los atributos estan codificados numéricamente')
            
                 
        if pc is not None and pkl is None:
            raise forms.ValidationError("Debe introducir un modelo entrenado para cambiar la capacidad predictiva")
        
        
        if pkl is not None:
            if str(pkl).endswith('.pkl') is False:
                raise forms.ValidationError("Por favor, introduce un fichero de modelo con extensión .pkl")
            if pc is None:
                raise forms.ValidationError("Introduce la capacidad predictiva del modelo entrenado")
            #Intentar hacer prediccion con 
            if arff is not None:
                dec_path = True
                try:
                    dec_path = pkl_test_prediction(arff, pkl)
                except:
                    raise forms.ValidationError("ARFF y PKL introducidos no compatibles.")
                if(not dec_path):
                    raise forms.ValidationError("El PKL debe contener el modelo entrenado con un algoritmo de árboles de decisión.")
        
                
            else:
                try:
                    pkl_test_prediction(model.attributesFile, pkl)
                except:
                    raise forms.ValidationError("El PKL introducido no es compatible con el ARFF almacenado")
        return self.cleaned_data
   
class SelectModelsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(SelectModelsForm, self).__init__(*args, **kwargs)
        vis_models = Model.objects.filter(visible = True)
        #user = get_object_or_404(User, pk=self.user)
        print 'all vis mod ', vis_models
        model_to_choose =  vis_models.exclude(uploader = self.user)
        '''
        for model in uploaded_models:
            if model in vis_models:
                vis_models.
        '''
        user_models = Model.objects.filter(users = self.user)
        self.fields['chosen_models'] = forms.ModelMultipleChoiceField(label='Seleccione los modelos que desea', queryset=model_to_choose, initial=user_models, required=False) 
        self.fields['chosen_models'].widget.attrs.update({'id' : 'my-select', 'class':'form-control'})
    def clean(self):
        return self.cleaned_data