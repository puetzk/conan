import unittest
from conans.test.tools import TestServer, TestClient
from conans.model.ref import ConanFileReference
import os
from conans.test.utils.cpp_test_files import cpp_hello_conan_files
from conans.paths import CONANFILE, CONANFILE_TXT
from conans.util.files import load


generator = """
from conans.model import Generator
from conans.paths import BUILD_INFO
from conans import ConanFile, CMake

class MyCustomGenerator(Generator):
    @property
    def filename(self):
        return "customfile.gen"

    @property
    def content(self):
        return "My custom generator content"


class MyCustomGeneratorPackage(ConanFile):
    name = "MyCustomGen"
    version = "0.2"
"""

consumer = """
[requires]
Hello0/0.1@lasote/stable
MyCustomGen/0.2@lasote/stable

[generators]
MyCustomGenerator
"""


class CustomGeneratorTest(unittest.TestCase):

    def setUp(self):
        test_server = TestServer([("*/*@*/*", "*")],  # read permissions
                                 [],  # write permissions
                                 users={"lasote": "mypass"})  # exported users and passwords
        self.servers = {"default": test_server}

    def reuse_test(self):
        conan_reference = ConanFileReference.loads("Hello0/0.1@lasote/stable")
        files = cpp_hello_conan_files("Hello0", "0.1")
        files[CONANFILE] = files[CONANFILE].replace("build(", "build2(")
        client = TestClient(servers=self.servers, users={"default": [("lasote", "mypass")]})
        client.save(files)
        client.run("export lasote/stable")
        client.run("upload %s" % str(conan_reference))

        gen_reference = ConanFileReference.loads("MyCustomGen/0.2@lasote/stable")
        files = {CONANFILE: generator}
        client = TestClient(servers=self.servers, users={"default": [("lasote", "mypass")]})
        client.save(files)
        client.run("export lasote/stable")
        client.run("upload %s" % str(gen_reference))

        # Test local, no retrieval
        files = {CONANFILE_TXT: consumer}
        client.save(files, clean_first=True)
        client.run("install --build")
        generated = load(os.path.join(client.current_folder, "customfile.gen"))
        self.assertEqual(generated, "My custom generator content")

        # Test retrieval from remote
        client = TestClient(servers=self.servers, users={"default": [("lasote", "mypass")]})
        files = {CONANFILE_TXT: consumer}
        client.save(files)
        client.run("install --build")

        generated = load(os.path.join(client.current_folder, "customfile.gen"))
        self.assertEqual(generated, "My custom generator content")