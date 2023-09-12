# Copyright (C) 2022-2023 Indoc Systems
#
# Contact Indoc Systems for any questions regarding the use of this source code.


class MetaService(type):
    def __new__(cls, name: str, bases, namespace, **kwargs):
        if not name.startswith('Srv'):
            raise TypeError('[Fatal] Invalid Service Statement: class name should start with "Srv"', name)
        return super().__new__(cls, name, bases, namespace, **kwargs)
