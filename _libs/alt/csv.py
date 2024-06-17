from alt.dict_ import dict_
import alt.file

def read(csv_file, separator=';', attrs=None):

    text = alt.file.readlines(csv_file)
    header = text[0].split(separator)
    header = [col.strip() for col in header]
    data = []
    for line in text[1:]:
        line = line.strip()
        if not line:
            continue
        row = dict_()
        line = line.split(separator)
        for attr, value in zip(header, line):
            if attrs:
                attr = attrs[attr]
            row[attr] = value.strip()
        data.append(row)

    return data