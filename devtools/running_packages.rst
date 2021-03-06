.. _running_packages:

Running and deploying packages
================================
Executables and applications including shared libraries can be also distributed, deployed and run with conan. This might have
some advantages compared to deploying with other systems:

- A unified development and distribution tool, for all systems and platforms
- Manage any number of different deployment configurations in the same way you manage them for development
- Use a conan server remote to store all your applications and runtimes for all Operating Systems, platforms and targets

There are different approaches:

Using virtual environments
---------------------------

We can crate a package that contains an executable, for example from the default package template created by ``conan new``:

.. code-block:: bash

    $ conan new Hello/0.1

The source code used contains an executable called ``greet``, but it is not packaged by default. Lets modify the recipe
``package()`` method to also package the executable:

.. code-block:: python

    def package(self):
        self.copy("*greet*", src="hello/bin", dst="bin", keep_path=False)


Now, we can create the package as usual, but if we try to run the executable, it won't be found:

.. code-block:: bash

    $ conan create user/testing
    ...
    Hello/0.1@user/testing package(): Copied 1 '.h' files: hello.h
    Hello/0.1@user/testing package(): Copied 1 '.exe' files: greet.exe
    Hello/0.1@user/testing package(): Copied 1 '.lib' files: hello.lib

    $ greet
    > ... not found...


Conan does not modify by default the environment, it will just create the package in the local cache, and that is not
in the system PATH, so the ``greet`` executable is not found.

The ``virtualrunenv`` generator will generate files that add the packages default binary locations to the necessary paths:

- It adds the dependencies ``lib`` subfolder to the ``DYLD_LIBRARY_PATH`` environment variable (for OSX shared libraries)
- It adds the dependencies ``lib`` subfolder to the ``LD_LIBRARY_PATH`` environment variable (for Linux shared libraries)
- It adds the dependencies ``bin`` subfolder to the ``PATH`` environment variable (for executables)

So if we install the package, specifying such ``virtualenv`` like:

.. code-block:: bash

    $ conan install Hello/0.1@user/testing -g virtualrunenv

We will get some files, that can be called to activate and deactivate such environment variables

.. code-block:: bash

    $ activate # $ source activate in nix
    $ greet
    > Hello World!


Imports
--------
It is possible to define a custom conanfile (either .txt or .py), with an ``imports`` section, that can retrieve from local
cache the desired files. This approach, requires a user conanfile, so it might not be very convenient.


Deployable packages
--------------------
With the ``deploy()`` method, a package can specify which files and artifacts to copy to user space, of to other locations
in the system. In the above example we could add to our ``Hello`` conanfile.py, and run ``conan create`` again:

.. code-block:: python

    def deploy(self):
        self.copy("*", dst="bin", src="bin")


With that method in our package recipe, it will copy the executable when installed directly:

.. code-block:: bash

    $ conan install Hello/0.1@user/testing
    ...
    > Hello/0.1@user/testing deploy(): Copied 1 '.exe' files: greet.exe
    $ bin\greet.exe
    > Hello World!

The deploy will create a ``deploy_manifest.txt`` file with the files that have been deployed.

Read more about ``deploy()`` in the reference.

Running from packages
----------------------
If you want to directly run one executable from your dependencies, it is not necessary to use the generators
and activate the environment, as it can be directly done in code with the ``RunEnvironment`` helper. So if
the ``Consumer`` package is willing to execute the ``greet`` app while building its own package, it can be done:

.. code-block:: python

    from conans import ConanFile, tools, RunEnvironment

    class ConsumerConan(ConanFile):
        name = "Consumer"
        version = "0.1"
        settings = "os", "compiler", "build_type", "arch"
        requires = "Hello/0.1@user/testing"

        def build(self):
            env = RunEnvironment(self)
            with tools.environment_append(env.vars):
                self.run("greet")

Instead of using the environment, it is also possible to access the path of the dependencies:

.. code-block:: python

    def build(self):
        path = os.path.join(self.deps_cpp_info["Hello"].rootpath, "bin")
        self.run("%s/greet" % path)

Note, however, that this might not be enough if shared libraries exist, while using the above ``RunEnvironment``
is a more complete solution


Finally, there is another approach: the package containing the executable, adds its "bin" folder to the PATH.
In this case the **Hello** package conanfile would contain:

.. code-block:: python

    def package_info(self):
        self.cpp_info.libs = ["hello"]
        self.env_info.PATH = os.path.join(self.package_folder, "bin")

Note that this is not enough for shared libraries, and defining DYLD_LIBRARY_PATH and LD_LIBRARY_PATH could be
necessary.

The consumer package would be simple, as the PATH environment variable will already contain the desired path
to greet executable:

.. code-block:: python

    def build(self):
        self.run("greet")


.. _repackage:

Runtime packages and re-packaging
----------------------------------
It is possible to create packages that contain only runtime binaries, getting rid of all build-time dependencies.
If we want to create a package from the above "Hello" one, but only containing the executable (rembember that the above
package also contains a library, and the headers), we could do:

.. code-block:: python

    from conans import ConanFile

    class HellorunConan(ConanFile):
        name = "HelloRun"
        version = "0.1"
        build_requires = "Hello/0.1@user/testing"
        keep_imports = True

        def imports(self):
            self.copy("*.exe", dst="bin")
            
        def package(self):
            self.copy("*")


This recipe has the following characteristics:

- It includes the ``Hello/0.1@user/testing`` package as ``build_requires``.
  That means that it will be used to build this "HelloRun" package, but once the "HelloRun" package is built,
  it will not be necessary to retrieve it.
- It is using an ``imports()`` to copy from the dependencies, in this case, the executable
- It is using ``keep_imports`` attribute to define that imported artifacts during the ``build()`` step (which
  is not define, then using the default empty one), are kept and not removed after build
- The ``package()`` method packages the imported artifacts that will be in the build folder.


Installing and running this package, can be done by any of the means presented above, for example, we could do:

.. code-block:: bash

    $ conan install HelloRun/0.1@user/testing -g virtualrunenv
    # It will not install Hello/0.1@...
    $ activate
    $ greet
    > Hello World!




