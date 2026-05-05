# server.py
import socket
import sys
from datetime import datetime
from hl7apy.parser import parse_message
import tkinter
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
import threading
from datetime import datetime
import requests

HOST = '0.0.0.0' # '0.0.0.0' is listening for any host IP Address (arbitrarily unless IP address of the A1C Machine device in the "analyzer network settings" is placed here instead)
PORT = 2575      # This is the number that must match the A1C Machine HL7 device you are listening for.

SB = b'\x0b'
EB = b'\x1c'
CR = b'\x0d'


def build_ack(raw_hl7: str) -> bytes:
    """
    Build a proper HL7 ACK (ER7) wrapped in MLLP.
    """
    msg = parse_message(raw_hl7, validation_level=2)
    msh = msg.children[0]

    sending_app = msh.msh_3[0].hd_1.value if msh.msh_3 else ""

    sending_fac = msh.msh_4[0].hd_1.value if msh.msh_4 else ""

    receiving_app = msh.msh_5[0].hd_1.value if msh.msh_5 else ""

    receiving_fac = msh.msh_6[0].hd_1.value if msh.msh_6 else ""

    orig_msg_ctrl = msh.msh_10.value if msh.msh_10 else ""

    version = msh.msh_12.value if msh.msh_12 else ""


    ts = datetime.now().strftime('%Y%m%d%H%M%S')

    # NEW: unique ACK control ID
    ack_ctrl = f"ACK{ts}"

    # NEW: ACK^R01 instead of ACK
    msh_ack = (
        f"MSH|^~\\&|{receiving_app}|{receiving_fac}|"
        f"{sending_app}|{sending_fac}|{ts}|ACK^R01|"
        f"{ack_ctrl}|P|{version}\r"
    )

    # MSA-2 echoes original control ID
    msa = f"MSA|AA|{orig_msg_ctrl}\r"

    er7 = msh_ack + msa
    return SB + er7.encode("utf-8") + EB + CR       
# End of Acknowledgement Building Function


def handle_connection(conn):
    buffer = b''
    try:
        while True:
            chunk = conn.recv(4096)
            # If no data, the analyzer has closed the connection
            if not chunk:
                break
            buffer += chunk
            # process all complete MLLP frames in buffer
            while True:
                start = buffer.find(SB)
                end = buffer.find(EB)
                if start != -1 and end != -1 and end > start:
                    raw_bytes = buffer[start+1:end]
                    # remove processed frame (also drop following CR if present)
                    buffer = buffer[end+1:]
                    if buffer.startswith(CR):
                        buffer = buffer[1:]
                    raw_hl7 = raw_bytes.decode('utf-8', errors='replace')
                    raw_hl7Print = raw_hl7
                    print((raw_hl7Print).replace("\r", "\\r"))

                    # ACK/NACK right after full frame is extracted
                    process_hl7_and_ack(conn, raw_hl7)
                else:
                    break
    finally:
        conn.close()
# End of handle_connection() function


def process_hl7_and_ack(conn, raw_hl7):
    try:
        # ***The outline of Hl7 message structure also outputs to the Nested_Outline.txt file***
        with open("Nested_Outline.txt", "w") as output:
            print("Nested_Outline Structure:", file=output)
            first_msg = parse_message(raw_hl7, validation_level=2)
            print_tree(elem=first_msg, file=output)

        # ***Retrieve Patient_ID and A1C % from HL7 message using parse_oru_r01().***
        # The function also prints the Patiend_ID and A1C % to the terminal.
        patient_data = parse_oru_r01(raw_hl7)
        patient_id = patient_data[0]
        a1c_value = patient_data[1]
        if a1c_value == '>15.0':
            a1c_value = '15.0'
        
        if a1c_value == '<4.0':
            a1c_value = '4.0'
        
        units = patient_data[2]
        date = patient_data[3]
        pid_datetime = patient_data[4]

        # ***Send Aknowledgement back to machine***
        conn.sendall(build_ack(raw_hl7))
    
    except Exception as data_retrieval_Error:
        # Print full traceback of the data_retrieval_Error
        import traceback
        print(f"\nError: {data_retrieval_Error}\n\nFull Traceback:")
        traceback.print_exc()

        # ***build a NACK (MSA|AE) including error text***
        nack = build_nack(raw_hl7, str(data_retrieval_Error))
        conn.sendall(nack)


    try:
        # ***Send data to the clinic's database by sending it to an endpoint and then show user what you sent***
        test_url = "http://127.0.0.1:5000/a1c"
        payload = {
            "token": "12345678910abcdefghij",
            "patient_id": patient_id,
            "pid": pid_datetime,
            "A1c": a1c_value,
        }

        response = requests.post(test_url, json=payload)
        
        print("Status:", response.status_code)

        if response.status_code == requests.codes.ok:
            print("Response JSON:", response.json())
            messagebox.showinfo(title="Database Status", message="Data successfully transmited to database\n\nPatient ID: " + patient_id + "\nA1C: " + a1c_value + units)

    except Exception as endpointError:
         # Print full traceback of the endpointError
        import traceback
        print(f"\nError: {endpointError}\n\nFull Traceback:")
        traceback.print_exc()

    # ***Tkinter: Once you get the necessary data from the A1C Abbott Afinion 2 Machnine, print it to user window using Tkinter, 
    #          overwriting the previous message.***
    ui_message.delete(index1='1.0', index2='10.0')
    ui_message.insert(index='1.0', 
                        chars=f"Patient ID Recieved: {patient_id}\nA1C Result Recieved: {a1c_value}{units}\nDate: {date}")
    ui_message.pack()

# END process_hl7_and_ack() function


# Parser specifically to try and gain patient data

# --- Configure logging to file ---
def parse_oru_r01(raw_hl7):
    msg = parse_message(raw_hl7, validation_level=2)
    pat_res_grp = msg.children[1]
    
    # --- Patient ID ---
    patient_id = None
    try:
        oru_pat, order_obs = pat_res_grp.children
        print("First child under Patient Result Group is: ", oru_pat)
        pid_seg = next((s for s in oru_pat.children if s.name == 'PID'), None)
        if pid_seg and pid_seg.pid_3:
            # In the A1C machine message, PID-3 is just the string "ID".
            patient_id = pid_seg.pid_3[0].to_er7()
            print("Got patient_id: ", patient_id)
    except ValueError:
        order_obs = pat_res_grp.children[0]

    
    # --- HbA1c result ---
    try:
        oru_pat, order_obs = pat_res_grp.children
        print("Second child under Patient Result Group is: ", order_obs)
        print("\tThis 2nd child's children", order_obs.children)
        
        ORU_grp = next((s for s in order_obs.children if s.name == 'ORU_R01_OBSERVATION'), None)
        if ORU_grp:
            OBX_seg = next((s for s in ORU_grp.children if s.name == 'OBX'), None)
            print("Froze?")
            if OBX_seg and OBX_seg.obx_5:
                # In the A1C machine message, the element in OBX_5 is the "VARIES_1 (Component)", which is the A1C percentage value.
                a1c_value = OBX_seg.obx_5[0].to_er7() if OBX_seg.obx_5[0].to_er7() else "N/A"
                print("Got a1c_value: ", a1c_value)

            if OBX_seg and OBX_seg.obx_6:
                # In the A1C machine message, the element in OBX_6 is the "CE_1 (Component)", which is the smbol for the unit of measurement '%'.
                a1c_unit = OBX_seg.obx_6[0].to_er7() if OBX_seg.obx_6[0].to_er7() else "N/A"
                print("Got a1c_unit: ", a1c_unit)
    except ValueError:
        order_obs = pat_res_grp.children[0]

    
    # --- Date/time ---
    try:
        oru_pat, order_obs = pat_res_grp.children
        ORU_grp = next((s for s in order_obs.children if s.name == 'ORU_R01_OBSERVATION'), None)
        if ORU_grp:
            OBX_seg = next((s for s in ORU_grp.children if s.name == 'OBX'), None)
            if OBX_seg and OBX_seg.obx_19:
                print("Froze_Date's_OBX_guess?")
                # In the A1C machine message, the element in OBX_19 is the "TS_1 (component)", which is the date in yearmonthdayhrsminsec.
                raw_datetime = OBX_seg.obx_19[0].to_er7() if OBX_seg.obx_19[0].to_er7() else "N/A"
                print("Got raw_datetime: ", raw_datetime)
                if raw_datetime:
                    try:
                        parsed_datetime = datetime.strptime(raw_datetime, "%Y%m%d%H%M%S")
                        print("parsed datetime: ", parsed_datetime)
                        date_str = parsed_datetime.strftime("%m/%d/%Y %H:%M:%S")
                    except ValueError:
                        date_str = "Invalid format"
                else:
                    date_str = "N/A"
    except ValueError:
        order_obs = pat_res_grp.children[0]

    print(f"Patient ID: {patient_id}\n")
    print(f"HbA1c: {a1c_value}{a1c_unit}\n")
    print(f"Date: {date_str}\n")
    
    return patient_id, a1c_value, a1c_unit, date_str, raw_datetime
# End Parser for Patient data


# function to print the nested message outline
def print_tree(elem, file=None, indent=0):
    spacer = "  " * indent
    print(f"{spacer}{elem.name}  ({elem.__class__.__name__})", file=file)
    if hasattr(elem, "children"):
        for child in elem.children:
            print_tree(elem=child, file=file, indent=indent + 1)
# End of printing outline()


def build_nack(raw_hl7: str, error_text: str = "", error_code: str = "AE") -> bytes:
    try:
        msg = parse_message(raw_hl7, validation_level=2)
        msh = getattr(msg, "msh", None)

        orig_ctrl = msh.msh_10.value if msh and msh.msh_10 else ""
        version = msh.msh_12.value if msh and msh.msh_12 else "2.4"

        sending_app = msh.msh_3.to_er7() if msh and msh.msh_3 else ""
        sending_fac = msh.msh_4.to_er7() if msh and msh.msh_4 else ""
        receiving_app = msh.msh_5.to_er7() if msh and msh.msh_5 else ""
        receiving_fac = msh.msh_6.to_er7() if msh and msh.msh_6 else ""
    except Exception:
        orig_ctrl = ""
        version = "2.4"
        sending_app = sending_fac = receiving_app = receiving_fac = ""

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    ack_ctrl = f"ACK{ts}"

    msh_nack = (
        f"MSH|^~\\&|{receiving_app}|{receiving_fac}|"
        f"{sending_app}|{sending_fac}|{ts}|ACK^R01|{ack_ctrl}|P|{version}\r"
    )

    # FIX: Only include MSA-3 if error_text is present
    if error_text:
        msa = f"MSA|{error_code}|{orig_ctrl}|{error_text}\r"
    else:
        msa = f"MSA|{error_code}|{orig_ctrl}\r"

    err = f"ERR|||{error_text}\r" if error_text else ""

    er7 = msh_nack + msa + err
    return SB + er7.encode("utf-8") + EB + CR
# End of Negative Acknowledgement Build Function


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        print(f"Listening for Patient Data from A1C Abbott Affinon 2 over MLLP HL7 protocol on {HOST}:{PORT}…")
        
        while True:
            conn, addr = server.accept()
            print("Connection from", addr)
            with conn:
                handle_connection(conn) 
# End of start_server()

# Event handler - User closed program via window manager or CTRL-C
def eventDeleteDisplay():
    print("UI: Closing")

    # Continuing closing window now
    global main_UI
    main_UI.destroy()
#End of eventDeleteDisplay()

def start_UI():
    global main_UI
    main_UI = tkinter.Tk()

    # main_UI's Initial Display()
    main_UI.wm_title("A1C Patient Data Retrieval System")
    main_UI.resizable('1','1')
    main_UI.protocol("WM_DELETE_WINDOW", eventDeleteDisplay)

    # These are the 4 app messages that will be displayed over the lifetime of the UI Window using "ui_message",
    # After destroying the previous message object (with ui_message.destroy())
    global ui_message, startup_msg
    ui_message = ScrolledText(
                master=main_UI,
                wrap=tkinter.WORD,
                width=50,  # In chars
                height=20)  # In chars     

    # Compute display position for all objects
    ui_message.pack(side=tkinter.TOP, fill=tkinter.BOTH)

    # Tkinter: When you start the program, put this print message in the root "main" Tkinter Window, informing the user:
    startup_msg = f"Listening for Patient Data from A1C Abbott Affinon 2 over MLLP HL7 protocol on {PORT}…"
    ui_message.insert(index='1.0',
                       chars=f"{startup_msg}")
    
    # Starts the UI
    main_UI.mainloop()
# End of start_UI()

# Main Loop of Execution:
def main():
    global thread_server
    thread_server = threading.Thread(target=start_server)
    thread_server.daemon = True
    thread_server.start()

    start_UI() # running Tkinter on main thread

if __name__ == "__main__":
    sys.exit(main())