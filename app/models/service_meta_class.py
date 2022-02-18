class MetaService(type):
    def __new__(cls, name: str, bases, namespace, **kwargs):
        if not name.startswith('Srv'):
            raise TypeError('[Fatal] Invalid Service Statement: class name should start with "Srv"', name)
        return super().__new__(cls, name, bases, namespace, **kwargs)

class HPCMetaService(type):
    def __new__(cls, name: str, bases, namespace, **kwargs):
        if not name.startswith('HPC'):
            raise TypeError('[Fatal] Invalid Service Statement: class name should start with "Srv"', name)
        return super().__new__(cls, name, bases, namespace, **kwargs)