# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnnPrediction
                                 A QGIS plugin
 Ann prediction
                              -------------------
        begin                : 2018-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2018 by d.morozov
        email                : kanutan93@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QVariant
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QTableWidgetItem
# Initialize Qt resources from file resources.py
import AnnPrediction.gui.resources
# Import the code for the DockWidget
from AnnPrediction.gui.ann_prediction_dockwidget import AnnPredictionDockWidget
import os.path
from qgis.core import QgsCategorizedSymbolRendererV2, \
    QgsRendererCategoryV2, \
    QgsSimpleFillSymbolLayerV2, \
    QgsFeature, \
    QgsVectorLayer, \
    QgsField, \
    QgsGeometry, \
    QgsPoint, \
    QgsMapLayerRegistry, \
    QgsCoordinateReferenceSystem, \
    QgsSymbolV2,\
    QgsStyleV2, \
    QgsGraduatedSymbolRendererV2
import csv
import numpy as np
import pandas as pd
from AnnPrediction.nn.nn_keras import NnKeras


class AnnPrediction:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AnnPrediction_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Ann prediction')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'AnnPrediction')
        self.toolbar.setObjectName(u'AnnPrediction')

        #print "** INITIALIZING AnnPrediction"

        self.pluginIsActive = False
        self.dockwidget = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('AnnPrediction', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/AnnPrediction/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Ann prediction'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING AnnPrediction"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD AnnPrediction"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Ann prediction'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING AnnPrediction"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = AnnPredictionDockWidget()

            self.addConnects()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.dockwidget)
            self.dockwidget.show()


    def addConnects(self):
        self.dockwidget.addVectorLayersButton.clicked.connect(self.showDialog)
        self.dockwidget.exportToCSV.clicked.connect(self.exportToCSV)
        self.dockwidget.train.clicked.connect(self.train)
        self.dockwidget.predict.clicked.connect(self.predict)
        self.dockwidget.activationFunction.addItems(['relu', 'sigmoid', 'tanh'])

    def showDialog(self):
        self.predictedIdx = 0
        filename = QFileDialog.getOpenFileName(caption='Open file', directory='/home')
        self.layer = self.iface.addVectorLayer(filename, "test", "ogr")
        if not self.layer:
            print("Layer failed to load!")
        self.provider = self.layer.dataProvider()
        self.createTable(self.provider)
        self.createLayersFromData(self.fields, self.data)


    def exportToCSV(self):
        if(self.data != None):
            field_names = [field for field in self.fields.values()]
            with open('/home/dima/.qgis2/python/plugins/AnnPrediction/export.csv', 'wb') as f:
                print(f)
                dw = csv.DictWriter(f, field_names, delimiter=';')
                dw.writeheader()
                revertedData = np.asfarray(self.data, dtype=np.float32).transpose().tolist()
                for row in revertedData:
                    dw.writerow(dict(zip(field_names, row)))

    def train(self):
        revertedData = np.asfarray(self.data, dtype=np.float32).transpose().tolist()
        field_names = [field for field in self.fields.values()]
        self.dataframe = pd.DataFrame(data=revertedData, columns=field_names)
        dataset = self.dataframe.values
        config = {
            'neuronsPerLayer': 64,
            'activationFunction': self.dockwidget.activationFunction.currentText(),
            'hiddenLayers': self.dockwidget.hiddenLayers.value(),
            'epochs': self.dockwidget.epochs.value(),
            'learningRate': self.dockwidget.learningRate.value(),
            'decay': 1e-6,
            'momentum': self.dockwidget.momentum.value(),
            'nesterov': True
        }
        print(config)
        self.nnKeras = NnKeras(dataset, self.dataframe.shape[0], self.dataframe.shape[1], config)
        self.model = self.nnKeras.train()
        print('trained')


    def predict(self):
        inputPredict = self.nnKeras.dataset.transpose()[self.nnKeras.columnsCount - 1:self.nnKeras.columnsCount,:self.nnKeras.rowsCount]  # Last element etc 2005 year
        outputPredict = self.nnKeras.predict(self.model, inputPredict)
        self.data = np.insert(self.data, len(self.data), outputPredict, axis=0).tolist()
        self.addPredictToTable(self.provider)
        self.createPredictedLayer(self.data)
        newFields = self.fields.values()
        newFields.append('predicted-' + str(self.predictedIdx))
        self.fields = self.readFields(newFields)
        self.predictedIdx += 1

    def createPredictedLayer(self, data):
        latIdx = 0
        lonIdx = 1
        currentYearIdx = len(self.fields)
        s = QSettings()
        default_value = s.value("/Projections/defaultBehaviour")
        s.setValue("/Projections/defaultBehaviour", "useProject")

        style = QgsStyleV2().defaultStyle()
        defaultColorRampNames = style.colorRampNames()
        ramp = style.colorRamp(defaultColorRampNames[22])  # spectral
        yearLayer = QgsVectorLayer("Point", 'predicted-' + str(self.predictedIdx), "memory")
        crs = yearLayer.crs()
        crs.createFromId(4326)
        yearLayer.setCrs(crs)
        yearProvider = yearLayer.dataProvider()
        yearLayer.startEditing()

        yearProvider.addAttributes([
            QgsField("GID_LAT", QVariant.Double),
            QgsField("GID_LON", QVariant.Double),
            QgsField("predicted-" + str(self.predictedIdx), QVariant.Double)
        ])
        features = []
        for j in range(len(data[0])):
            feature = QgsFeature()
            feature.setGeometry(QgsGeometry.fromPoint(QgsPoint(data[lonIdx][j], data[latIdx][j])))
            feature.setAttributes([data[latIdx][j], data[lonIdx][j], data[currentYearIdx][j]])
            features.append(feature)
        yearProvider.addFeatures(features)
        yearLayer.commitChanges()
        QgsMapLayerRegistry.instance().addMapLayer(yearLayer)
        self.categorizeLayer(yearLayer, 'predicted-' + str(self.predictedIdx), ramp, len(data[0]))

    def createLayersFromData(self, fields, data):
        latIdx = 0
        lonIdx = 1
        currentYearIdx = 2

        s = QSettings()
        default_value = s.value("/Projections/defaultBehaviour")
        s.setValue("/Projections/defaultBehaviour", "useProject")

        style = QgsStyleV2().defaultStyle()
        defaultColorRampNames = style.colorRampNames()
        ramp = style.colorRamp(defaultColorRampNames[22]) #spectral

        for field in self.fields.values()[2::5]:
            yearLayer = QgsVectorLayer("Point", field, "memory")
            crs = yearLayer.crs()
            crs.createFromId(4326)
            yearLayer.setCrs(crs)
            yearProvider = yearLayer.dataProvider()
            yearLayer.startEditing()

            yearProvider.addAttributes([
                QgsField("GID_LAT", QVariant.Double),
                QgsField("GID_LON", QVariant.Double),
                QgsField(field, QVariant.Double)
            ])
            features = []
            for j in range(len(data[0])):
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPoint(QgsPoint(data[lonIdx][j], data[latIdx][j])))
                feature.setAttributes([data[latIdx][j], data[lonIdx][j], data[currentYearIdx][j]])
                features.append(feature)
            yearProvider.addFeatures(features)
            yearLayer.commitChanges()
            QgsMapLayerRegistry.instance().addMapLayer(yearLayer)
            self.categorizeLayer(yearLayer, field, ramp, len(data[0]))

            currentYearIdx += 1

        s.setValue("/Projections/defaultBehaviour", default_value)



    def categorizeLayer(self, layer, fieldName, ramp, numberOfClasses):
        renderer = QgsGraduatedSymbolRendererV2()
        renderer.setClassAttribute(fieldName)
        renderer.setMode(QgsGraduatedSymbolRendererV2.EqualInterval)
        renderer.updateClasses(layer, QgsGraduatedSymbolRendererV2.EqualInterval, numberOfClasses)
        renderer.updateColorRamp(ramp, inverted=True)
        layer.setRendererV2(renderer)
        layer.triggerRepaint()

    def addPredictToTable(self, provider):
        self.dockwidget.attributeTable.clear()
        self.dockwidget.attributeTable.setColumnCount(len(self.fields) + 1)
        self.dockwidget.attributeTable.setRowCount(provider.featureCount())
        header = []
        for i in self.fields.values():
            header.append(i)
        header.append('predicted-' + str(self.predictedIdx))
        self.dockwidget.attributeTable.setHorizontalHeaderLabels(header)
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                self.dockwidget.attributeTable.setItem(j, i, QTableWidgetItem(unicode(self.data[i][j] or 'NULL')))

    def createTable(self, provider):
        self.fields = self.readFields([field.name() for field in provider.fields()])
        self.data = self.readData(self.fields, provider)
        self.dockwidget.attributeTable.clear()
        self.dockwidget.attributeTable.setColumnCount(len(self.fields))
        self.dockwidget.attributeTable.setRowCount(provider.featureCount())
        header = []
        for i in self.fields.values():
            header.append(i)
        self.dockwidget.attributeTable.setHorizontalHeaderLabels(header)
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                self.dockwidget.attributeTable.setItem(j, i, QTableWidgetItem(unicode(self.data[i][j] or 'NULL')))


    def readFields(self, providerFields):
        fieldsDict = {}
        i = 0
        for field in providerFields:
            fieldsDict.update({i: field})
            i += 1
        return fieldsDict

    def readData(self, fields, provider):
        data = []
        for i in range(len(fields)):
            data += [[]]
        for feat in provider.getFeatures():
            attrs = feat.attributes()
            for i in range(len(attrs)):
                data[i] += [attrs[i]]
        return data