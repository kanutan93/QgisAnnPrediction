import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout
import numpy as np
from sklearn.preprocessing import Normalizer as normilizer
import pandas as pd


if __name__ == '__main__':
    dataframe = pd.read_csv("/home/dima/.qgis2/python/plugins/AnnPrediction/export.txt", delimiter=';', header=None)
    dataset = dataframe.values
    scale = normilizer()
    scaledDataset = scale.fit_transform(dataset[:dataframe.shape[0], 2:22])
    x_train = scaledDataset.transpose()[::2, :dataframe.shape[0]]
    y_train = scaledDataset.transpose()[1::2, :dataframe.shape[0]]
    x_test = scaledDataset.transpose()[18:19, :dataframe.shape[0]]
    y_test = scaledDataset.transpose()[19:20, :dataframe.shape[0]]


    model = Sequential()
    model.add(Dense(64, input_dim=dataframe.shape[0], activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(64, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(dataframe.shape[0], activation='sigmoid'))
    model.compile(loss='mean_squared_error', optimizer='adam')

    history = model.fit(x_train, y_train, epochs=20000, batch_size=128)
    score = model.predict(x_test, batch_size=128)
    print(score)
    print(y_test)