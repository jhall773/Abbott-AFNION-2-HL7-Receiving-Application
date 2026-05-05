# client.py
import socket

HOST = socket.gethostname() # Current Address @ Library  # (Server address at Innovation Center).  #'10.245.160.145' (Server address at home).
PORT = 2575          # Must match server.listen() port

# MLLP framing characters
SB = b'\x0b'  # Start Block
EB = b'\x1c'  # End Block
CR = b'\x0d'  # Carriage Return

# Sample HL7 v2.4 message from the Afinion 2 _ HL7 Connectivity Protocol Mannual from Abbott
hl7_payload = ("MSH|^~\\&|Afinion 2 Analyzer||||20191030102640||ORU^R01|1000|Q|2.4|||AL|NE||8859/1\rPID|1||1019962101125029|\rPV1|1|||||||||||||||||||\rOBR|1||1|HbA1c|||||||N||||ORH||||||||^10197873||F|\rOBX|1|ST|HbA1c||6.2|%|||||F|||||OPR001||AF20000697|20191007143510|"
)

# Wrap in MLLP and send
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((HOST, PORT))
    sock.sendall(SB + hl7_payload.encode('utf-8') + EB + CR)

    # Read the ACK (until EB+CR)
    data = b''
    while not data.endswith(EB + CR):
        chunk = sock.recv(1024)
        if not chunk:
            break
        data += chunk

# Unwrap MLLP and print
# Remove only the first SB and the last EB+CR
if data.startswith(SB):
    data = data[len(SB):]

if data.endswith(EB + CR):
    data = data[:-len(EB + CR)]

ack = data.decode('utf-8')
print("Received ACK:")
print(ack.replace("\r", "\\r"))