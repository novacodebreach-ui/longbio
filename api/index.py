import os
import sys
import time
import binascii
import jwt
import urllib3
import requests
import logging
from flask import Flask, request, jsonify, make_response, render_template_string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

# Fix Vercel Import Paths
sys.path.append(os.path.dirname(__file__))

try:
    import my_pb2
    import output_pb2
except ImportError as e:
    print(f"Import Error: {e}")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- CONFIGURATION ---
FREEFIRE_UPDATE_URL = "https://clientbp.ggblueshark.com/UpdateSocialBasicInfo"
MAJOR_LOGIN_URL = "https://loginbp.ggblueshark.com/MajorLogin"
OAUTH_URL = "https://100067.connect.garena.com/oauth/guest/token/grant"
FREEFIRE_VERSION = "OB52"
KEY = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
IV = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

# --- DYNAMIC BIO PROTOBUF (data.proto) ---
_sym_db = _symbol_database.Default()
DESCRIPTOR_BIO = _descriptor_pool.Default().AddSerializedFile(
    b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3'
)
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR_BIO, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR_BIO, 'data1_pb2', globals())
BioData = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

# --- HELPER FUNCTIONS ---
def encrypt_data(data_bytes):
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return cipher.encrypt(pad(data_bytes, AES.block_size))

def decode_jwt_info(token):
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return str(decoded.get("account_id")), decoded.get("nickname"), decoded.get("lock_region")
    except: return None, None, None

def perform_major_login(access_token, open_id):
    platforms = [8, 3, 4, 6]
    for p_type in platforms:
        try:
            game_data = my_pb2.GameData()
            game_data.timestamp = "2024-12-05 18:15:32"
            game_data.game_name = "free fire"
            game_data.game_version = 1
            game_data.version_code = "1.120.2"
            game_data.os_info = "Android OS 9"
            game_data.open_id = open_id
            game_data.access_token = access_token
            game_data.platform_type = p_type
            game_data.field_99 = str(p_type)
            game_data.field_100 = str(p_type)

            encrypted = encrypt_data(game_data.SerializeToString())
            headers = {"User-Agent": "Dalvik/2.1.0", "Content-Type": "application/octet-stream", "ReleaseVersion": FREEFIRE_VERSION}
            resp = requests.post(MAJOR_LOGIN_URL, data=encrypted, headers=headers, timeout=5, verify=False)

            if resp.status_code == 200:
                out = output_pb2.Garena_420()
                out.ParseFromString(resp.content)
                if out.token: return out.token
        except: continue
    return None

def perform_guest_login(uid, password):
    payload = {'uid': uid, 'password': password, 'response_type': "token", 'client_type': "2", 'client_id': "100067"}
    try:
        r = requests.post(OAUTH_URL, data=payload, timeout=8, verify=False)
        d = r.json()
        return d.get('access_token'), d.get('open_id')
    except: return None, None

# --- UI TEMPLATE ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AETHER | Profile Command</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #050505; color: white; font-family: sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); }
        .gradient-text { background: linear-gradient(to right, #fff, #a855f7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
</head>
<body class="flex flex-col items-center justify-center min-h-screen p-6">
    <div class="glass p-8 rounded-3xl w-full max-w-md shadow-2xl">
        <h1 class="text-3xl font-black gradient-text mb-6 text-center tracking-tighter">AETHER.OS</h1>
        <form action="/bio_upload" method="GET" class="space-y-4">
            <input name="bio" placeholder="New Signature / Bio" class="w-full bg-black/50 border border-white/10 p-4 rounded-xl" required>
            <div class="grid grid-cols-2 gap-2">
                <input name="uid" placeholder="UID" class="bg-black/50 border border-white/10 p-4 rounded-xl">
                <input name="pass" type="password" placeholder="Pass" class="bg-black/50 border border-white/10 p-4 rounded-xl">
            </div>
            <p class="text-center text-xs text-gray-500">OR</p>
            <input name="jwt" placeholder="Direct JWT Token" class="w-full bg-black/50 border border-white/10 p-4 rounded-xl">
            <button class="w-full bg-white text-black font-bold py-4 rounded-xl hover:bg-purple-500 hover:text-white transition">EXECUTE OVERRIDE</button>
        </form>
    </div>
</body>
</html>
"""

# --- ROUTES ---
@app.route("/")
def index():
    return render_template_string(HTML_UI)

@app.route("/bio_upload")
def bio_upload():
    bio = request.args.get("bio")
    jwt_token = request.args.get("jwt")
    uid = request.args.get("uid")
    password = request.args.get("pass")

    final_jwt = jwt_token
    if not final_jwt and uid and password:
        acc, oid = perform_guest_login(uid, password)
        if acc and oid:
            final_jwt = perform_major_login(acc, oid)

    if not final_jwt:
        return jsonify({"status": "error", "message": "Authentication Failed"}), 401

    # Bio Injection
    try:
        data = BioData()
        data.field_2 = 17
        data.field_5.CopyFrom(EmptyMessage())
        data.field_6.CopyFrom(EmptyMessage())
        data.field_8 = bio
        data.field_9 = 1
        data.field_11.CopyFrom(EmptyMessage())
        data.field_12.CopyFrom(EmptyMessage())

        encrypted = encrypt_data(data.SerializeToString())
        headers = {"Authorization": f"Bearer {final_jwt}", "ReleaseVersion": FREEFIRE_VERSION}
        resp = requests.post(FREEFIRE_UPDATE_URL, headers=headers, data=encrypted, timeout=10, verify=False)
        
        u, n, r = decode_jwt_info(final_jwt)
        
        return jsonify({
            "status": "Success" if resp.status_code == 200 else "Failed",
            "name": n,
            "region": r,
            "uid": u,
            "response_hex": binascii.hexlify(resp.content).decode()[:50]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
