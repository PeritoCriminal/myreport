# report_maker/signals/__init__.py

"""
Pacote responsável pelo registro dos signals do app report_maker.

Os módulos são importados para que os decorators @receiver
sejam devidamente registrados quando o app é carregado.
"""

from . import image  # noqa
from . import examobject  # noqa
from . import reportcase  # noqa
