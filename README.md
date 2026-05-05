# Abbott-AFNION-2-HL7-Receiving-Application
This is a project originally designed to help a diabetes clinic called Clinicas Del Azucar create an automated process to gain A1C information from their A1C machine (the Abbott AFINION 2 machine) by physically connecting it to a laptop using ethernet and triggering the machine to make TCP/IP socket connections with the laptop and send data.

# How to Run the Application
To use the application, one could either run the Python script ".py" files directly, or one can use the Windows ".exe" applications.

## To use the Python script files, please follow this procedure (running each python script ".py" file in a seperate terminal):
1. Run the **"fake_endpoint.py"** file.
2. Run the **"hl7_server_Production_DB.py"** file.
3. Run the **"hl7_client_2_one_test.py"** file or the **"hl7_client_test_runner.py"** file.
4. Accept the confirmation message (in the application window for the **"hl7_server_Production_DB.py"** file) showing that the data was successfully retrieved from    the database.
5. View the results appear (in the application window for the **"hl7_server_Production_DB.py"** file).
6. If you ran the **"hl7_client_test_runner.py"** file, you can see the results of several tests (including edge case tests) in the **"hl7_test_message_results.txt"** file.
7. View the nested outline of the Abbott AFINION 2 machine's HL7 message structure in the **"Nested_Outline.txt"** file.

## To use the Windows executable files (.exe), please follow this procedure (double-clicking every ".exe" to run the app):
1. Go to the **"HL7_Retriever_Application_Files** folder.
2. Run the **"fake_endpoint.exe"** application file.
3. Run the **"hl7_server_Production_DB.exe"** application file.
4. Run the **"hl7_client_2_one_test.exe"** application file or the **"hl7_client_test_runner.exe"** application file.
5. Accept the confirmation message (in the application window for the **"hl7_server_Production_DB.exe"** file) showing that the data was successfully retrieved from the database.
6. View the results appear (in the application window for the **"hl7_server_Production_DB.exe"** file).
7. If you ran the **"hl7_client_test_runner.exe"** file, you can see the results of several tests (including edge case tests) in the **"hl7_test_message_results.txt"** file.
8. View the nested outline of the Abbott AFINION 2 machine's HL7 message structure in the **"Nested_Outline.txt"** file.
