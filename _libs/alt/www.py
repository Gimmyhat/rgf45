from alt.dict_ import dict_

def prepare_params(params, default=None):

    params = dict_(params)
    for attr, value in params.items():
        if isinstance(value, str):
            params[attr] = value.strip()
        if default and attr in default and attr not in params:
            params[attr] = default[attr]

    return params