import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    BarberAdmin = "barber_admin"
    USER = "user"
    BARBER = "barber"
    MODERATOR = "moderator"