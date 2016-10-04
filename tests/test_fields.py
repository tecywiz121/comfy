import comfy
from comfy.fields import *
import unittest

class Mocked(Exception):
    def __init__(self, args, kwargs):
        self.args = args
        self.kwargs = kwargs
        super().__init__()

class MockStr(str):
    def to_dict(self):
        return '6'

class MockInt(int):
    def to_dict(self):
        return 6

class MockConf(comfy.Conf):
    f = Field(int)

    def update(self, other):
        raise Mocked([other], {})

    def sanitize(self):
        raise Mocked([], {})

class TestField(unittest.TestCase):
    def setUp(self):
        self.f = Field(int, name='name')

    def test_init(self):
        self.assertEqual(self.f.field_type, int)
        self.assertEqual(self.f.name, 'name')
        self.assertEqual(self.f.required, BaseField.required)
        self.assertEqual(self.f.null, BaseField.null)
        self.assertEqual(self.f.description, BaseField.description)
        self.assertEqual(self.f.choices, BaseField.choices)
        self.assertEqual(self.f.validator, BaseField.validator)
        self.assertEqual(self.f.default, BaseField.default)

    def test_to_type(self):
        self.assertEqual(self.f.to_type(1), 1)
        self.assertEqual(self.f.to_type('123'), 123)

    def test_dump(self):
        self.assertEqual(self.f.dump(66), 66)
        self.assertEqual(self.f.dump(MockInt()), 6)

    def test_update_one(self):
        self.assertEqual(self.f.update(2, BaseField.UNSET), 2)
        self.assertEqual(self.f.update(BaseField.UNSET, 2), 2)

    def test_update(self):
        self.assertEqual(self.f.update(1, 9), 9)

    def test_sanitize_null(self):
        self.f.null = False
        with self.assertRaises(NullError):
            self.f.sanitize(None)

        self.f.null = True
        self.assertIsNone(self.f.sanitize(None))

    def test_sanitize_unset(self):
        self.f.required = True
        with self.assertRaises(UnsetError):
            self.f.sanitize(BaseField.UNSET)

        self.f.required = False
        self.assertIs(self.f.sanitize(BaseField.UNSET), BaseField.UNSET)

    def test_sanitize_choices(self):
        self.f.choices = [1, 2, 66]
        with self.assertRaises(MischoiceError):
            self.f.sanitize(-1)
        self.assertEqual(self.f.sanitize(66), 66)

    def test_sanitize_convert_choices(self):
        self.f.choices = [1, 2, 66]
        with self.assertRaises(MischoiceError):
            self.f.sanitize('-1')
        self.assertEqual(self.f.sanitize('66'), 66)

    def test_sanitize_validator(self):
        def v(x):
            raise ValidationError('', 'Bad')
        self.f.validator = v
        with self.assertRaises(ValidationError):
            self.f.sanitize(1)

class TestFieldWithConf(unittest.TestCase):
    def setUp(self):
        self.f = Field(MockConf, name='name')

    def test_init(self):
        self.assertEqual(self.f.field_type, MockConf)
        self.assertEqual(self.f.name, 'name')
        self.assertEqual(self.f.required, BaseField.required)
        self.assertEqual(self.f.null, BaseField.null)
        self.assertEqual(self.f.description, BaseField.description)
        self.assertEqual(self.f.choices, BaseField.choices)
        self.assertEqual(self.f.validator, BaseField.validator)
        self.assertEqual(self.f.default, BaseField.default)

    def test_update(self):
        c = MockConf()
        with self.assertRaises(Mocked):
            self.f.update(c, c)

    def test_sanitize(self):
        c = MockConf()
        with self.assertRaises(Mocked):
            self.f.sanitize(c)

class TestListField(unittest.TestCase):
    def setUp(self):
        self.f = ListField(int, name='name')

    def test_init(self):
        self.assertEqual(self.f.field_type, list)
        self.assertEqual(self.f.item_type, int)
        self.assertEqual(self.f.name, 'name')
        self.assertEqual(self.f.required, BaseField.required)
        self.assertEqual(self.f.null, BaseField.null)
        self.assertEqual(self.f.description, BaseField.description)
        self.assertEqual(self.f.choices, BaseField.choices)
        self.assertEqual(self.f.validator, BaseField.validator)
        self.assertEqual(self.f.default, [])
        self.assertEqual(self.f.update_mode, ListUpdate.replace)
        self.assertEqual(self.f.empty, False)

    def test_to_item_type(self):
        self.assertEqual(self.f.to_item_type(1), 1)
        self.assertEqual(self.f.to_item_type('123'), 123)

    def test_to_type(self):
        self.assertEqual(self.f.to_type([1]), [1])
        self.assertEqual(self.f.to_type('123'), [1, 2, 3])
        self.assertEqual(self.f.to_type(['1', '2', '3']), [1, 2, 3])

    def test_update_one(self):
        self.assertEqual(self.f.update([2], BaseField.UNSET), [2])
        self.assertEqual(self.f.update(BaseField.UNSET, [2]), [2])

    def test_update_replace(self):
        self.f.update_mode = ListUpdate.replace
        a = [1, 2, 3]
        b = self.f.update(a, [4, 5, 6])
        self.assertIs(b, a)
        self.assertEqual(b, [4, 5, 6])
        self.assertEqual(a, [4, 5, 6])

    def test_update_append(self):
        self.f.update_mode = ListUpdate.append
        a = [1, 2, 3]
        b = self.f.update(a, [4, 5, 6])
        self.assertIs(b, a)
        self.assertEqual(b, [1, 2, 3, 4, 5, 6])
        self.assertEqual(a, [1, 2, 3, 4, 5, 6])

    def test_sanitize_int(self):
        with self.assertRaises(TypeError):
            self.f.sanitize(1)

    def test_sanitize(self):
        self.assertEqual(self.f.sanitize('123'), [1, 2, 3])

    def test_sanitize_empty(self):
        self.f.empty = False
        with self.assertRaises(EmptyError):
            self.f.sanitize([])
        self.f.empty = True
        self.assertEqual(self.f.sanitize([]), [])

class TestDictField(unittest.TestCase):
    def setUp(self):
        self.f = DictField(int, str, name='name')

    def test_init(self):
        self.assertEqual(self.f.field_type, dict)
        self.assertEqual(self.f.key_type, int)
        self.assertEqual(self.f.value_type, str)
        self.assertEqual(self.f.name, 'name')
        self.assertEqual(self.f.required, BaseField.required)
        self.assertEqual(self.f.null, BaseField.null)
        self.assertEqual(self.f.description, BaseField.description)
        self.assertEqual(self.f.choices, BaseField.choices)
        self.assertEqual(self.f.validator, BaseField.validator)
        self.assertEqual(self.f.default, {})
        self.assertEqual(self.f.update_mode, DictUpdate.replace)
        self.assertEqual(self.f.empty, False)

    def test_to_key_type(self):
        self.assertEqual(self.f.to_key_type('1'), 1)
        x = MockInt(5)
        self.assertIs(self.f.to_key_type(x), x)

    def test_to_value_type(self):
        self.assertEqual(self.f.to_value_type('1'), '1')
        x = MockStr('5')
        self.assertIs(self.f.to_value_type(x), x)

    def test_get_items_in(self):
        class Mock(object):
            def items(self):
                raise Mocked([], {})
        with self.assertRaises(Mocked):
            self.f.get_items_in(Mock())

    def test_to_type(self):
        self.assertEqual(self.f.to_type({'1': 1}), {1: '1'})

    def test_update_one(self):
        self.assertEqual(self.f.update({'a': 1}, BaseField.UNSET), {'a': 1})
        self.assertEqual(self.f.update(BaseField.UNSET, {'b': 2}), {'b': 2})

    def test_update_replace(self):
        self.f.update_mode = DictUpdate.replace
        self.assertEqual(self.f.update({'a': 1}, {'b': 2}), {'b': 2})

    def test_update_merge(self):
        self.f.update_mode = DictUpdate.merge
        src = {'a': {'b': 1}, 'c': 4}
        self.assertEqual(self.f.update(src, {'a': {'d': 2}}),
                         {'a': {'d': 2}, 'c': 4})

    def test_update_deep_merge(self):
        self.f.update_mode = DictUpdate.deep_merge
        src = {'a': {'b': 1}, 'c': 4}
        self.assertEqual(self.f.update(src, {'a': {'d': 2}}),
                         {'a': {'b': 1, 'd': 2}, 'c': 4})

    def test_sanitize_int(self):
        with self.assertRaises(AttributeError):
            self.f.sanitize(1)

    def test_sanitize(self):
        self.assertEqual(self.f.sanitize({1:2,3:4}), {1: '2', 3: '4'})

    def test_sanitize_empty(self):
        self.f.empty = False
        with self.assertRaises(EmptyError):
            self.f.sanitize({})
        self.f.empty = True
        self.assertEqual(self.f.sanitize({}), {})

