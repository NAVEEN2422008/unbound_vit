"""
Authentication & Role-Based Access Control (RBAC) security dependency for FINRES.
Supports API-Key and Bearer Token authentication with granular role authorization.
"""
from fastapi import Header, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from src_py.core.response import TokenData

security_bearer = HTTPBearer(auto_error=False)

# Standard credentials mapped to required USER ROLES: CUSTOMER, BANKER, ADMIN
VALID_API_KEYS = {
    "FINRES_CREDIT_OFFICER_KEY_2026": TokenData(
        user_id="OFFICER_BALA_772",
        role="BANKER",
        permissions=["read:portfolio", "write:restructure", "write:intervene", "approve:human_review"]
    ),
    "FINRES_BANKER_KEY_2026": TokenData(
        user_id="BANKER_SUNDARAM_01",
        role="BANKER",
        permissions=["read:portfolio", "write:restructure", "write:intervene", "approve:human_review"]
    ),
    "FINRES_RISK_ANALYST_KEY_2026": TokenData(
        user_id="ANALYST_MEERA_109",
        role="BANKER",
        permissions=["read:portfolio", "read:diagnostics", "simulate:twin"]
    ),
    "FINRES_ADMIN_KEY_2026": TokenData(
        user_id="ADMIN_SYSTEM_ROOT",
        role="ADMIN",
        permissions=["read:all", "write:all", "admin:all"]
    ),
    "FINRES_AUDITOR_DPDP_KEY_2026": TokenData(
        user_id="AUDITOR_RBI_441",
        role="ADMIN",
        permissions=["read:audit_logs", "read:governance", "verify:dpdp"]
    ),
    "FINRES_CUSTOMER_PORTAL_KEY_2026": TokenData(
        user_id="CUST_PORTAL_USER",
        role="CUSTOMER",
        permissions=["read:dashboard", "write:consent"]
    )
}


def authenticate_user(
    x_api_key: Optional[str] = Header(default="FINRES_CREDIT_OFFICER_KEY_2026", alias="X-API-KEY"),
    auth: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> TokenData:
    """
    Authenticates requests using X-API-KEY header or Bearer token.
    Defaults to CREDIT_OFFICER for seamless developer local testing.
    """
    token_key = x_api_key
    if auth and auth.credentials in VALID_API_KEYS:
        token_key = auth.credentials

    if not token_key or token_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials (X-API-KEY)."
        )

    return VALID_API_KEYS[token_key]


def require_roles(allowed_roles: List[str]):
    def role_checker(user: TokenData = Security(authenticate_user)) -> TokenData:
        if user.role not in allowed_roles and "ADMIN" not in user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles {allowed_roles}. Current role: {user.role}"
            )
        return user
    return role_checker
