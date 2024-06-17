import alt_path
import glob
import untangle
import shape_lib
from alt.dict_ import dict_
import alt.file

cfg = alt.cfg.read()

_send_dir = cfg.dir.send
_shapes_dir = cfg.dir.control


def xml_get_list_value(xml, attr):
    if not hasattr(xml, attr):
        return []
    value = getattr(xml, attr)
    if isinstance(value, list):
        return value
    return [value]


alt.file.mkdir(_shapes_dir)
xml_files = glob.glob(_send_dir + '*.xml')
data = []
for xml_file in xml_files:
    print(xml_file)
    xml = untangle.parse(xml_file)
    data = []
    for entity in xml.DataMessage.Package.SpecialZone.SpecialZoneEntitySpatial:
        attrs = entity.SpecialZoneObjectInfo
        polys = []
        for elem in xml_get_list_value(entity, 'SpatialElement'):
            poly = []
            points = []
            for unit in elem.SpelementUnit:
                points.append((float(unit.NewOrdinate['X']), float(unit.NewOrdinate['Y'])))
            poly.append(points)
            for ring in xml_get_list_value(elem, 'SpatialRingElement'):
                points = []
                for unit in ring.SpelementUnit:
                    points.append((float(unit.NewOrdinate['X']), float(unit.NewOrdinate['Y'])))
                poly.append(points)
            polys.append(poly)
        row = dict_(name=attrs['Name'], region=attrs['Region'], area=attrs['Area'], polys=polys)
        data.append(row)

    shape_lib.write(f'{_shapes_dir}/{alt.file.name(xml_file)}.shp', data)
