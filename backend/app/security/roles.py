from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    DATA_ADMIN = "DATA_ADMIN"
    ANALYST = "ANALYST"
    BUSINESS_USER = "BUSINESS_USER"
    DECISION_MAKER = "DECISION_MAKER"
    EXTERNAL_PARTNER = "EXTERNAL_PARTNER"


ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        "manage_users",
        "manage_roles",
        "manage_data",
        "view_analytics",
        "run_analysis",
        "run_simulations",
        "view_recommendations",
        "approve_recommendations",
        "execute_actions",
        "view_audit_logs",
    },

    UserRole.DATA_ADMIN: {
        "manage_data",
        "view_analytics",
        "run_analysis",
        "view_audit_logs",
    },

    UserRole.ANALYST: {
        "view_analytics",
        "run_analysis",
        "run_simulations",
    },

    UserRole.BUSINESS_USER: {
        "view_analytics",
        "run_simulations",
    },

    UserRole.DECISION_MAKER: {
        "view_analytics",
        "run_simulations",
        "view_recommendations",
        "approve_recommendations",
        "execute_actions",
    },

    UserRole.EXTERNAL_PARTNER: {
        "view_analytics",
    },
}


def has_permission(role: str, permission: str) -> bool:
    try:
        user_role = UserRole(role)
    except ValueError:
        return False

    return permission in ROLE_PERMISSIONS.get(user_role, set())