from .fields import BaseField

class ConfMeta(type):
    def __new__(cls, cname, bases, attrs):
        fields = []

        for name, value in attrs.items():
            if isinstance(value, BaseField):
                fields.append((name, value))
                if not value.name:
                    value.name = name

        attrs['fields'] = tuple(fields)
        return super(ConfMeta, cls).__new__(cls, cname, bases, attrs)

class Conf(metaclass=ConfMeta):
    @classmethod
    def _only_fields(cls, d):
        '''Extracts values from a dictionary based on their field name'''
        result = {}
        for field, field_def in cls.fields:
            if d is BaseField.UNSET:
                continue
            try:
                value = d[field_def.name]
            except KeyError:
                value = BaseField.UNSET

            if issubclass(field_def.field_type, Conf):
                value = field_def.field_type(value)

            result[field] = value
        return result

    def __init__(self, *args, **kwargs):
        values = kwargs
        nargs = len(args)
        if nargs == 1:
            values = self._only_fields(args[0])
            values.update(kwargs)
        elif nargs:
            raise TypeError('__init__() takes 1 positional argument but {} were'
                            ' given'.format(nargs))

        for field, field_def in self.fields:
            try:
                value = values[field]
            except KeyError:
                try:
                    value = field_def.default()
                except TypeError:
                    value = field_def.default
            setattr(self, field, value)

    def sanitize(self, path=''):
        for field, field_def in self.fields:
            value = getattr(self, field)
            value = field_def.sanitize(value)
            setattr(self, field, value)

        return self

    def update(self, *args):
        if not args:
            raise TypeError('update() takes at least one positional argument'
                            ' but none were given')

        for other in args:
            for field, field_def in self.fields:
                my_value = getattr(self, field)
                other_value = getattr(other, field)
                setattr(self, field, field_def.update(my_value, other_value))

        return self

    def to_dict(self):
        cls = self.__class__
        result = {}
        for field, field_def in cls.fields:
            value = getattr(self, field, BaseField.UNSET)
            if value is not BaseField.UNSET:
                result[field_def.name] = field_def.dump(getattr(self, field))
        return result

    def __repr__(self):
        return type(self).__name__ + '(' + repr(self.to_dict()) + ')'
