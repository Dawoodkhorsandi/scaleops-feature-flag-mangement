import enum


class FeatureFlagAuditActionEnum(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    TOGGLE = "toggle"
    AUTO_DISABLE = "auto_disable"
