class Enumeration(object):
    """
    A small helper class for more readable enumerations,
    and compatible with Django's choice convention.
    You may just pass the instance of this class as the choices
    argument of model/form fields.

    Example:
        MY_ENUM = Enumeration(
            (100, 'MY_NAME', 'My verbose name'),
            (200, 'MY_AGE', 'My verbose age'),
        )
        assert MY_ENUM.MY_AGE == 100
        assert MY_ENUM[1] == (200, 'My verbose age')
    """

    def __init__(self, *enum_list):
        self.enum_list = [(item[0], item[2]) for item in enum_list]
        self.enum_dict = {}
        self._enums_dict_switch = {}
        for item in enum_list:
            self.enum_dict[item[1]] = item[0]
            self._enums_dict_switch[item[0]] = item[1]

    def __contains__(self, v):
        return v in self.enum_list

    def __len__(self):
        return len(self.enum_list)

    def __getitem__(self, v):
        if isinstance(v, str):
            return self.enum_dict[v]
        elif isinstance(v, int):
            return self.enum_list[v]

    def __getattr__(self, name):
        if name == "enum_dict":
            raise AttributeError()
        try:
            return self.enum_dict[name]
        except KeyError as e:
            raise AttributeError(*e.args)

    def __iter__(self):
        return self.enum_list.__iter__()

    def get_title(self, key):
        return self._enums_dict_switch.get(key, "")
