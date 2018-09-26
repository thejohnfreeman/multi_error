import io
from typing import Callable, cast, List, Type, Tuple, Union


Predicate = Callable[[BaseException], bool]

Predicates = Union[
    Type[BaseException],
    Tuple[Type[BaseException], ...],
]

PredicateLike = Union[
    Predicates,
    Predicate,
]

SplitError = Tuple[Union['MultiError', None], Union['MultiError', None]]


class MultiError(Exception):

    def __init__(self, errors: List[BaseException]) -> None:
        self.errors = errors

    @property
    def size(self) -> int:
        return sum(map(_sizeof, self.errors))

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _tree(self).getvalue()

    @staticmethod
    def split(predicate: PredicateLike, error: 'MultiError') -> SplitError:
        predicate = _predicate(predicate)
        ys = cast(List[BaseException], [])
        ns = cast(List[BaseException], [])
        for child in error.errors:
            if isinstance(child, MultiError):
                y, n = MultiError.split(predicate, child)
                if y is not None:
                    ys.append(y)
                if n is not None:
                    ns.append(n)
            elif predicate(child):
                ys.append(child)
            else:
                ns.append(child)
        # TODO: Copy over traceback and other context.
        match = MultiError(ys) if ys else None
        rest = MultiError(ns) if ns else None
        return (match, rest)


def _predicate(input: PredicateLike) -> Predicate:
    if callable(input) and not isinstance(input, type):
        return cast(Predicate, input)
    return lambda e: isinstance(e, cast(Predicates, input))


def _sizeof(error: BaseException) -> int:
    return error.size if isinstance(error, MultiError) else 1


def _repr(error: BaseException) -> str:
    if isinstance(error, MultiError):
        return f"MultiError([{', '.join(map(_repr, error.errors))}])"
    return error.__class__.__name__


def _tree(parent: BaseException, closed=0, opened=0, file=None):
    """Pretty-print a tree-like representation of a MultiError."""
    if file is None:
        file = io.StringIO()
    print(parent.__class__.__name__, end='', file=file)
    if isinstance(parent, MultiError):
        n = len(parent.errors)
        # Print the suffix.
        print(f' |{parent.size}|', file=file)
        # Print the children.
        for i, child in enumerate(parent.errors, 1):
            # TODO: Truncate at some threshold.
            last = i == n
            print('    ' * closed, end='', file=file)
            print('│   ' * opened, end='', file=file)
            print('└── ' if last else '├── ', end='', file=file)
            _tree(
                child,
                closed=closed + last,
                opened=opened + (not last),
                file=file
            )
    else:
        print(file=file)
    return file
