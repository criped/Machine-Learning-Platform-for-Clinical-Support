from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
# Create your models here.

@python_2_unicode_compatible
class Model(models.Model):
    name = models.CharField(max_length=400, null=False)
    date = models.DateField()
    users = models.ManyToManyField(User, blank=True, related_name='assigned_users')
    uploader = models.ForeignKey(User, null=True, blank=True)
    modelFile = models.FileField(upload_to='C:/Users/Cristian/workspace/MLPredictor/MLPredictorPlatform/models/PKL', null=True, blank=True)
    attributesFile = models.FileField(upload_to='C:/Users/Cristian/workspace/MLPredictor/MLPredictorPlatform/models/attributes')
    description = models.TextField(null=True, blank=True)
    visible = models.BooleanField()
    predictive_capacity = models.FloatField(null=True, blank=True, validators = [MinValueValidator(0), MaxValueValidator(100)])
    def __str__(self):
        return self.name
