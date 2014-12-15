"""Unit tests for struct.py."""


import unittest
from collections import OrderedDict
import pickle
import copy

from simplestruct.struct import *


# Pickled types must be defined at module level.
class PickleFoo(Struct):
    a = Field()


class StructCase(unittest.TestCase):
    
    def test_Field(self):
        # We're just testing the behavior of Field as a descriptor,
        # and not Struct/MetaStruct, so we'll mock the behavior of
        # the meta machinery.
        barfield = Field()
        barfield.name = 'bar'
        
        # Normal read/write access.
        class Foo:
            _immutable = False
            bar = barfield
        f = Foo()
        f.bar = 5
        self.assertEqual(f.bar, 5)
        
        # Immutable access, pre- and post-initialization.
        class Foo:
            _immutable = True
            bar = barfield
        f = Foo()
        f._initialized = False
        f.bar = 5
        f._initialized = True
        with self.assertRaises(AttributeError):
            f.bar = 6
        
        # Equality and hashing.
        self.assertTrue(barfield.eq(5, 5))
        self.assertFalse(barfield.eq(5, 6))
        self.assertEqual(barfield.hash(5), hash(5))
    
    def test_Struct(self):
        # Basic instantiation and pretty printing.
        class Foo(Struct):
            bar = Field()
        f = Foo(5)
        self.assertEqual(f.bar, 5)
        self.assertEqual(str(f), 'Foo(bar=5)')
        
        # Equality and hashing.
        class Foo(Struct):
            bar = Field()
        f1 = Foo(5)
        f2 = Foo(5)
        f3 = Foo(6)
        self.assertEqual(f1, f2)
        self.assertNotEqual(f1, f3)
        self.assertEqual(hash(f1), hash(f2))
        # hash(f1) == hash(f3) is unlikely but valid.
        
        # No hashing for mutable structs.
        class Foo(Struct):
            _immutable = False
            bar = Field()
        f = Foo(5)
        with self.assertRaises(TypeError):
            hash(f)
        
        # Construction by keyword.
        class Foo(Struct):
            a = Field()
            b = Field()
            c = Field()
        f1 = Foo(1, b=2, **{'c': 3})
        f2 = Foo(1, 2, 3)
        self.assertEqual(f1, f2)
        # _struct attribute.
        names = [f.name for f in Foo._struct]
        self.assertEqual(names, ['a', 'b', 'c'])
        
        # Parentheses-less shorthand.
        class Foo(Struct):
            bar = Field
        f = Foo(5)
        self.assertEqual(f.bar, 5)
        
        # Distinct uses of Field instances are cloned.
        barfield = Field()
        class Foo1(Struct):
            bar1 = barfield
            bar2 = barfield
        class Foo2(Struct):
            bar3 = barfield
        # Check for distinct instances. Although if there's
        # overlap, there'd be a name collision anyway.
        ids = {id(f) for f in Foo1._struct + Foo2._struct}
        self.assertTrue(len(ids) == 3)
        
        # Tuple decomposition.
        class Foo(Struct):
            a = Field()
            b = Field()
        f = Foo(1, 2)
        a, b = f
        self.assertEqual(len(f), 2)
        self.assertEqual((a, b), (1, 2))
    
    def test_mutability(self):
        # Mutable, unhashable.
        class Foo(Struct):
            _immutable = False
            bar = Field()
        f = Foo(5)
        f.bar = 6
        with self.assertRaises(TypeError):
            hash(f)
        
        # Immutable and hashable after initialization is done.
        class Foo(Struct):
            bar = Field()
            def __init__(self, *_):
                self.bar += 1
        f = Foo(5)
        self.assertEqual(f.bar, 6)
        hash(f)
        with self.assertRaises(AttributeError):
            f.bar = 7
        
        # Unhashable during initialization.
        class Foo(Struct):
            bar = Field()
            def __init__(self, bar):
                hash(self)
        with self.assertRaises(TypeError):
            f = Foo(5)
    
    def test_custom_eq_hash(self):
        class CustomField(Field):
            def eq(self, val1, val2):
                return val1 * val2 > 0
            def hash(self, val):
                return int(val) * 2
        
        class FooA(Struct):
            bar = Field()
        class FooB(Struct):
            bar = CustomField()
        
        fa1 = FooA(5)
        fa2 = FooA(6)
        fb1 = FooB(5)
        fb2 = FooB(6)
        
        self.assertNotEqual(fa1, fa2)
        self.assertEqual(hash(fa1), hash(5))
        self.assertEqual(fb1, fb2)
        self.assertEqual(hash(fb1), 10)
    
    def test_asdict(self):
        class Foo(Struct):
            a = Field()
            b = Field()
            c = Field()
        f = Foo(1, 2, 3)
        d = f._asdict()
        exp_d = OrderedDict([('a', 1), ('b', 2), ('c', 3)])
        self.assertEqual(d, exp_d)
    
    def test_replace(self):
        class Foo(Struct):
            a = Field()
            b = Field()
            c = Field()
        f1 = Foo(1, 2, 3)
        f2 = f1._replace(b=4)
        f3 = Foo(1, 4, 3)
        self.assertEqual(f2, f3)
    
    def test_pickleability(self):
        # Pickle dump/load.
        f1 = PickleFoo(1)
        buf = pickle.dumps(f1)
        f2 = pickle.loads(buf)
        self.assertEqual(f2, f1)
        
        # Deep copy.
        f3 = copy.deepcopy(f1)
        self.assertEqual(f3, f1)
    
    def test_inherit_fields(self):
        # Normal case.
        class Foo(Struct):
            a = Field()
        class Bar(Foo):
            _inherit_fields = True
            b = Field()
        bar = Bar(1, 2)
        self.assertEqual(bar.a, 1)
        self.assertEqual(bar.b, 2)
        
        # Name collision.
        with self.assertRaises(AttributeError):
            class Baz(Foo):
                _inherit_fields = True
                a = Field()


if __name__ == '__main__':
    unittest.main()
