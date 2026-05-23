from pydantic import BaseModel


class SimulateLoginRequest(BaseModel):
    user_id: int | None = None
    device_hash: str
    device_label: str | None = None
    browser: str | None = None
    os: str | None = None
    ip_address: str
    country: str
    city: str
    is_vpn: bool = False
    is_proxy: bool = False
    success: bool = True
    failed_attempts: int = 0


class SimulateTransactionRequest(BaseModel):
    user_id: int | None = None
    to_account: str
    amount: float
    currency: str = "EUR"
    recipient_name: str
    recipient_is_new: bool = False


class SimulateSecurityLogRequest(BaseModel):
    user_id: int | None = None
    event_type: str = "SECURITY_EVENT"
    endpoint: str
    ip_address: str
    payload_sample: str


class SimulateTokenTheftRequest(BaseModel):
    user_id: int | None = None
    session_token_hash: str
    original_ip_address: str
    new_ip_address: str
    original_country: str
    new_country: str
    original_device_hash: str
    new_device_hash: str
    is_vpn: bool = False
    is_proxy: bool = False


class SimulateMuleRingRequest(BaseModel):
    mule_account: str | None = None
    amount: float = 500.0

