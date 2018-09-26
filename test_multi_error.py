from multi_error import MultiError
from pytest import fixture


@fixture()
def multi_error1():
    return MultiError([
        RuntimeError('a'),
        MultiError([
            RuntimeError('b'),
            ValueError(),
        ]),
    ])


@fixture()
def multi_error2():
    return MultiError([
        MultiError([
            RuntimeError('a'),
            MultiError([
                RuntimeError('b'),
                ValueError(),
            ]),
            ValueError(),
        ]),
        RuntimeError('c'),
        MultiError([
            RuntimeError('d'),
            ValueError(),
            MultiError([
                RuntimeError('e'),
                ValueError(),
            ]),
        ]),
    ])


def test_size(multi_error1):
    assert multi_error1.size == 3


def test_repr(multi_error1):
    assert (
        repr(multi_error1) ==
        'MultiError([RuntimeError, MultiError([RuntimeError, ValueError])])'
    )


def test_str(multi_error1):
    s = str(multi_error1)
    # We *could* test the literal output, but I just want a sanity check.
    # The output is meant to be human-readable; it does not have a schema.
    assert isinstance(s, str) and len(s) > 20


def test_split(multi_error1):
    match, rest = MultiError.split(RuntimeError, multi_error1)
    assert (
        repr(match) ==
        'MultiError([RuntimeError, MultiError([RuntimeError])])'
    )
    assert repr(rest) == 'MultiError([MultiError([ValueError])])'
