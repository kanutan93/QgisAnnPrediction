import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import SGD
import numpy as np
from sklearn.preprocessing import MinMaxScaler as normilizer
import pandas as pd
import csv


class NnKeras:
    def __init__(self, dataset, rowsCount, columnsCount, config):
        self.dataset = dataset
        self.normilizerTrain = normilizer()
        self.normilizerPredict = normilizer()
        self.rowsCount = rowsCount
        self.columnsCount = columnsCount
        self.config = config


    def train(self):
        normilizedDataSet = self.normilizerTrain.fit_transform(self.dataset)
        inputTrain = normilizedDataSet.transpose()[:self.columnsCount - 1, :self.rowsCount]
        outputTrain = normilizedDataSet.transpose()[1:self.columnsCount, :self.rowsCount]
        model = Sequential()
        model.add(Dense(self.config['neuronsPerLayer'], input_dim=self.rowsCount, activation=self.config['activationFunction']))
        model.add(Dropout(0.5))
        for i in range(self.config['hiddenLayers']):
            model.add(Dense(self.config['neuronsPerLayer'], activation=self.config['activationFunction']))
            model.add(Dropout(0.5))
        model.add(Dense(self.rowsCount, activation=self.config['activationFunction']))
        sgd = SGD(lr=self.config['learningRate'], decay=self.config['decay'], momentum=self.config['momentum'], nesterov=self.config['nesterov'])
        model.compile(loss='mean_squared_error', optimizer=sgd)
        model.fit(inputTrain, outputTrain, epochs=self.config['epochs'], batch_size=128)
        return model


    def predict(self, model, inputPredict):
        outputPredict = model.predict(inputPredict, batch_size=128)
        self.normilizerPredict.fit_transform(inputPredict)
        outputPredict = self.normilizerPredict.inverse_transform(outputPredict)
        return outputPredict

if __name__ == '__main__':

    data=[]
    with open("/home/dima/.qgis2/python/plugins/AnnPrediction/export.csv") as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            data.append(row)

    dataframe = pd.DataFrame(data=data[1:], columns=data[0])
    dataset = dataframe.values
    config = {
        'neuronsPerLayer': 64,
        'activationFunction': 'relu',
        'hiddenLayers': 5,
        'epochs': 500,
        'learningRate': 0.1,
        'decay': 1e-6,
        'momentum': 0.9,
        'nesterov': True
    }
    nnKeras = NnKeras(dataset, dataframe.shape[0], dataframe.shape[1], config)
    model = nnKeras.train()
    inputPredict = nnKeras.dataset.transpose()[nnKeras.columnsCount - 1:nnKeras.columnsCount, :nnKeras.rowsCount]# Last element etc 2005 year
    outputPredict = nnKeras.predict(model, inputPredict)
    print(inputPredict)
    print(outputPredict)
    outputDataframe = pd.DataFrame({
        "200601": outputPredict[0]
    })

    result = pd.concat([dataframe, outputDataframe], axis=1)
    print(result)

