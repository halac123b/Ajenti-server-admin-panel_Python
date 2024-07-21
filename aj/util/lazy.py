import logging


class LazyModule:
    """Mô phỏng lại cách import module"""

    def __init__(self, module, obj=None):
        # Module cần import
        self._module = module
        # Các field của module cần import
        self._object = obj
        self._loaded = False

    def __load(self):
        logging.debug(f"Lazy-loading module {self._module}")
        # Dynamic load 1 module
        target = __import__(self._module, fromlist=[str(self._module)])
        # Get 1 field object từ module
        if self._object:
            target = getattr(target, self._object)

        # Lấy các field con từ field vừa lấy đc
        for k in dir(target):
            try:
                self.__dict__[k] = getattr(target, k)
            except AttributeError:
                pass

        self._loaded = True

    def __getattr__(self, attr):
        """Get 1 field cụ thể từ object đc import"""
        if not self._loaded:
            self.__load()
        return self.__dict__[attr]
