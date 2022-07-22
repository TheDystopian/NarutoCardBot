class AccessDenied(Exception):
    """Raised when something not allowed"""

    pass


class NotEnough(Exception):
    """Raised when not enogh something"""

    pass

class NoCards(Exception):
    """Raised when there is no available cards"""
    
    pass

class NoCardsUpgrade(Exception):
    """Raised when there is no suitable cards to upgrade"""
    
    pass


class NoPack(Exception):
    """Raised when there is no such pack"""
    
    pass

class NoUser(Exception):
    """Raised when this user is not registered in database"""
    
    pass

class NoBattles(Exception):
    """Raised when this user has no battle points left"""
    
    pass

class CardDoNotExist(Exception):
    """Raised when there is no card exist"""
    
    pass

class NoCardsToDestroy(Exception):
    """Raised when there is no card to destroy"""
    
    pass