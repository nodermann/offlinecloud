class NameRelatedError(Exception):
    name: str

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name

class NoQueryParameter(NameRelatedError): pass
class InvalidQueryParameter(NameRelatedError): pass
class NoJsonKey(NameRelatedError): pass
class InvalidJsonKey(NameRelatedError): pass
class NoMultipart(NameRelatedError): pass
class InvalidMultipart(NameRelatedError): pass
