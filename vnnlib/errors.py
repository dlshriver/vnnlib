class VnnLibError(Exception):
    pass


class TokenizerError(VnnLibError):
    pass


class ParserError(VnnLibError):
    pass


__all__ = ["ParserError", "TokenizerError", "VnnLibError"]
