
class Auditable:
    """
    A simple marker mixin class.

    Any SQLAlchemy model that inherits from this class will be automatically
    registered for audit logging by the event listener system.
    """
    pass