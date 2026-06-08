class AppException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class NotFoundException(AppException):
    def __init__(self, msg):
        super().__init__(msg)


class MethodNotAllowedException(AppException):
    def __init__(self, msg):

        super().__init__(msg)


class ValidationException(AppException):
    def __init__(self, msg):
        super().__init__(msg)
