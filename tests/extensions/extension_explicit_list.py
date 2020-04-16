from labthings.server.extensions import BaseExtension

test_extension = BaseExtension("org.labthings.tests.extension")
test_extension_excluded = BaseExtension("org.labthings.tests.extension_excluded")

__extensions__ = ["test_extension"]
