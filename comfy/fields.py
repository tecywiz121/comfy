# vim: set et sw=4 sts=4 ts=4:
from enum import Enum
import collections
import comfy

class ValidationError(Exception):
    def __init__(self, field, message):
        super().__init__(message)
        self.field = field

class NullError(ValidationError):
    def __init__(self, field):
        super().__init__(field, "Field '{}' is None".format(field.name))

class UnsetError(ValidationError):
    def __init__(self, field):
        super().__init__(field,
                         "Required option '{}' not set".format(field.name))

class MischoiceError(ValidationError):
    def __init__(self, field):
        super().__init__(field,
                         "Invalid choice for '{}'".format(field.name))

class EmptyError(ValidationError):
    def __init__(self, field):
        super().__init__(field,
                         "Empty collection for '{}'".format(field.name))

class BaseField(object):
    UNSET = type('UnsetValue', tuple(), {'__repr__': lambda x: '<unset>'})()

    name = ''
    field_type = int

    required = True
    null = False
    description = ''
    choices = None
    validator = lambda v: None

    default = UNSET

class Field(BaseField):
    def __init__(self,
                 field_type,
                 name = '',
                 required=BaseField.required,
                 null=BaseField.null,
                 description=BaseField.description,
                 choices=BaseField.choices,
                 validator=BaseField.validator,
                 default=BaseField.default):
        self.field_type = field_type
        self.name = name
        self.required = required
        self.null = null
        self.description = description
        self.choices = choices
        self.validator = validator
        self.default = default

    def to_type(self, src):
        if isinstance(src, self.field_type):
            return src
        else:
            return self.field_type(src)

    def dump(self, value):
        try:
            to_dict = value.to_dict
        except AttributeError:
            return value
        return to_dict()

    def update(self, v1, v2):
        if v1 == BaseField.UNSET:
            return v2
        elif v2 == BaseField.UNSET:
            return v1

        if issubclass(self.field_type, comfy.Conf):
            v1.update(v2)
            return v1
        else:
            return v2

    def sanitize(self, src):
        # Null checking
        if src is None:
            if self.null:
                return src
            else:
                raise NullError(self)

        # Required Checking
        if src is BaseField.UNSET:
            if self.required:
                raise UnsetError(self)
            else:
                return self.default
        else:
            src = self.to_type(src)

        # Choices
        if self.choices:
            if src not in self.choices:
                raise MischoiceError(self)

        if issubclass(self.field_type, comfy.Conf):
            src.sanitize()

        # Validator
        self.validator(src)

        return src

class ListUpdate(Enum):
    replace = 0
    append  = 1

class ListField(Field):
    def __init__(self,
                 item_type,
                 empty=False,
                 update=ListUpdate.replace,
                 *args,
                 **kwargs):
        defaults = {'default': list}
        defaults.update(kwargs)
        super().__init__(list, *args, **defaults)
        self.empty = empty
        self.item_type = item_type
        self.update_mode = update

    def to_item_type(self, src):
        if isinstance(src, self.item_type):
            return src
        else:
            return self.item_type(src)

    def to_type(self, src):
        return [self.to_item_type(x) for x in src]

    def update(self, v1, v2):
        if v1 == BaseField.UNSET:
            return v2
        elif v2 == BaseField.UNSET:
            return v1

        if self.update_mode == ListUpdate.replace:
            del v1[:]
            if v2:
                v1 += v2
        elif self.update_mode == ListUpdate.append:
            if v2:
                v1 += v2
        else:
            raise Exception('Unknown ListUpdate method')
        return v1

    def sanitize(self, src):
        if src is BaseField.UNSET:
            if self.required:
                raise UnsetError(self)
            else:
                try:
                    return self.default()
                except TypeError:
                    return self.default

        src = super().sanitize(src)
        if not self.empty and len(src) == 0:
            raise EmptyError(self)
        elif issubclass(self.item_type, comfy.Conf):
            for item in src:
                item.sanitize()

        return src


class DictUpdate(Enum):
    replace     = 0
    merge       = 1
    deep_merge  = 2

class DictField(Field):
    @staticmethod
    def deep_merge(d, u):
        for k, v in u.items():
            if isinstance(v, collections.Mapping):
                r = DictField.deep_merge(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d

    def __init__(self,
                 key_type,
                 value_type,
                 empty=False,
                 update=DictUpdate.replace,
                 *args,
                 **kwargs):
        defaults = {'default': dict}
        defaults.update(kwargs)
        super().__init__(dict, *args, **defaults)

        if issubclass(key_type, comfy.Conf):
            raise TypeError('key_type cannot be a subclass of Conf')

        if issubclass(value_type, comfy.Conf):
            raise TypeError('value_type cannot be a subclass of Conf, for now')

        self.key_type = key_type
        self.value_type = value_type
        self.empty = empty
        self.update_mode = update

    def to_key_type(self, k):
        if isinstance(k, self.key_type):
            return k
        else:
            return self.key_type(k)

    def to_value_type(self, v):
        if isinstance(v, self.value_type):
            return v
        else:
            return self.value_type(v)

    def get_items_in(self, value):
        return value.items()

    def to_type(self, src):
        result = self.field_type()
        for k, v in self.get_items_in(src):
            k = self.to_key_type(k)
            v = self.to_value_type(v)
            result[k] = v
        return result

    def update(self, v1, v2):
        if v1 == BaseField.UNSET:
            return v2
        elif v2 == BaseField.UNSET:
            return v1

        if self.update_mode == DictUpdate.replace:
            v1.clear()
            v1.update(v2)
        elif self.update_mode == DictUpdate.merge:
            v1.update(v2)
        elif self.update_mode == DictUpdate.deep_merge:
            self.deep_merge(v1, v2)
        else:
            raise Exception('Unknown DictUpdate method')

        return v1

    def sanitize(self, src):
        src = super().sanitize(src)
        if not self.empty and len(src) == 0:
            raise EmptyError(self)

        if issubclass(self.value_type, comfy.Conf):
            for value in src.values():
                value.sanitize()
        return src
