import arff as ar
from django.shortcuts import get_object_or_404



data = ar.load(open('./media/arffTest.txt', 'rb'))
#print(data)
for row in data['attributes']:
    if type(row[1]) is list:
        print(row[1])
    