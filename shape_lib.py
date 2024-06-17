import glob

import alt.file
import os
from osgeo import ogr, osr
from alt.dict_ import dict_

def read(shp_file, encoding='utf-8'):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    os.environ['SHAPE_ENCODING'] = encoding
    shp = driver.Open(shp_file)
    layer = shp.GetLayer()
    layer_def = layer.GetLayerDefn()
    attrs = [layer_def.GetFieldDefn(i).GetName().lower() for i in range(0, layer_def.GetFieldCount())]

    data = []
    for ifeature in range(layer.GetFeatureCount()):
        row = dict_()
        feature = layer.GetFeature(ifeature)
        for iattr, attr in enumerate(attrs):
            row[attr] = feature.GetField(iattr)
        row.geom = feature.GetGeometryRef().ExportToJson()
        data.append(row)

    sr = layer.GetSpatialRef()
    proj4 = sr.ExportToProj4()

    return data, proj4

def write(shp_file, data):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(shp_file):
        for file in glob.glob(shp_file.replace('.shp','.*')):
            alt.file.delete(file)
    shp = driver.CreateDataSource(shp_file)

    sr = osr.SpatialReference()
    sr.ImportFromEPSG(4326)
    layer = shp.CreateLayer('layer', sr, ogr.wkbMultiPolygon, options=['ENCODING=CP1251'])
    for attr in data[0].keys():
        if attr == 'polys':
            continue
        fd = ogr.FieldDefn(attr, ogr.OFTString)
        fd.SetWidth(254)
        layer.CreateField(fd)
    ld = layer.GetLayerDefn()

    for irow, row in enumerate(data):
        feature = ogr.Feature(ld)
        feature.SetFID(irow)
        feature['name'] = row.name
        feature['region'] = row.region
        feature['area'] = row.area
        multi_geom = ogr.Geometry(ogr.wkbMultiPolygon)
        for poly in row.polys:
            poly_geom = ogr.Geometry(ogr.wkbPolygon)
            for ring in poly:
                ring_geom = ogr.Geometry(ogr.wkbLinearRing)
                for x, y in ring:
                    ring_geom.AddPoint(x, y)
                poly_geom.AddGeometry(ring_geom)
            multi_geom.AddGeometry(poly_geom)
        feature.SetGeometry(multi_geom)
        layer.CreateFeature(feature)

    del shp