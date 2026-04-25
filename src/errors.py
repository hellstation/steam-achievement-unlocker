class AppError(Exception):
    pass


class AuthError(AppError):
    pass


class PrivacyError(AppError):
    pass


class NetworkError(AppError):
    pass


class APIResponseError(AppError):
    pass


class ConfigError(AppError):
    pass
