"""
KNOUX OS Guardian - REST API Layer
Exposes all 12 modules as RESTful endpoints with JWT auth, RBAC, async execution, and audit logging
"""

import asyncio
import json
import os

# Import all 12 modules
import sys
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import jwt
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.config import get_config

# Initialize FastAPI app
app = FastAPI(
    title="KNOUX OS Guardian API",
    description="REST API for all 12 system modules with JWT auth, RBAC, and async execution",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "knoux-os-guardian-secret-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In-memory storage for audit logs and async tasks
audit_logs: List[Dict[str, Any]] = []
async_tasks: Dict[str, Dict[str, Any]] = {}

# Token blacklist for logout/invalidation (in-memory; replace with persistent store in production)
blacklisted_tokens: set[str] = set()

# Test users (as required by integration instructions)
users_db: Dict[str, Dict[str, Any]] = {
    "admin_user": {
        "username": "admin_user",
        "password": "admin123",
        "roles": ["admin"],
        "disabled": False,
    },
    "analyst_user": {
        "username": "analyst_user",
        "password": "analyst123",
        "roles": ["analyst"],
        "disabled": False,
    },
    "viewer_user": {
        "username": "viewer_user",
        "password": "viewer123",
        "roles": ["viewer"],
        "disabled": False,
    },
}


# Pydantic Models
class Token(BaseModel):
    correlation_id: Optional[str] = None
    access_token: str
    token_type: str
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    correlation_id: str
    status: str
    message: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    username: Optional[str] = None
    roles: List[str] = []


class User(BaseModel):
    username: str
    roles: List[str]
    disabled: bool = False


class UserInDB(User):
    password: str


class ModuleStatus(BaseModel):
    correlation_id: Optional[str] = None
    module_name: str
    enabled: bool
    last_run: Optional[datetime]
    status: str
    health_score: float = Field(ge=0, le=100)


class ExecutionRequest(BaseModel):
    run_mode: str = Field(
        "immediate", description="Execution mode: 'immediate' or 'async'"
    )
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(
        "normal", description="Priority: 'low', 'normal', 'high', 'critical'"
    )


class ExecutionResponse(BaseModel):
    correlation_id: Optional[str] = None
    run_id: str
    module_name: str
    status: str
    run_mode: str
    started_at: datetime
    completed_at: Optional[datetime]
    severity: str = Field(
        "info", description="Severity: 'info', 'low', 'medium', 'high', 'critical'"
    )
    details: Dict[str, Any] = Field(default_factory=dict)
    message: str


class AsyncTaskStatus(BaseModel):
    correlation_id: Optional[str] = None
    run_id: str
    module_name: str
    status: str
    progress: float = Field(ge=0, le=100)
    started_at: datetime
    estimated_completion: Optional[datetime]
    result: Optional[Dict[str, Any]]


class AuditLog(BaseModel):
    correlation_id: Optional[str] = None
    audit_id: str
    timestamp: datetime
    module_name: str
    action: str
    run_id: Optional[str]
    actor: str
    actor_role: str
    severity: str
    status: str
    metadata: Dict[str, Any]


class PaginatedResponse(BaseModel):
    correlation_id: Optional[str] = None
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class MetricsResponse(BaseModel):
    correlation_id: str
    timestamp: str
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_connections: int


class AlertItem(BaseModel):
    alert_id: str
    timestamp: str
    severity: str
    title: str
    description: str
    module_name: Optional[str] = None
    run_id: Optional[str] = None


class AlertsResponse(BaseModel):
    correlation_id: str
    items: List[AlertItem]
    total: int


class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float


class NetworkMetrics(BaseModel):
    active_connections: int
    bytes_sent: int
    bytes_received: int


class MonitoringMetricsResponse(BaseModel):
    correlation_id: str
    timestamp: str
    system: SystemMetrics
    network: NetworkMetrics
    modules: Dict[str, Dict[str, Any]]


class Alert(BaseModel):
    id: str
    severity: str
    title: str
    message: str
    source: str
    module: Optional[str] = None
    created_at: str
class AlertsSummary(BaseModel):
    total: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    unacknowledged: int


class MonitoringAlertsResponse(BaseModel):
    correlation_id: str
    alerts: List[Alert]
    summary: AlertsSummary


class PaginationInfo(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class AuditLogsResponse(BaseModel):
    correlation_id: str
    logs: List[Dict[str, Any]]
    pagination: PaginationInfo


class SettingsPayload(BaseModel):
    changes: Dict[str, Any]


class HealthResponse(BaseModel):
    correlation_id: str
    status: str
    timestamp: str
    version: str
    modules_available: int


# Authentication and Authorization
def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user or user["password"] != password:
        return False
    return UserInDB(**user)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials

        if token in blacklisted_tokens:
            raise credentials_exception

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])

        if username is None:
            raise credentials_exception

        token_data = TokenData(username=username, roles=roles)
    except InvalidTokenError:
        raise credentials_exception

    user = users_db.get(token_data.username)
    if user is None:
        raise credentials_exception

    return User(**user)


def require_roles(*allowed_roles: str):
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return role_checker


# Audit logging
def log_audit_event(
    request: Request,
    module_name: str,
    action: str,
    run_id: Optional[str] = None,
    actor: Optional[User] = None,
    severity: str = "info",
    status: str = "success",
    metadata: Optional[Dict] = None,
):
    audit_id = str(uuid.uuid4())

    # Get client info
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    audit_entry = {
        "correlation_id": getattr(request.state, "correlation_id", None),
        "audit_id": audit_id,
        "timestamp": datetime.utcnow(),
        "module_name": module_name,
        "action": action,
        "run_id": run_id,
        "actor": actor.username if actor else "system",
        "actor_role": actor.roles[0] if actor and actor.roles else "system",
        "severity": severity,
        "status": status,
        "metadata": {
            "source_ip": client_host,
            "user_agent": user_agent,
            "correlation_id": getattr(request.state, "correlation_id", None),
            "parameters": metadata.get("parameters", {}) if metadata else {},
            "run_mode": (
                metadata.get("run_mode", "immediate") if metadata else "immediate"
            ),
            **(metadata or {}),
        },
    }

    audit_logs.append(audit_entry)
    return audit_id


# Module execution functions
async def execute_module_async(
    module_name: str,
    run_id: str,
    parameters: Dict[str, Any],
    request: Request,
    actor: User,
):
    """Execute module in background with audit logging"""

    # Log async schedule
    log_audit_event(
        request=request,
        module_name=module_name,
        action="schedule_async",
        run_id=run_id,
        actor=actor,
        severity="info",
        status="pending",
        metadata={"parameters": parameters, "run_mode": "async"},
    )

    # Update task status
    async_tasks[run_id] = {
        "status": "running",
        "progress": 0,
        "started_at": datetime.utcnow(),
        "module_name": module_name,
    }

    try:
        # Simulate module execution (replace with actual module calls)
        await asyncio.sleep(2)  # Simulate work

        # Update progress
        async_tasks[run_id]["progress"] = 50

        # Call actual module based on module_name
        result = await simulate_module_execution(module_name, parameters)

        # Update task status
        async_tasks[run_id].update(
            {
                "status": "completed",
                "progress": 100,
                "completed_at": datetime.utcnow(),
                "result": result,
            }
        )

        # Log async execution completion
        log_audit_event(
            request=request,
            module_name=module_name,
            action="execute_async",
            run_id=run_id,
            actor=actor,
            severity=result.get("severity", "info"),
            status="success",
            metadata={"parameters": parameters, "run_mode": "async", "result": result},
        )

    except Exception as e:
        # Update task status on error
        async_tasks[run_id].update(
            {
                "status": "failed",
                "progress": 100,
                "completed_at": datetime.utcnow(),
                "error": str(e),
            }
        )

        # Log error
        log_audit_event(
            request=request,
            module_name=module_name,
            action="execute_async",
            run_id=run_id,
            actor=actor,
            severity="critical",
            status="failed",
            metadata={"parameters": parameters, "run_mode": "async", "error": str(e)},
        )


async def simulate_module_execution(
    module_name: str, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Simulate module execution with realistic responses"""

    # Module-specific simulation logic
    if module_name == "DiskSpaceOrchestrator":
        return {
            "severity": "medium",
            "volumes": [
                {
                    "mount": "C:",
                    "free_bytes": 15000000000,
                    "free_percent": 15.5,
                    "threshold_breached": True,
                },
                {
                    "mount": "D:",
                    "free_bytes": 50000000000,
                    "free_percent": 45.2,
                    "threshold_breached": False,
                },
            ],
            "total_free_gb": 65.0,
            "lowest_free_percent": 15.5,
            "recommendations": ["Clean temporary files", "Archive old documents"],
        }

    elif module_name == "NetworkMonitor":
        return {
            "severity": "high",
            "anomalies": [
                {
                    "type": "suspicious_connection",
                    "dest_ip": "185.220.101.34",
                    "process": "unknown.exe",
                    "risk_score": 85,
                },
                {
                    "type": "privacy_leak",
                    "dest_host": "tracker.doubleclick.net",
                    "process": "browser.exe",
                    "risk_score": 65,
                },
            ],
            "total_connections": 142,
            "suspicious_count": 2,
            "derived_severity": "high",
        }

    elif module_name == "PerformanceOptimizer":
        return {
            "severity": "low",
            "cpu_usage": 78.5,
            "memory_usage": 65.2,
            "optimized_processes": 3,
            "performance_gain": 12.3,
            "recommendations": ["Reduce startup programs", "Clear memory cache"],
        }

    elif module_name == "SecurityHardener":
        return {
            "severity": "medium",
            "findings": [
                {
                    "rule": "CIS-2.3.10.1",
                    "title": "Guest account enabled",
                    "status": "non_compliant",
                    "severity": "high",
                },
                {
                    "rule": "CIS-9.1.1",
                    "title": "Firewall disabled",
                    "status": "non_compliant",
                    "severity": "critical",
                },
            ],
            "compliance_score": 65.5,
            "fixed_issues": 0,
            "pending_issues": 2,
        }

    elif module_name == "UpdateGuardian":
        return {
            "severity": "low",
            "pending_updates": [
                {
                    "kb": "KB5005565",
                    "title": "Security Update",
                    "risk": "low",
                    "size_mb": 125.5,
                },
                {
                    "kb": "KB5006670",
                    "title": "Cumulative Update",
                    "risk": "medium",
                    "size_mb": 450.2,
                },
            ],
            "deferred_updates": 1,
            "blocked_updates": 0,
            "recommendations": ["Install security updates", "Review deferred updates"],
        }

    elif module_name == "DriverHealthManager":
        return {
            "severity": "medium",
            "drivers": [
                {
                    "name": "nvidia.sys",
                    "status": "warning",
                    "crashes": 2,
                    "version": "456.71",
                },
                {
                    "name": "intelppm.sys",
                    "status": "healthy",
                    "crashes": 0,
                    "version": "10.0.19041.1",
                },
            ],
            "healthy_count": 8,
            "warning_count": 2,
            "critical_count": 0,
        }

    elif module_name == "ForensicAnalyzer":
        return {
            "severity": "high",
            "findings": [
                {
                    "type": "bsod",
                    "bugcheck": "0x0000000A",
                    "root_cause": "Driver memory corruption",
                    "confidence": 0.8,
                },
                {
                    "type": "memory_leak",
                    "process": "chrome.exe",
                    "leak_rate": "15MB/hour",
                    "confidence": 0.6,
                },
            ],
            "stability_score": 45.5,
            "critical_findings": 1,
            "recommendations": ["Update graphics driver", "Run memory diagnostic"],
        }

    elif module_name == "ThermalController":
        return {
            "severity": "critical",
            "temperatures": [
                {
                    "component": "CPU",
                    "temp_celsius": 92.5,
                    "status": "critical",
                    "max_safe": 90,
                },
                {
                    "component": "GPU",
                    "temp_celsius": 85.2,
                    "status": "hot",
                    "max_safe": 95,
                },
            ],
            "hottest_component": "CPU",
            "overall_status": "critical",
            "actions_taken": ["CPU throttling", "Fan boost"],
        }

    elif module_name == "PowerManager":
        return {
            "severity": "low",
            "power_source": "battery",
            "battery_percent": 35.5,
            "estimated_runtime_minutes": 45,
            "efficiency_score": 72.3,
            "recommendations": ["Switch to power saver", "Reduce brightness"],
        }

    elif module_name == "ApplicationCurator":
        return {
            "severity": "medium",
            "applications": [
                {
                    "name": "OldToolbar",
                    "status": "abandoned",
                    "size_mb": 125.5,
                    "last_used_days": 120,
                },
                {
                    "name": "UnusedApp",
                    "status": "idle",
                    "size_mb": 85.2,
                    "last_used_days": 45,
                },
            ],
            "total_apps": 42,
            "abandoned_apps": 3,
            "disk_savings_mb": 325.7,
        }

    elif module_name == "RegistryGuardian":
        return {
            "severity": "high",
            "issues": [
                {
                    "type": "malware",
                    "path": "HKLM\\Run\\suspicious.exe",
                    "severity": "critical",
                    "action": "delete",
                },
                {
                    "type": "bloatware",
                    "path": "HKLM\\Uninstall\\Toolbar",
                    "severity": "medium",
                    "action": "quarantine",
                },
            ],
            "total_issues": 5,
            "critical_issues": 1,
            "fixed_issues": 0,
        }

    elif module_name == "BackupOrchestrator":
        return {
            "severity": "info",
            "backup_type": "incremental",
            "items_backed_up": 1250,
            "total_size_gb": 12.5,
            "destination": "C:\\Backups",
            "status": "completed",
            "next_scheduled": (datetime.utcnow() + timedelta(days=1)).isoformat(),
        }

    # Default response for unknown modules
    return {
        "severity": "info",
        "message": f"Module {module_name} executed successfully",
        "execution_time_ms": 1250,
        "parameters_received": parameters,
    }


# API Endpoints
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        response: Response = await call_next(request)
        response.headers["x-correlation-id"] = correlation_id
        return response


app.add_middleware(CorrelationIdMiddleware)


@app.post("/api/v1/auth/login", response_model=Token)
async def login_for_access_token(request: Request, login: LoginRequest):
    """Authenticate user and return JWT token"""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    username = login.username
    password = login.password

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "roles": user.roles},
        expires_delta=access_token_expires,
    )

    # Log authentication
    log_audit_event(
        request=request,
        module_name="auth",
        action="login",
        actor=user,
        severity="info",
        status="success",
        metadata={"username": username},
    )

    return {
        "correlation_id": correlation_id,
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_access_token(request: Request, refresh: RefreshTokenRequest):
    """Refresh token flow placeholder.

    This API currently uses access tokens only. This endpoint validates the provided
    refresh_token format and issues a new access token for the same subject.
    """
    try:
        payload = jwt.decode(refresh.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])

        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        if username not in users_db:
            raise HTTPException(status_code=401, detail="Unknown user")

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": username, "roles": roles},
            expires_delta=access_token_expires,
        )

        correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
        log_audit_event(
            request=request,
            module_name="auth",
            action="refresh",
            actor=User(username=username, roles=roles, disabled=False),
            severity="info",
            status="success",
            metadata={"username": username},
        )

        return {
            "correlation_id": correlation_id,
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@app.post("/api/v1/auth/logout", response_model=LogoutResponse)
async def logout(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout by blacklisting the presented access token."""
    token = credentials.credentials
    blacklisted_tokens.add(token)

    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    # Best-effort decode for audit.
    actor_username = "unknown"
    actor_roles: List[str] = []
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False}
        )
        actor_username = payload.get("sub") or "unknown"
        actor_roles = payload.get("roles", []) or []
    except Exception:
        pass

    log_audit_event(
        request=request,
        module_name="auth",
        action="logout",
        actor=User(username=actor_username, roles=actor_roles, disabled=False),
        severity="info",
        status="success",
        metadata={"username": actor_username},
    )

    return {
        "correlation_id": correlation_id,
        "status": "success",
        "message": "Logged out",
    }


@app.get("/api/v1/modules", response_model=List[ModuleStatus])
async def list_modules(
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    """List all available modules with their status"""
    correlation_id = getattr(request.state, "correlation_id", None)
    modules = [
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="DiskSpaceOrchestrator",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(hours=2),
            status="healthy",
            health_score=85.5,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="NetworkMonitor",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(minutes=30),
            status="active",
            health_score=92.3,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="PerformanceOptimizer",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(hours=1),
            status="optimizing",
            health_score=78.9,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="SecurityHardener",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(days=1),
            status="scanning",
            health_score=65.5,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="UpdateGuardian",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(hours=6),
            status="monitoring",
            health_score=88.2,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="DriverHealthManager",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(minutes=45),
            status="healthy",
            health_score=91.7,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="ForensicAnalyzer",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(hours=3),
            status="analyzing",
            health_score=76.4,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="ThermalController",
            enabled=True,
            last_run=datetime.utcnow(),
            status="critical",
            health_score=45.2,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="PowerManager",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(minutes=15),
            status="optimizing",
            health_score=82.1,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="ApplicationCurator",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(days=2),
            status="idle",
            health_score=71.8,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="RegistryGuardian",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(days=7),
            status="scanning",
            health_score=68.9,
        ),
        ModuleStatus(
            correlation_id=correlation_id,
            module_name="BackupOrchestrator",
            enabled=True,
            last_run=datetime.utcnow() - timedelta(hours=12),
            status="backing_up",
            health_score=94.5,
        ),
    ]
    return modules


@app.get("/api/v1/modules/{module_name}/status", response_model=ModuleStatus)
async def get_module_status(
    module_name: str,
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    """Get detailed status for a specific module"""
    # In a real implementation, this would query the actual module
    return ModuleStatus(
        correlation_id=getattr(request.state, "correlation_id", None),
        module_name=module_name,
        enabled=True,
        last_run=datetime.utcnow() - timedelta(hours=1),
        status="healthy",
        health_score=85.5,
    )


@app.post("/api/v1/modules/{module_name}/execute", response_model=ExecutionResponse)
async def execute_module(
    module_name: str,
    execution_request: ExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Execute a module either immediately or asynchronously"""
    run_id = str(uuid.uuid4())
    started_at = datetime.utcnow()

    if execution_request.run_mode == "immediate":
        # Immediate execution
        result = await simulate_module_execution(
            module_name, execution_request.parameters
        )

        # Log execution
        log_audit_event(
            request=request,
            module_name=module_name,
            action="execute",
            run_id=run_id,
            actor=current_user,
            severity=result.get("severity", "info"),
            status="success",
            metadata={
                "parameters": execution_request.parameters,
                "run_mode": "immediate",
                "result": result,
            },
        )

        return ExecutionResponse(
            correlation_id=getattr(request.state, "correlation_id", None),
            run_id=run_id,
            module_name=module_name,
            status="completed",
            run_mode="immediate",
            started_at=started_at,
            completed_at=datetime.utcnow(),
            severity=result.get("severity", "info"),
            details=result,
            message=f"Module {module_name} executed successfully",
        )

    elif execution_request.run_mode == "async":
        # Async execution
        background_tasks.add_task(
            execute_module_async,
            module_name,
            run_id,
            execution_request.parameters,
            request,
            current_user,
        )

        return ExecutionResponse(
            correlation_id=getattr(request.state, "correlation_id", None),
            run_id=run_id,
            module_name=module_name,
            status="running",
            run_mode="async",
            started_at=started_at,
            completed_at=None,
            severity="info",
            details={"message": "Async execution scheduled"},
            message=f"Module {module_name} scheduled for async execution",
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid run_mode. Use 'immediate' or 'async'",
        )


@app.get(
    "/api/v1/modules/{module_name}/runs/{run_id}", response_model=ExecutionResponse
)
async def get_execution_result(
    module_name: str,
    run_id: str,
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    """Get execution result for a specific run"""
    # Check if this is an async task
    if run_id in async_tasks:
        task = async_tasks[run_id]
        if task["status"] == "completed":
            return ExecutionResponse(
                correlation_id=getattr(request.state, "correlation_id", None),
                run_id=run_id,
                module_name=module_name,
                status="completed",
                run_mode="async",
                started_at=task["started_at"],
                completed_at=task.get("completed_at"),
                severity=task["result"].get("severity", "info"),
                details=task["result"],
                message=f"Async execution completed for {module_name}",
            )
        else:
            return ExecutionResponse(
                correlation_id=getattr(request.state, "correlation_id", None),
                run_id=run_id,
                module_name=module_name,
                status=task["status"],
                run_mode="async",
                started_at=task["started_at"],
                completed_at=None,
                severity="info",
                details={"progress": task["progress"]},
                message=f"Async execution {task['status']} for {module_name}",
            )

    # For immediate executions, return simulated result
    result = await simulate_module_execution(module_name, {})
    return ExecutionResponse(
        correlation_id=getattr(request.state, "correlation_id", None),
        run_id=run_id,
        module_name=module_name,
        status="completed",
        run_mode="immediate",
        started_at=datetime.utcnow() - timedelta(minutes=5),
        completed_at=datetime.utcnow() - timedelta(minutes=4, seconds=30),
        severity=result.get("severity", "info"),
        details=result,
        message=f"Execution result for {module_name}",
    )


@app.get("/api/v1/audit/logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    request: Request,
    module_name: Optional[str] = None,
    action: Optional[str] = None,
    severity: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Get audit logs with filtering and pagination"""
    # Filter logs
    filtered_logs = audit_logs.copy()

    if module_name:
        filtered_logs = [
            log for log in filtered_logs if log["module_name"] == module_name
        ]

    if action:
        filtered_logs = [log for log in filtered_logs if log["action"] == action]

    if severity:
        filtered_logs = [log for log in filtered_logs if log["severity"] == severity]

    # Sort by timestamp descending
    filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)

    # Paginate
    total = len(filtered_logs)
    total_pages = (total + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    paginated_items = filtered_logs[start_idx:end_idx]

    correlation_id = (
        getattr(request.state, "correlation_id", None)
        if request is not None
        else str(uuid.uuid4())
    )
    pagination = PaginationInfo(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )
    return AuditLogsResponse(
        correlation_id=correlation_id,
        logs=paginated_items,
        pagination=pagination,
    )


@app.get("/api/v1/audit/logs/{audit_id}", response_model=AuditLog)
async def get_audit_log_detail(
    audit_id: str, current_user: User = Depends(require_roles("admin", "analyst"))
):
    """Get detailed audit log entry"""
    for log in audit_logs:
        if log["audit_id"] == audit_id:
            return log

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found"
    )


        timestamp=datetime.utcnow().isoformat(),
        system=system,
        network=network,
        modules=modules,
    )


@app.get("/api/v1/monitoring/metrics", response_model=MonitoringMetricsResponse)
async def get_monitoring_metrics(
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    return _build_monitoring_metrics_payload(correlation_id)


@app.get("/api/v1/metrics", response_model=MonitoringMetricsResponse)
async def get_metrics_alias(
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    return await get_monitoring_metrics(request, current_user)


@app.get("/health", response_model=MonitoringMetricsResponse)
async def health_as_metrics(
    request: Request,
):
    """Alias for monitoring metrics as requested."""
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    return _build_monitoring_metrics_payload(correlation_id)


@app.get("/api/v1/async/tasks/{run_id}", response_model=AsyncTaskStatus)
    run_id: str,
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Get status of an async task"""
    if run_id not in async_tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Async task not found"
        )

    task = async_tasks[run_id]
    return AsyncTaskStatus(
        correlation_id=getattr(request.state, "correlation_id", None),
        run_id=run_id,
        module_name=task["module_name"],
        status=task["status"],
        progress=task["progress"],
        started_at=task["started_at"],
        estimated_completion=task.get("completed_at"),
        result=task.get("result"),
    )


@app.get("/api/v1/tasks/{task_id}/status", response_model=AsyncTaskStatus)
async def get_task_status_alias(
    task_id: str,
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Alias to match required task polling path."""
    return await get_async_task_status(task_id, request, current_user)


@app.get("/api/v1/monitoring/alerts", response_model=MonitoringAlertsResponse)
async def get_monitoring_alerts(
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    alerts = [
        Alert(
            id=str(uuid.uuid4()),
            severity="high",
            title="Security Threat Detected",
            message="Mock suspicious network activity detected",
            source="NetworkMonitor",
            module="NetworkMonitor",
            created_at=datetime.utcnow().isoformat(),
            acknowledged=False,
        ),
        Alert(
            id=str(uuid.uuid4()),
            severity="medium",
            title="Disk Space Warning",
            message="Mock disk usage threshold breached",
            source="DiskSpaceOrchestrator",
            module="DiskSpaceOrchestrator",
            created_at=(datetime.utcnow() - timedelta(hours=2)).isoformat(),
            acknowledged=True,
        ),
    ]

    def _count(sev: str) -> int:
        return sum(1 for a in alerts if a.severity == sev)

    summary = AlertsSummary(
        total=len(alerts),
        critical=_count("critical"),
        high=_count("high"),
        medium=_count("medium"),
        low=_count("low"),
        info=_count("info"),
        unacknowledged=sum(1 for a in alerts if not a.acknowledged),
    )

    return MonitoringAlertsResponse(
        correlation_id=correlation_id,
        alerts=alerts,
        summary=summary,
    )


@app.get("/api/v1/alerts", response_model=MonitoringAlertsResponse)
async def get_alerts_alias(
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    return await get_monitoring_alerts(request, current_user)


@app.get("/api/v1/settings")
async def get_settings(
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst", "viewer")),
):
    cfg = get_config()
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    log_audit_event(
        request=request,
        module_name="settings",
        action="read",
        actor=current_user,
        severity="info",
        status="success",
        metadata={},
    )
    return {"correlation_id": correlation_id, "settings": cfg.config}


@app.put("/api/v1/settings")
async def update_settings(
    payload: SettingsPayload,
    request: Request,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    cfg = get_config()
    for key, value in payload.changes.items():
        cfg.set(key, value)
    cfg.save()
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    log_audit_event(
        request=request,
        module_name="settings",
        action="update",
        actor=current_user,
        severity="info",
        status="success",
        metadata={"changes": payload.changes},
    )
    return {"correlation_id": correlation_id, "status": "success"}


# Module-specific endpoints
@app.post(
    "/api/v1/modules/DiskSpaceOrchestrator/scan", response_model=ExecutionResponse
)
async def scan_disk_space(
    execution_request: ExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Specialized endpoint for disk space scanning"""
    return await execute_module(
        "DiskSpaceOrchestrator",
        execution_request,
        request,
        background_tasks,
        current_user,
    )


@app.post("/api/v1/modules/NetworkMonitor/analyze", response_model=ExecutionResponse)
async def analyze_network(
    execution_request: ExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("admin", "analyst")),
):
    """Specialized endpoint for network analysis"""
    return await execute_module(
        "NetworkMonitor", execution_request, request, background_tasks, current_user
    )


@app.post("/api/v1/modules/SecurityHardener/harden", response_model=ExecutionResponse)
async def harden_security(
    execution_request: ExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_roles("admin")),
):
    """Specialized endpoint for security hardening (admin only)"""
    return await execute_module(
        "SecurityHardener", execution_request, request, background_tasks, current_user
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
