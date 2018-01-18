# Machine Learning Platform for Clinical Support

This is a Django web application that allows users to query predictions, create new machine learning models from the dataset specification and manage them. 

It is able to train a machine learning model from a [ARFF](https://www.cs.waikato.ac.nz/ml/weka/arff.html) file describing the dataset. It creates a RandomForest classifier, which is ready to make predictions by entering input data via a dynamically generated form. The result of the prediction will show the probability of every class and a graph representing the influence of every input attribute data.

I developed it for academical purpose exclusively. In fact, it was my Bachelor's thesis.

Back in the day, I did not know about virtual envs. That is why this repository does not include a requirements.txt. My apologies for that.




