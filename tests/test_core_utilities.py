from labthings.core import utilities
import pytest


@pytest.fixture
def example_class():
    class ExampleClass:
        """
        First line of class docstring.
        Second line of class docstring.
        """

        def class_method(self):
            """
            First line of class method docstring.
            Second line of class method docstring.
            """
            return self

        def class_method_no_docstring(self):
            return self

    return ExampleClass


def test_get_docstring(example_class):
    assert (
        utilities.get_docstring(example_class)
        == "First line of class docstring. Second line of class docstring. "
    )

    assert utilities.get_docstring(example_class.class_method) == (
        "First line of class method docstring. Second line of class method docstring. "
    )

    assert utilities.get_docstring(example_class.class_method_no_docstring) == ""


def test_get_summary(example_class):
    assert utilities.get_summary(example_class) == "First line of class docstring."

    assert (
        utilities.get_summary(example_class.class_method)
        == "First line of class method docstring."
    )

    assert utilities.get_summary(example_class.class_method_no_docstring) == ""


# def test_rupdate():
#    d1 = {"a": "String", "b": 5, "c": [], "d": {"a": "String", "b": 5, "c": []}}
#
#    d2 = {
#        "a": "String 2",
#        "b": 50,
#        "c": [10, 20, 30, 40, 50],
#        "d": {"a": "String 2d", "b": 50, "c": [10, 20, 30, 40, 50], "e": ["New list"]},
#    }
#
#    assert utilities.rupdate(d1, d2) == d2


def test_rupdate_granular():
    # Update string value
    s1 = {
        "a": "String",
    }
    s2 = {
        "a": "String 2",
    }
    assert utilities.rupdate(s1, s2) == s2

    # Update int value
    i1 = {
        "b": 5,
    }
    i2 = {"b": 50}
    assert utilities.rupdate(i1, i2) == i2

    # Update list elements
    l1 = {"c": []}
    l2 = {"c": [1, 2, 3, 4]}
    assert utilities.rupdate(l1, l2) == l2

    # Extend list elements
    l1 = {"c": [1, 2, 3]}
    l2 = {"c": [4, 5, 6]}
    assert utilities.rupdate(l1, l2)["c"] == [1, 2, 3, 4, 5, 6]

    # Merge dictionaries
    d1 = {"d": {"a": "String", "b": 5, "c": []}}
    d2 = {
        "d": {"a": "String 2", "b": 50, "c": [1, 2, 3, 4, 5]},
    }
    assert utilities.rupdate(d1, d2) == d2

    # Replace value with list
    ml1 = {"k": True}
    ml2 = {"k": [1, 2, 3]}
    assert utilities.rupdate(ml1, ml2) == ml2

    # Create missing value
    ms1 = {}
    ms2 = {"k": "v"}
    assert utilities.rupdate(ms1, ms2) == ms2

    # Create missing list
    ml1 = {}
    ml2 = {"k": [1, 2, 3]}
    assert utilities.rupdate(ml1, ml2) == ml2

    # Create missing dictionary
    md1 = {}
    md2 = {
        "d": {"a": "String 2", "b": 50, "c": [1, 2, 3, 4, 5]},
    }
    assert utilities.rupdate(md1, md2) == md2


def test_rapply():
    d1 = {
        "a": "String",
        "b": 5,
        "c": [10, 20, 30, 40, 50],
        "d": {"a": "String", "b": 5, "c": [10, 20, 30, 40, 50]},
    }

    def as_str(v):
        return str(v)

    d2 = {
        "a": "String",
        "b": "5",
        "c": ["10", "20", "30", "40", "50"],
        "d": {"a": "String", "b": "5", "c": ["10", "20", "30", "40", "50"]},
    }

    assert utilities.rapply(d1, as_str) == d2

    d2_no_iter = {
        "a": "String",
        "b": "5",
        "c": "[10, 20, 30, 40, 50]",
        "d": {"a": "String", "b": "5", "c": "[10, 20, 30, 40, 50]"},
    }

    assert utilities.rapply(d1, as_str, apply_to_iterables=False) == d2_no_iter


def test_get_by_path():
    d1 = {"a": {"b": "String"}}

    assert utilities.get_by_path(d1, ("a", "b")) == "String"


def test_set_by_path():
    d1 = {"a": {"b": "String"}}

    utilities.set_by_path(d1, ("a", "b"), "Set")

    assert d1["a"]["b"] == "Set"


def test_create_from_path():
    assert utilities.create_from_path(["a", "b", "c"]) == {"a": {"b": {"c": {}}}}


def test_camel_to_snake():
    assert utilities.camel_to_snake("SomeCamelString") == "some_camel_string"


def test_camel_to_spine():
    assert utilities.camel_to_spine("SomeCamelString") == "some-camel-string"


def test_snake_to_spinee():
    assert utilities.snake_to_spine("some_snake_string") == "some-snake-string"
