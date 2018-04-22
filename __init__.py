# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnnPrediction
                                 A QGIS plugin
 Ann prediction
                             -------------------
        begin                : 2018-04-12
        copyright            : (C) 2018 by d.morozov
        email                : kanutan93@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load AnnPrediction class from file AnnPrediction.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from core.ann_prediction import AnnPrediction
    return AnnPrediction(iface)
