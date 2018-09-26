import io


class MultiError(Exception):

    def __init__(self, errors):
        self.errors = errors
        self.size = sum(map(_sizeof, errors))

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _tree(self).getvalue()


def _sizeof(error):
    return error.size if isinstance(error, MultiError) else 1


def _repr(error):
    if isinstance(error, MultiError):
        return f"MultiError([{', '.join(map(_repr, error.errors))}])"
    return error.__class__.__name__


def _tree(parent: MultiError, closed=0, opened=0, file=None):
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
