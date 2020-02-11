from threading import ThreadError


class LockError(ThreadError):
    ERROR_CODES = {
        "ACQUIRE_ERROR": "Unable to acquire. Lock in use by another thread.",
        "IN_USE_ERROR": "Lock in use by another thread.",
    }

    def __init__(self, code, lock):
        self.code = code
        if code in LockError.ERROR_CODES:
            self.message = LockError.ERROR_CODES[code]
        else:
            self.message = "Unknown error."

        self.string = f"{self.code}: LOCK {lock}: {self.message}"
        print(self.string)

        ThreadError.__init__(self)

    def __str__(self):
        return self.string
