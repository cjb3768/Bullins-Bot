import pkgutil

#package to inspect
import Commands

package = Commands
prefix = package.__name__ + "."
modules = {}
for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
    submodname = modname.split('.', 1)[-1]

    print("found submodule {} (is a package: {})".format(modname, ispkg))
    module = importer.find_module(modname).load_module(modname)
    print("Imported ", module)

    modules[submodname] = module

#print(modules)
modules['roll'].execute()

for mod in ['echo', 'roll', 'dne']:
    try:
        print("'{}': {}".format(mod, modules[mod].execute.__doc__))
    except KeyError:
        print("Unknown module '{}'!".format(mod))
