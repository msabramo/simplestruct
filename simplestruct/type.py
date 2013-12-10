"""Type checking and type coercion."""

# Spare me the "It's not the Python way" lectures. I've lost too much
# time to type errors in places where I never had any intention of
# allowing duck-typed alternative values.

# A kind is a tuple of types. A value satisfies a kind if it is an
# instance of any of the types. For convenience, kinds may also be
# specified as a single type, a sequence other than a tuple, and as
# None (equivalent to (object,)).

# A type specification is a kind along with a tuple of modifier strings,
# which may include:
#
#   'seq': sequence of elements satisfying the kind
#   'nodups': with 'seq', no duplicate elements allowed
#
# The modifier strings may also be given as another sequence or as a
# space-delimited string.


__all__ = [
    'checktype',
    'checktype_seq',
    'check_spec',
]


def str_valtype(val):
    """Get a string describing the type of val."""
    return type(val).__name__

def normalize_kind(kind):
    """Make a proper kind out of one of the alternative forms."""
    if kind is None:
        return (object,)
    elif isinstance(kind, type):
        return (kind,)
    else:
        return tuple(kind)

def normalize_mods(mods):
    """Make a modifier list out of space-delimited string."""
    if isinstance(mods, str):
        return tuple(mods.split())
    else:
        return tuple(mods)

def str_kind(kind):
    """Get a string describing a kind."""
    if len(kind) == 0:
        return '()'
    elif len(kind) == 1:
        return kind[0].__name__
    elif len(kind) == 2:
        return kind[0].__name__ + ' or ' + kind[1].__name__
    else:
        return 'one of {' + ', '.join(t.__name__ for t in kind) + '}'


def checktype(val, kind):
    """Raise TypeError if val does not satisfy kind."""
    kind = normalize_kind(kind)
    if not isinstance(val, kind):
        raise TypeError('Expected {}; got {}'.format(
                        str_kind(kind), str_valtype(val)))

def checktype_seq(seq, kind, nodups=False):
    """Raise TypeError if seq is not a sequence of elements satisfying
    kind. Optionally require elements to be unique.
    
    As a special case, a string is considered to be an atomic value
    rather than a sequence of single-character strings. (Thus,
    checktype_seq('foo', str) will fail.)
    """
    kind = normalize_kind(kind)
    exp = str_kind(kind)
    
    # Make sure we have a sequence.
    try:
        iterator = iter(seq)
        # Generators aren't sequences. This avoids a confusing bug
        # where we consume a generator by type-checking it, and leave
        # only an exhausted iterator for the user code.
        len(seq)
    except TypeError:
        got = str_valtype(seq)
        raise TypeError('Expected sequence of {}; '
                        'got {} instead of sequence'.format(exp, got))
    
    if isinstance(seq, str):
        raise TypeError('Expected sequence of {}; got single str '
                        '(strings do not count as character '
                        'sequences'.format(exp))
        
    for i, item in enumerate(iterator):
        if not isinstance(item, kind):
            got = str_valtype(item)
            raise TypeError('Expected sequence of {}; '
                            'got sequence with {} at position {}'.format(
                            exp, got, i))
    
    if nodups:
        seen = []
        for i, item in enumerate(seq):
            if item in seen:
                raise TypeError('Duplicate element {} at position {}'.format(
                                repr(item), i))
            seen.append(item)


def check_spec(val, kind, mods):
    """Raise TypeError if val does not match the type specification
    given by kind and mods.
    """
    mods = normalize_mods(mods)
    if 'seq' in mods:
        nodups = 'nodups' in mods
        checktype_seq(val, kind, nodups=nodups)
    else:
        checktype(val, kind)