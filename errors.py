class AccessDenied(Exception):
    """Raised when something not allowed"""

    pass


class NotEnough(Exception):
    """Raised when not enogh something"""

    pass

class NoCards(Exception):
    """Raised when there is no suitable command"""
    
    pass

class NoPack(Exception):
    """Raised when there is no suitable command"""
    
    pass
class NoUser(Exception):
    """Raised when this user is not registered in database"""
    
    pass

class NoBattles(Exception):
    """Raised when this user is not registered in database"""
    
    pass
