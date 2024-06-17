# -*- coding: utf-8 -*-

import alt_path
import glob
import jinja2
import uuid
import json
import untangle
from typing import Optional, Any
from collections import defaultdict
from datetime import datetime
from pyproj import Geod
import os

import alt.cfg
import alt.file
import alt.pg
import gis.geom
import shape_lib
from alt.types import Strict


class Object(Strict):
    guid: Optional[str]
    region: str
    name: str
    geom: Any
    area: float


class Error:
    def __init__(self):
        self.errors = defaultdict(list)

    def setup(self, shp_file, name):
        self.shp_file = shp_file
        self.name = name

    def error(self, msg):
        msg = self.name + ': ' + msg
        self.errors[self.shp_file].append(msg)


def read_dict_xsd():
    regions = {}
    # Получить директорию, где находится скрипт
    script_dir = os.path.dirname(os.path.abspath(__file__))
    xml = untangle.parse(os.path.join(script_dir, 'xsd/Dictionaries.xsd'))
    for type in xml.xs_schema.xs_simpleType:
        if type.xs_annotation.xs_documentation.cdata == 'Субъекты РФ':
            for reg in type.xs_restriction.xs_enumeration:
                code = reg['value']
                name = reg.xs_annotation.xs_documentation.cdata
                regions[name] = code

    return regions


def get_value(obj, attrs, return_none=False):
    for attr in attrs:
        if attr in obj:
            return obj[attr]

    if return_none:
        return
    else:
        raise Exception('Attr not found')


def read_sended_xml():
    sended = {}
    for date_dir in sorted(glob.glob(_sended_dir + '????-??-??')):
        for xml_file in glob.glob(date_dir + '/*.xml'):
            xml = untangle.parse(xml_file)
            guid = xml.DataMessage.eDocument['GUID']
            mode = xml.DataMessage.eDocument['ProcessingKind']
            entity = xml.DataMessage.Package.SpecialZone.SpecialZoneEntitySpatial
            region = entity.SpecialZoneObjectInfo['Region']
            name = entity.SpecialZoneObjectInfo['Name']
            points = []
            for point in entity.SpatialElement.SpelementUnit:
                points.append((point.NewOrdinate['X'], point.NewOrdinate['Y']))
            # todo expand here
            obj = Object(
                guid=guid,
                region=region,
                name=name,
                polygons=polygons
            )
            if mode == 'Addition':
                if guid in sended:
                    raise Exception('Объект существует')
                sended[guid] = obj
            if mode == 'Replacement':
                if guid not in sended:
                    raise Exception('Объект не существует')
                if sended[guid].region != region or \
                        sended[guid].name != name:
                    raise Exception('Другой GUID')
                sended[guid] = obj
            if mode == 'Deletion':
                if guid not in sended:
                    raise Exception('Объект не существует')
                del sended[guid]
    return list(sended.values())


def read_shapes():
    is_break = False
    shapes = []
    # region_dirs = glob.glob(_shapes_dir + '**', recursive=True)
    keys = {}
    # todo поправить для ГСК
    geod = Geod('+a=6378137 +f=0.0033528106647475126')
    # for region_dir in region_dirs:
    if True:
        # todo remove limit
        # shp_files = glob.glob(region_dir + '/*.shp')
        shp_files = glob.glob(_shapes_dir + '**/*.shp', recursive=True)
        for shp_file in shp_files:
            print(shp_file)

            _error.setup(shp_file, '')
            shp, proj4 = shape_lib.read(shp_file, encoding='CP1251')
            # print('### proj4: ', proj4)
            if proj4 != '+proj=longlat +ellps=GSK2011 +no_defs':
                _error.error(f'Проекция не ГСК-11: {shp_file}')
                # break
                continue
                # raise Exception(f'Проекция не ГСК-11: {shp_file}')
            region_attr, name_attr, area_attr = 'subrf', None, 'area'
            # todo remove limit
            for obj in shp:
                if name_attr is None:
                    if 'заявки' in shp_file:
                        name_attr = 'full_name'
                        type = 'З'
                    elif 'НФ' in shp_file:
                        name_attr = 'name_gbz'
                        type = 'НФ'
                    elif 'Лиц' in shp_file or 'лиц' in shp_file:
                        name_attr = 'snomv'
                        type = 'Лиц'
                    else:
                        _error.error('Неверное название шейп файла')
                        is_break = True
                        break
                    if name_attr not in obj:
                        _error.error(f'Нет поля названия: {name_attr}')
                        is_break = True
                        break
                    if area_attr not in obj:
                        _error.error(f'Нет поля площади: {area_attr}')
                        is_break = True
                        break
                    if not isinstance(obj[area_attr], float):
                        _error.error(f'Поле площади не число: {area_attr}')
                        is_break = True
                        break
                    if region_attr not in obj:
                        _error.error(f'Нет поля субъекта РФ: {region_attr}')
                        is_break = True
                        break

                name = obj[name_attr]
                if name is None:
                    _error.error('Пустое имя')
                    continue
                _error.setup(shp_file, name)

                region_name = obj[region_attr]
                # region_name = get_value(obj, ['subrf', 'sub_rf_sm', 'subjekt', 'sub_rf'])
                if region_name is None:
                    _error.error(f'Пустой субъект РФ')
                    continue

                region_name = region_name.replace('АО', 'автономный округ')
                # что делать?
                if region_name not in _regions:
                    _error.error(f'Субъекта РФ нет в справочнике')
                    continue
                region = _regions[region_name]

                name = name.replace('"', '&quot;')[:200]

                geom = gis.geom.Geom(geojson=obj.geom, proj=proj4, check_validity=False)
                # geom = gis.geom.Geom(geojson=obj.geom, proj=proj4)
                if not geom.gdal:
                    _error.error('Неустранимая ошибка в геометрии')
                    continue
                # что делать?
                if not geom.valid():
                    # _error.error('Ошибка в геометрии')
                    sql = "select public.st_astext(public.st_makevalid(public.st_geomfromtext(%s))) as wkt"
                    geom = gis.geom.Geom(wkt=db.sql(sql, geom.wkt(), return_one=True).wkt)
                    if not geom.valid():
                        _error.error('Неустранимая ошибка в геометрии')
                    continue
                # todo точно 3857 ?
                # geom.to_proj(4326)
                # gj = json.loads(geom.geojson())
                # if gj["type"] == "MultiPolygon":
                #     polygons = gj['coordinates']
                # elif gj["type"] == "Polygon":
                #     polygons = [gj['coordinates']]
                # else:
                #     raise Exception('Geometry not polygon')
                # todo check area ?
                # calc_area = 0
                # for poly in polygons:
                #     xg = [xg for xg, yg in poly[0]]
                #     yg = [yg for xg, yg in poly[0]]
                #     calc_area += abs(geod.polygon_area_perimeter(xg, yg)[0])
                area = obj[area_attr] * 1e6

                # area = get_value(obj, ['area', 'square', 'area3'], return_none=True)
                # if area is not None:
                #     if isinstance(area, str):
                #         if not area.isdigit():
                #             _error.error('Area not float')
                #             continue
                #         area = float(area)
                #     area = area * 1e6
                #     if abs(area - calc_area) / calc_area > 0.25:
                #         _error.error('Wrong area')
                # else:
                #     area = calc_area
                key = (region, name)
                # todo что делать?
                if key in keys:
                    key_shp_file, key_type, ishape = keys[key]
                    shapes[ishape].geom.add(geom)
                    continue
                    # if True or key_type != type:
                    #     key_gj = {'type': 'Multipolygon', 'coordinates': shapes[ishape].polygons}
                    #     key_poly = gis.geom.Geom(geojson=key_gj)
                    #     gj = {'type': 'Multipolygon', 'coordinates': polygons}
                    #     poly = gis.geom.Geom(geojson=gj)
                    #     poly.add(key_poly)
                    #     gj = json.loads(poly.geojson())
                    #     if gj["type"] == "MultiPolygon":
                    #         polygons = gj['coordinates']
                    #     elif gj["type"] == "Polygon":
                    #         polygons = [gj['coordinates']]
                    #     shapes[ishape].polygons = polygons
                    #     continue
                    # _error.error(f'Повтор ключа: {keys[key]}')
                    # continue
                    # raise Exception('Повтор ключа')
                keys[key] = (shp_file, type, len(shapes))
                # todo expand here
                shapes.append(Object(
                    region=region,
                    name=name,
                    geom=geom,
                    area=area
                ))
    # todo remove change debug
    # shapes[3].points[0] = (-1,-1)
    # todo remove delete debug
    # shapes.pop()
    if is_break:
        print('### is break!')
    else:
        print('### is not break!')

    return shapes


def make_send_xml(shapes, sended):
    alt.file.delete(_send_dir)
    alt.file.mkdir(_send_dir)
    jinja = jinja2.Environment(loader=jinja2.FileSystemLoader(alt.cfg.main_dir() + 'tpl'))
    jinja.globals.update(dict(len=len, enumerate=enumerate))
    main_tpl = jinja.get_template('main.xml')

    sended_objs_by_key = {}
    send: Object
    for send in sended:
        sended_objs_by_key[(send.region, send.name)] = send

    data = defaultdict(list)
    n_total = 0

    obj: Object
    for obj in shapes:
        key = (obj.region, obj.name)
        mode = None
        if key not in sended_objs_by_key:
            mode = 'Addition'
            obj.guid = str(uuid.uuid4())
        # else:
        #     if obj != sended_objs_by_key[key]:
        #         continue
        #     else:
        #         mode = 'Replacement'
        #         obj.guid = sended_objs_by_key[key].guid
        #     del sended_objs_by_key[key]
        data[(obj.region, mode)].append(obj.dict())

    for region, mode in data:
        objs = data[(region, mode)]
        for obj in objs:
            gj = json.loads(obj['geom'].geojson())
            if gj["type"] == "MultiPolygon":
                obj['polygons'] = gj['coordinates']
            elif gj["type"] == "Polygon":
                obj['polygons'] = [gj['coordinates']]
            else:
                raise Exception('Geometry not polygon')
        n_objs = len(objs)
        if len(objs) >= 10000:
            raise Exception('Too many objs')
        n_total += n_objs
        xml = main_tpl.render(region=region, mode=mode, guid=str(uuid.uuid4()), objs=objs,
                              n_objs=n_objs, ctime=datetime.now().isoformat()[:19] + 'Z')
        print(f'{region}-{mode}')
        alt.file.write(f'{_send_dir}{region}-{mode}.xml', xml)

    # mode = 'Deletion'
    # for obj in sended_objs_by_key.values():
    #     xml = main_tpl.render(mode=mode, **obj.dict())
    #     print(f'{mode}-{obj.guid}')
    #     alt.file.write(f'{_send_dir}{mode}-{obj.guid}.xml', xml)

    print('n_total =', n_total)


_error = Error()
_regions = read_dict_xsd()
# sended = read_sended_xml()
sended = []

cfg = alt.cfg.read()
DOCKER = os.getenv('DOCKER', False)

_host, _user, _pwd = cfg['pg_docker'].values() if DOCKER else cfg['pg'].values()
_shapes_dir, _sended_dir, _send_dir, _error_dir, _ = cfg['dir'].values()

db = alt.pg.DB(host=_host, user=_user, pwd=_pwd)
shapes = read_shapes()
make_send_xml(shapes, sended)

alt.file.delete(_error_dir)
alt.file.mkdir(_error_dir)
for shp_file, msgs in _error.errors.items():
    alt.file.write(_error_dir + os.path.basename(shp_file) + '.txt', '\n'.join(msgs))
