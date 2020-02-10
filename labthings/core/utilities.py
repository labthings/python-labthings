import collections.abc
import re
import operator
import sys
from functools import reduce

PY3 = sys.version_info > (3,)


def get_docstring(obj, remove_newlines=True):
    """Return the docstring of an object
    
    Args:
        obj: Any Python object
        remove_newlines (bool): Remove newlines from the docstring (default: {True})
    
    Returns:
        str: Object docstring
    """
    ds = obj.__doc__
    if ds:
        stripped = [line.strip() for line in ds.splitlines() if line]
        if not remove_newlines:
            return "\n".join(stripped)
        return " ".join(stripped).replace("\n", " ").replace("\r", "")
    return ""


def get_summary(obj):
    """Return the first line of the dosctring of an object
    
    Args:
        obj: Any Python object
    
    Returns:
        str: First line of object docstring
    """
    print(get_docstring(obj, remove_newlines=False))
    return get_docstring(obj, remove_newlines=False).partition("\n")[0].strip()


def rupdate(destination_dict, update_dict):
    """Recursively update a dictionary

    This will take an "update_dictionary", 
    and recursively merge it with "destination_dict".
    
    Args:
        destination_dict (dict): Original dictionary
        update_dict (dict): New data dictionary
    
    Returns:
        dict: Merged dictionary
    """
    for k, v in update_dict.items():
        # Merge lists if they're present in both objects
        if isinstance(v, list):
            if not k in destination_dict:
                destination_dict[k] = []
            if isinstance(destination_dict[k], list):
                destination_dict[k].extend(v)
        # Recursively merge dictionaries if the element is a dictionary
        elif isinstance(v, collections.abc.Mapping):
            if not k in destination_dict:
                destination_dict[k] = {}
            destination_dict[k] = rupdate(destination_dict.get(k, {}), v)
        # If not a list or dictionary, overwrite old value with new value
        else:
            destination_dict[k] = v
    return destination_dict


def rapply(data, func, *args, apply_to_iterables=True, **kwargs):
    """
    Recursively apply a function to a dictionary, list, array, or tuple

    Args:
        data: Input iterable data
        func: Function to apply to all non-iterable values
        apply_to_iterables (bool): Apply the function to elements in lists/tuples

    Returns:
        dict: Updated dictionary
    """

    # If the object is a dictionary
    if isinstance(data, collections.abc.Mapping):
        return {
            key: rapply(
                val, func, *args, apply_to_iterables=apply_to_iterables, **kwargs
            )
            for key, val in data.items()
        }
    # If the object is iterable but NOT a dictionary or a string
    elif apply_to_iterables and (
        isinstance(data, collections.abc.Iterable)
        and not isinstance(data, collections.abc.Mapping)
        and not isinstance(data, str)
    ):
        return [
            rapply(x, func, *args, apply_to_iterables=apply_to_iterables, **kwargs)
            for x in data
        ]
    # if the object is neither a map nor iterable
    else:
        return func(data, *args, **kwargs)


def get_by_path(root, items):
    """Access a nested object in root by item sequence."""
    return reduce(operator.getitem, items, root)


def set_by_path(root, items, value):
    """Set a value in a nested object in root by item sequence."""
    get_by_path(root, items[:-1])[items[-1]] = value


def create_from_path(items):
    """Create a dictionary from a list of nested keys.RuntimeError

    E.g. ["foo", "bar", "baz"] will become
    {
        "foo": {
            "bar": {
                "baz": {}
            }
        }
    }
    
    Args:
        items (list): Key path
    
    Returns:
        dict: Nested dictionary of key path
    """
    tree_dict = {}
    for key in reversed(items):
        tree_dict = {key: tree_dict}
    return tree_dict


def camel_to_snake(name):
    """Convert a CamelCase string into snake_case
    
    Args:
        name (str): CamelCase string
    
    Returns:
        str: snake_case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def camel_to_spine(name):
    """Convert a CamelCase string into spine-case
    
    Args:
        name (str): CamelCase string
    
    Returns:
        str: spine-case string
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()


def snake_to_spine(name):
    """Convert a snake_case string into spine-case
    
    Args:
        name (str): snake_case string
    
    Returns:
        str: spine-case string
    """
    return name.replace("_", "-")
