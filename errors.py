class EcoleDirecteError(Exception):
    pass


class APIError(EcoleDirecteError):
    pass


class DownloadError(EcoleDirecteError):
    pass


class LoginError(EcoleDirecteError):
    pass
