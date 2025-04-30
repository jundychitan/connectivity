from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from database import (
    create_table, add_gateway, get_all_gateways, approve_gateway,
    get_gateway_ssh_key, disapprove_gateway,
    add_port_forwarding, get_all_port_forwardings, delete_port_forwarding
)
import os
import subprocess
from starlette.middleware.cors import CORSMiddleware
import socket
from starlette.middleware.sessions import SessionMiddleware


port_forwarding_processes = {}  # entry_id -> process

# ================== MODELS ==================

class GatewayConnectionRequest(BaseModel):
    hostname: str
    ssh_key: str
    mac_address: str  # <-- Added mac_address field

class PortForwardingRequest(BaseModel):
    origin_port: int
    destination_port: int

class LoginRequest(BaseModel):
    username: str
    password: str

# ================== APP SETUP ==================

app = FastAPI()
create_table()

app.add_middleware(SessionMiddleware, secret_key="ORaS88rUqip0FxnllMUdBZVAnZnMW1HV")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://139.162.31.224:3000"],  # Allows all origins; you can restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# ================== GATEWAY ROUTES ==================

@app.get("/")
async def root():
    return {"message": "Gateway Auth V1"}


@app.post("/login")
async def login(payload: LoginRequest, request: Request):
    STATIC_USERNAME = "admin"
    STATIC_PASSWORD = "admin1234"

    if payload.username == STATIC_USERNAME and payload.password == STATIC_PASSWORD:
        # Store user session
        request.session["user"] = payload.username
        
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Login successful"}
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid credentials"}
        )

@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}

@app.get("/check-auth")
async def check_auth(request: Request):
    user = request.session.get("user")
    if user:
        return {"authenticated": True, "user": user}
    return JSONResponse(status_code=401, content={"authenticated": False})

@app.get("/list")
async def list_gateways():
    gateways = get_all_gateways()
    return gateways

@app.get("/approve/{gateway_id}")
async def approve(gateway_id: int):
    try:
        ssh_key = get_gateway_ssh_key(gateway_id)

        ssh_dir = os.path.expanduser("~/.ssh")
        authorized_keys_path = os.path.join(ssh_dir, "authorized_keys")

        os.makedirs(ssh_dir, exist_ok=True)
        with open(authorized_keys_path, "a") as f:
            f.write(f"\n{ssh_key.strip()}\n")

        approve_gateway(gateway_id)
    except Exception as error:
        return {"message": f"Error: {error}"}
    return {"message": f"Gateway {gateway_id} approved"}

@app.get("/revoke/{gateway_id}")
async def revoke(gateway_id: int):
    try:
        ssh_key = get_gateway_ssh_key(gateway_id)
        if not ssh_key:
            return {"message": "Gateway not found."}

        ssh_dir = os.path.expanduser("~/.ssh")
        authorized_keys_path = os.path.join(ssh_dir, "authorized_keys")

        if os.path.exists(authorized_keys_path):
            with open(authorized_keys_path, "r") as f:
                keys = f.read().splitlines()

            keys = [k for k in keys if k.strip() != ssh_key.strip()]

            with open(authorized_keys_path, "w") as f:
                f.write("\n".join(keys) + "\n")

        disapprove_gateway(gateway_id)

    except Exception as error:
        return {"message": f"Error: {error}"}

    return {"message": f"Gateway {gateway_id} revoked and SSH key removed"}

@app.post("/register")
async def register(payload: GatewayConnectionRequest):
    try:
        add_gateway(payload.hostname, payload.ssh_key, payload.mac_address)
    except Exception as error:
        return {"message": f"Error: {error}"}

    return {"message": f"Request sent for {payload.hostname}"}

# ================== PORT FORWARDING ROUTES ==================

def is_port_in_use(port: int, host: str = "0.0.0.0") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        try:
            s.bind((host, port))
            return False
        except socket.error:
            return True

@app.post("/port-forwarding")
async def create_port_forwarding(payload: PortForwardingRequest):
    try:

        if is_port_in_use(payload.origin_port):
            return {"message": f"Origin port {payload.origin_port} is already in use."}
        if is_port_in_use(payload.destination_port):
            return {"message": f"Destination port {payload.destination_port} is already in use."}

        # Spawn service
        process = subprocess.Popen([
            "/projects/tcp-bridge/tcp-bridge",
            "0.0.0.0",
            str(payload.origin_port),
            "0.0.0.0",
            str(payload.destination_port)
        ])

        entry_id = add_port_forwarding(payload.origin_port, payload.destination_port)
        port_forwarding_processes[entry_id] = process

    except Exception as error:
        return {"message": f"Error: {error}"}
    return {"message": "Port forwarding rule created successfully"}

@app.get("/port-forwarding")
async def list_port_forwardings():
    rules = get_all_port_forwardings()
    return rules

@app.delete("/port-forwarding/{entry_id}")
async def remove_port_forwarding(entry_id: int):
    try:
        # Kill the process if exists
        process = port_forwarding_processes.pop(entry_id, None)
        if process:
            process.kill()
            print(f"Process {entry_id} has been terminated.")

        delete_port_forwarding(entry_id)
    except Exception as error:
        return {"message": f"Error: {error}"}
    return {"message": f"Port forwarding rule {entry_id} deleted successfully"}
