import alt.file
import osr, os
from osgeo import ogr
from osgeo import gdal
from alt.dict_ import dict_

def write(shpfile, type, data, columns, proj='longlat'):
    
    driver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(shpfile):
        alt.file.delete(shpfile)
        alt.file.delete(shpfile.replace('.shp','.shx'))
        alt.file.delete(shpfile.replace('.shp','.proj'))
        alt.file.delete(shpfile.replace('.shp','.dbf'))
    shp = driver.CreateDataSource(shpfile)

    sr = osr.SpatialReference()
    sr.ImportFromProj4('+proj=%s +datum=WGS84 +no_defs' % proj)
    
    if type=='POINT':
        ogr_type = ogr.wkbPoint
    elif type=='LINE':
        ogr_type = ogr.wkbLineString
    elif type=='POLY':
        ogr_type = ogr.wkbPolygon
    else:
        raise Exception('Unknown type', type)
    layer = shp.CreateLayer('layer', sr, ogr_type, options = ['ENCODING=CP1251'])
    ld = layer.GetLayerDefn()

    for i, column in enumerate(columns):
        FieldDefinition = ogr.FieldDefn(column, ogr.OFTString)
        n = 1
        for row in data:
            n = max(len(row[i+1]), n)
        n = min(n, 254)
        FieldDefinition.SetWidth(n)
        layer.CreateField (FieldDefinition)
    
    for irow, row in enumerate(data):

        feature = ogr.Feature(ld)
        feature.SetFID(irow)
        for column, value in zip(columns, row[1:]):
            feature[column] = value[:254]

        geom = ogr.CreateGeometryFromWkt(row[0])
        feature.SetGeometry(geom)
        layer.CreateFeature(feature)
            
    shp.Destroy()
        
def read(shp_file, encoding='utf-8'):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    os.environ['SHAPE_ENCODING'] = encoding
    shp = driver.Open(shp_file)
    layer = shp.GetLayer()
    layer_def = layer.GetLayerDefn()
    attrs = [layer_def.GetFieldDefn(i).GetName() for i in range(0, layer_def.GetFieldCount())]

    data = []
    for ifeature in range(layer.GetFeatureCount()):
        row = dict_()
        feature = layer.GetFeature(ifeature)
        for iattr, attr in enumerate(attrs):
            row[attr] = feature.GetField(iattr)
        row.geom = feature.GetGeometryRef().ExportToJson()
        data.append(row)

    return data
