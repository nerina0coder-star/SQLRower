from typing import Any


def validator(*args):
    """
    validates arguments.

    The args must be structured like this:


    (
        name,

        checking,

        wanted_type,

        optional validator with message as a tuple with length 2

    ), (
        follow the pattern...
    ).
    """
    # Validating the given params
    if not all(isinstance(i, tuple) and (len(i) == 3 or len(i) == 4) for i in args):
        raise ValueError("All elements of args must be tuple with length 3 or 4")

    args: tuple[tuple[Any, ...]] = args # For type-hints

    for arg in args:
        name = arg[0]
        checking = arg[1]
        wanted_type = arg[2]
        optional_value = None if len(arg) == 3 else arg[3] # 1st is validator, 2nd is the message.

        if not isinstance(wanted_type, tuple):
            if isinstance(wanted_type, type):
                wanted_type = (wanted_type,)
            else:
                raise ValueError("'wanted_type' must be type tuple")

        if (checking is None and None not in wanted_type) or \
                not isinstance(checking, wanted_type):
            raise TypeError(f"{name} must be {wanted_type[0].__name__}{"".join(f" or {w.__name__}" for w in wanted_type[1:])}, got {type(checking).__name__} instead.")

        if optional_value is not None and \
                isinstance(optional_value, tuple) and \
                len(optional_value) == 2 and \
                callable(optional_value[0]):
            if not optional_value[0]():
                raise ValueError(optional_value[1])
