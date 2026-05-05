import socket

HOST = "localhost"   # or your server IP
PORT = 2575

SB = b"\x0b"
EB = b"\x1c"
CR = b"\x0d"

# ---------------------------------------------------------
# HL7 TEST MESSAGES
# ---------------------------------------------------------

real_test = (
    "MSH|^~\\&|Afinion 2 Analyzer||HBA1C-SERVER|LAB-COMPUTER|20260213153723||ORU^R01|1000|P|2.4|||AL|NE||8859/1\r"
    "PID|1||Patient_ID|\r"
    "PV1|1|||||||||||||||||||\r"
    "OBR|1||5|HbA1c|||||||N||||ORH||||||||^10234297||F|\r"
    "OBX|1|ST|HbA1c||n.n|%|||||F|||||||AF20000697|20260130131451|\r"
)

test1 = (
    "MSH|^~\\&|Afinion 2 Analyzer||HBA1C-SERVER|LAB-COMPUTER|20260216160000||ORU^R01|3001|P|2.4|||AL|NE||8859/1\r"
    "PID|1||12345|\r"
    "PV1|1|||||||||||||||||||\r"
    "OBR|1||10|HbA1c|||||||N||||ORH||||||||^10230001||F|\r"
    "OBX|1|ST|HbA1c||6.2|%|||||F|||||||AF20000697|20260216155900|\r"
)

test2 = (
    "MSH|^~\\&|Afinion 2 Analyzer||HBA1C-SERVER|LAB-COMPUTER|20260216161100||ORU^R01|4002|P|2.4|||AL|NE||8859/1\r"
    "PID|1||88888|\r"
    "PV1|1|||||||||||||||||||\r"
    "OBR|1||21|HbA1c|||||||N||||ORH||||||||^10230011||F|\r"
    "OBX|1|ST|HbA1c||4.0|%|||||F|||||||AF20000697|20260216161045|\r"
)

test3 = (
    "MSH|^~\\&|Afinion 2 Analyzer||HBA1C-SERVER|LAB-COMPUTER|20260216160100||ORU^R01|2002|P|2.4|||AL|NE||8859/1\r"
    "PID|1||67890|\r"
    "PV1|1|||||||||||||||||||\r"
    "OBR|1||11|HbA1c|||||||N||||ORH||||||||^10230002||F|\r"
    "OBX|1|ST|HbA1c||<4.0|%|||<||F|||||||AF20000697|20260216160030|\r"
)

test4 = (
    "MSH|^~\\&|Afinion 2 Analyzer||HBA1C-SERVER|LAB-COMPUTER|20260216160200||ORU^R01|2003|P|2.4|||AL|NE||8859/1\r"
    "PID|1||24680|\r"
    "PV1|1|||||||||||||||||||\r"
    "OBR|1||12|HbA1c|||||||N||||ORH||||||||^10230003||F|\r"
    "OBX|1|ST|HbA1c||>15.0|%|||>||F|||||||AF20000697|20260216160140|\r"
)

test5 = (
    "MSH|^~\\&|Afinion 2 Analyzer||HBA1C-SERVER|LAB-COMPUTER|20260216161000||ORU^R01|4001|P|2.4|||AL|NE||8859/1\r"
    "PID|1||77777|\r"
    "PV1|1|||||||||||||||||||\r"
    "OBR|1||20|HbA1c|||||||N||||ORH||||||||^10230010||F|\r"
    "OBX|1|ST|HbA1c||---|%|||||F|||||||AF20000697|20260216160930|\r"
)

tests = [
    ("Real A1C Message Test", real_test),
    ("Test 1 - Normal HbA1c", test1),
    ("Test 2 - HbA1c = 4.0", test2),
    ("Test 3 - HbA1c < 4.0", test3),
    ("Test 4 - HbA1c > 15.0", test4),
    ("Test 5 - HbA1c unreadable (---)", test5),
]

# ---------------------------------------------------------
# SEND TESTS AND LOG RESULTS
# ---------------------------------------------------------

output_file = "hl7_test_message_results.txt"

with open(output_file, "w") as f:
    for label, msg in tests:
        print(f"Sending: {label}")
        f.write(label + "\n")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            sock.sendall(SB + msg.encode("utf-8") + EB + CR)

            data = b""
            while not data.endswith(EB + CR):
                chunk = sock.recv(1024)
                if not chunk:
                    break
                data += chunk

        # unwrap MLLP
        if data.startswith(SB):
            data = data[len(SB):]
        if data.endswith(EB + CR):
            data = data[:-len(EB + CR)]

        ack = data.decode("utf-8")

        # Escape for safe file output
        safe_ack = (
            ack
            .replace("\\", "\\\\")   # escape ALL backslashes
            .replace("\r", "\\r")    # show segment delimiters
        )

        f.write(safe_ack + "\n")
        f.write("-" * 50 + "\n\n")

print(f"Done. Results written to {output_file}")