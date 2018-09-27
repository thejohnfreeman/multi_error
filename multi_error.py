from async_generator import asynccontextmanager
from contextlib import contextmanager
import io
from typing import Any, Callable, cast, List, Optional, Type, Tuple, Union


Predicate = Callable[[BaseException], bool]

Predicates = Union[
    Type[BaseException],
    Tuple[Type[BaseException], ...],
]

PredicateLike = Union[
    Predicates,
    Predicate,
]

SplitError = Tuple[Optional[BaseException], Optional[BaseException]]


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

    def _copy_with(self, *args, **kwargs):
        """Copy this exception but with different arguments.

        Special attributes of exceptions (:attribute:`__context__`,
        :attribute:`__cause__`, and :attribute:`__traceback__`) are copied
        over to the new exception from this exception.

        Parameters
        ----------
        errors :
            A list of exceptions.

        Returns
        -------
        MultiError
            A copy of this exception, but with different arguments.
        """
        copy = self.__class__(*args, **kwargs)
        copy.__context__ = self.__context__
        copy.__cause__ = self.__cause__
        copy.__traceback__ = self.__traceback__
        return copy

    @staticmethod
    def split(predicate: PredicateLike, error: BaseException) -> SplitError:
        # Normalize our parameters.
        predicate = _predicate(predicate)

        # Handle exceptions that are not :class:`MultiError`.
        if not isinstance(error, MultiError):
            return (error, None) if predicate(error) else (None, error)

        # Yeses and noes.
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

        match = error._copy_with(ys) if ys else None
        rest = error._copy_with(ns) if ns else None
        return (match, rest)

    @staticmethod
    @contextmanager
    def catch(
            predicate: PredicateLike, handler: Callable[['MultiError'], Any],
    ):
        try:
            yield
        except BaseException as error:
            with _catching(predicate, error) as caught:
                handler(cast(MultiError, caught))

    @staticmethod
    @asynccontextmanager
    async def acatch(
            predicate: PredicateLike, handler: Callable[['MultiError'], Any],
    ):
        try:
            yield
        except BaseException as error:
            with _catching(predicate, error) as caught:
                await handler(cast(MultiError, caught))


@contextmanager
def _catching(predicate: PredicateLike, error: BaseException):
    caught, rest = MultiError.split(predicate, error)
    if caught is not None:
        yield caught
    if rest is not None:
        raise rest


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
