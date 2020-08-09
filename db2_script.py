# ----------------------------------------------------------------------------------------------#
#  NAME:     db2_script.py                                                                      #
#                                                                                               #
#  PURPOSE:  Script makes use of Db2 APIs to read, write and manipulate data from IBM DB        #
#                                                                                               #
#  API/SERVICES USED:                                                                           #
#    1. POST /auth/tokens                 :     AUTHENTICATION                                  #
#    2. GET /schemas/{schema_name}/tables :     LIST TABLES IN GIVEN SCHEMA_NAME                #
#    3. PUT /admin/tables                 :     CREATE A NEW TABLE                              #
#    4. POST /sql_jobs                    :     EXECUTE SQL STATEMENTS                          #
#                                                                                               #
#  CALLING RESTFUL SERVICES:                                                                    #
#  There are two types of RESTful calls that are used with Db2 on Cloud:                        #
#     * GET - get results from a SQL request                                                    #
#     * POST - Request an access token, or issue an SQL command                                 #
#                                                                                               #
#  All RESTful calls require the host IP address and the service URL:                           #
#     * host - this is the IP address of the machine that is hosting Db2 on Cloud               #
#     * api - the API library that is being used to communicate with Db2 on Cloud: "/dbapi/v4"  #
#     * service - the service (API) that is being requested                                     #
#                                                                                               #
# ----------------------------------------------------------------------------------------------#

# Load The Appropriate Python Modules
import json
import requests
from datetime import datetime


class BColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Db2Connection:

    def __init__(self, credentials):

        self.credentials = credentials
        self.api = "/dbapi/v4"
        self.host = self.credentials["https_url"] + self.api
        self.user_info = {
            "userid": self.credentials["username"],
            "password": self.credentials["password"]
        }

        self.schema_name = "NQL98658"
        self.logs_table = "LICENSE_OCR"
        self.employee_details_table = "EMPLOYEE_DETAILS"

        self.date = datetime.today().strftime('%Y-%m-%d')
        self.time = datetime.now().strftime('%H:%M:%S')

    def authenticate(self):
        """
        =========================================================================================================
        Authenticates the user credentials and returns an access token that can be used when invoking the operations.
        CALL:
            POST /auth/tokens

        If this call returns successfully, the post request will return a structure that looks like this:
            {
                "userid":   "STRING",         # User ID associated with the generated token.
                "token":    "STRING"          # Token string that can be used in subsequent requests that require authentication.
            }

        The access token is valid for about an hour which means you will have to refresh it if you've been away for a while.
        =========================================================================================================
        @return results returned by the RESTful call
        =========================================================================================================
        """
        print(BColors.HEADER + "\n\nConnecting to the \'" + self.host + "\' server ...\n", end="" + BColors.ENDC)

        service = "/auth/tokens"
        print(BColors.OKBLUE + "API CALL: ", self.host + service + BColors.ENDC)
        r = requests.post(self.host + service, json=self.user_info)

        if r.status_code == 200:
            print(BColors.OKGREEN + "Connection Successful!" + BColors.ENDC)
            return r
        else:
            print(BColors.FAIL + "Could not connect to {}",
                  "\nStatus Code: {}",
                  "\nERROR Message: {}".format(self.host, r.status_code, r.reason) + BColors.ENDC)
            exit(-1)

    def schema_info(self, auth_token):
        """
        =========================================================================================================
        Returns the list of tables in a schema.

        CALL:
            GET /schemas/{schema_name}/tables

        STRUCTURE OF REQUEST:
            {
                "schema_name": "STRING"
            }

        The parameters are as follows:
            * schema_name - schema name

        RESPONSE:
            {
                "count": "INTEGER",
                "resources": [{"name": "STRING", "schema": "STRING"},
                              {name": "STRING", "schema": "STRING"}, ...]
            }

         The parameters are as follows:
            * count - Number of elements
            * resources - List of tables
                * name - The table name
                * schema - The schema name
        =========================================================================================================
        @param auth_token:
        @return:
        =========================================================================================================
        """

        print(BColors.HEADER + "\nAttempting to Collect data from schema {} ...".format(self.schema_name)
              + BColors.ENDC)

        service = "/schemas/{}/tables".format(self.schema_name)
        headers = {
            'content-type': "application/json",
            'authorization': "Bearer " + auth_token
        }
        # GET request
        print(BColors.OKBLUE + "API CALL: ", self.host + service + BColors.ENDC)
        r = requests.get(self.host + service, headers=headers)

        log_table = emp_table = False
        if r.status_code == 200:
            print(BColors.OKGREEN + "Data Successfully Collected!" + BColors.ENDC)
            num_tables = r.json()["count"]
            resources = r.json()["resources"]

            if num_tables != 0:
                # Iterate through the resources to ensure that table LICENSE_OCR doesn't exist
                for table in resources:
                    if table["name"] == self.logs_table:
                        log_table = True
                    if table["name"] == self.employee_details_table:
                        emp_table = True
        else:
            print(BColors.FAIL + "Error Collecting Schema Data."
                                 "\nStatus Code: {}"
                                 "\nERROR Message: {}".format(r.status_code, r.reason) + BColors.ENDC)

        return {"Logs": log_table, "Emp": emp_table}

    def create_table(self, auth_token, table_name):
        """
        =========================================================================================================
        Create a new table.
        CALL:
            PUT /admin/tables
        =========================================================================================================
        @param auth_token:
        @param table_name:
        @return:
        =========================================================================================================
        """
        print(BColors.HEADER + "\nAttempting to create table: {} under schema: {} ...".format(table_name,
                                                                                              self.schema_name)
              + BColors.ENDC)

        service = "/admin/tables"

        payload = {"LICENSE_OCR": {"schema": self.schema_name, "table": self.logs_table,
                                   "column_info": [
                                       {"data_type": "CHAR", "length": 10, "scale": {}, "column_name": "License_Plate",
                                        "nullable": "true"},
                                       {"data_type": "TIME", "length": {}, "scale": {}, "column_name": "Entry_Time",
                                        "nullable": "true"},
                                       {"data_type": "TIME", "length": {}, "scale": {}, "column_name": "Exit_Time",
                                        "nullable": "true"},
                                       {"data_type": "DATE", "length": {}, "scale": {}, "column_name": "Current_Date",
                                        "nullable": "true"}]
                                   },
                   "EMPLOYEE_DETAILS": {"schema": self.schema_name, "table": self.employee_details_table,
                                        "column_info": [
                                            {"data_type": "CHAR", "length": 20, "scale": {},
                                             "column_name": "Employee_Name",
                                             "nullable": "true"},
                                            {"data_type": "CHAR", "length": 10, "scale": {},
                                             "column_name": "License_Plate",
                                             "nullable": "true"},
                                            {"data_type": "CHAR", "length": 15, "scale": {},
                                             "column_name": "Position",
                                             "nullable": "true"}]
                                        }
                   }
        headers = {
            'content-type': "application/json",
            'authorization': "Bearer " + auth_token
        }

        print("API CALL: ", self.host + service)
        r = requests.put(self.host + service, data=json.dumps(payload[table_name]), headers=headers)
        if r.status_code == 201:
            print(BColors.OKGREEN + "Successfully created table {}!".format(table_name) + BColors.ENDC)
        else:
            print(BColors.FAIL + "Error Creating Table."
                                 "\nStatus Code: {}"
                                 "\nERROR Message: {}"
                                 "\n\nExiting Application.".format(r.status_code, r.reason) + BColors.ENDC)
            exit(-1)

    def insert_sql(self, service, license_plate, headers):
        """
        =========================================================================================================
        Executes a SQL Insert Statement to create a new entry
        CALL:
            POST /sql_jobs

        STRUCTURE OF SQL REQUEST:
            {
                "commands": "sql",
                "limit", x,
                "separator": ";",
                "stop_on_error": "yes"
            }

        The parameters are as follows:
            * commands - The SQL script to be executed (could be multiple statements)
            * limit - Maximum number of rows that will be fetched for each result set
            * separator - SQL statement terminator. A character that is used to mark the end of a SQL statement when
                          the provided SQL script contains multiple statements.
            * stop_on_error - If 'yes', the job stops executing at the first statement that returns an error. If 'no',
                              the job continues executing if one or more statements returns an error.
        =========================================================================================================
        @param service:
        @param license_plate:
        @param headers:
        @return:
        =========================================================================================================
        """

        print(BColors.HEADER + "\nPerforming an Insert Query for License Plate {}".format(license_plate)
              + BColors.ENDC)

        insert_command = {
            "commands": "INSERT INTO \"NQL98658\".\"LICENSE_OCR\" "
                        "(\"LICENSE_PLATE\",\"ENTRY_TIME\",\"EXIT_TIME\",\"CURRENT_DATE\") "
                        "VALUES('{}','{}', NULL, '{}');".format(license_plate, self.time, self.date),
            "limit": {},
            "separator": ";",
            "stop_on_error": "yes"
        }
        print("SQL Insert Statement: {}".format(insert_command["commands"]))
        print(BColors.OKBLUE + "API CALL: ", self.host + service + BColors.ENDC)

        insert_req = requests.post(self.host + service, headers=headers, json=insert_command)
        if insert_req.status_code == 201:
            print(BColors.OKGREEN + "SQL Insert Successful!" + BColors.ENDC)
        else:
            print(BColors.FAIL + "Error Inserting Data"
                                 "\nSQL Statement: {}"
                                 "\nStatus Code: {}"
                                 "\nERROR Message: {}".format(insert_command["commands"],
                                                              insert_req.status_code, insert_req.reason) + BColors.ENDC)

    def retrieve_sql(self, service, job_id, headers):
        """
        =========================================================================================================
        Now that the SQL statement has been set off for execution, we must request the results.
        The RESTful API is exactly the same as requesting the SQL to be run, but you need to add the job id to the
        end of the service.

        CALL:
            GET /sql_jobs/{id}

        RESPONSE:
            {
                "id": "STRING",
                "status": "STRING",
                "results": [{
                                "command": "STRING",
                                "columns": "ARRAY",
                                "rows": "ARRAY",
                                "rows_count": "INTEGER",
                                "limit": "INTEGER",
                                "last_inserted": "INTEGER",
                                "rows_affected": "INTEGER",
                                "runtime_seconds": "DOUBLE",
                                "error": "STRING"
                            }
                }]

            The status field contains either "completed", "running" or "failed". It is possible that you only get an
            intermediate result set (perhaps because the answer set is still being gathered) so running will be returned.
            When the status is running, you may already have some data in the results field. You must retrieve this
            data before issuing another request. The data that is returned is not cumulative which means any results
            returned in the RESTful call are lost on the next call.

                r = restful.get(...)
                if (r.status == "failed") leave...
                rows = get rows from r
                while r.status == "running":
                    r = restful.get(...)
                    rows = get rows from r
        =========================================================================================================
        @param service:
        @param job_id:
        @param headers:
        @return:
        =========================================================================================================
        """

        # Retrieving the SQL Results
        print(BColors.HEADER + "\nAttempting to Retrieve SQL Data ..." + BColors.ENDC)
        print(BColors.OKBLUE + "API CALL: ", self.host + service + "/" + job_id + BColors.ENDC)

        sql_req = requests.get(self.host + service + "/" + job_id, headers=headers)
        rows = []
        if sql_req.status_code != 200:
            print(BColors.FAIL + "Error retrieving SQL data"
                                 "\nStatus Code: {}"
                                 "\nERROR Message: {}".format(sql_req.status_code, sql_req.reason) + BColors.ENDC)
        else:
            print(BColors.OKGREEN + "SQL Retrieval Successful!" + BColors.ENDC)

            # Get Results
            results = sql_req.json()["results"]
            rows = results[0]["rows"]

        return rows

    def update_item(self, service, license_plate, headers):
        """
        Executes a SQL Update Statement to update attributes of an entry

        CALL:
            POST /sql_jobs

        STRUCTURE OF SQL REQUEST:
            {
                "commands": "sql",
                "limit", x,
                "separator": ";",
                "stop_on_error": "yes"
            }

        The parameters are as follows:
            * commands - The SQL script to be executed (could be multiple statements)
            * limit - Maximum number of rows that will be fetched for each result set
            * separator - SQL statement terminator. A character that is used to mark the end of a SQL statement when
                          the provided SQL script contains multiple statements.
            * stop_on_error - If 'yes', the job stops executing at the first statement that returns an error. If 'no',
                              the job continues executing if one or more statements returns an error.
        =========================================================================================================
        @param service:
        @param license_plate:
        @param headers:
        @return:
        =========================================================================================================
        """

        print(BColors.HEADER + "\nPerforming an Update Query for License Plate {}".format(license_plate) + BColors.ENDC)

        update_command = {
            "commands": "UPDATE \"NQL98658\".\"LICENSE_OCR\" "
                        "SET \"EXIT_TIME\" = '{}' "
                        "WHERE \"NQL98658\".\"LICENSE_OCR\".\"CURRENT_DATE\" = '{}' "
                        "AND \"NQL98658\".\"LICENSE_OCR\".\"LICENSE_PLATE\" = '{}' "
                        "AND \"NQL98658\".\"LICENSE_OCR\".\"EXIT_TIME\" IS NULL;".format(self.time, self.date,
                                                                                         license_plate),
            "limit": {},
            "separator": ";",
            "stop_on_error": "yes"
        }
        print("SQL Update Statement: {}".format(update_command["commands"]))
        print(BColors.OKBLUE + "API CALL: ", self.host + service + BColors.ENDC)

        update_req = requests.post(self.host + service, headers=headers, json=update_command)
        if update_req.status_code == 201:
            print(BColors.OKGREEN + "SQL Update Successful!" + BColors.ENDC)
        else:
            print(BColors.FAIL + "Error Inserting Data"
                                 "\nSQL Statement: {}"
                                 "\nStatus Code: {}"
                                 "\nERROR Message: {}".format(update_command["commands"],
                                                              update_req.status_code, update_req.reason) + BColors.ENDC)

    def write_data(self, auth_token, license_plate):
        """
        =========================================================================================================
        Executes one or more SQL statements as a background job.
        This endpoint returns a job ID that can be used to retrieve the results.

        CALL:
            POST /sql_jobs

        STRUCTURE OF SQL REQUEST:
            {
                "commands": "sql",
                "limit", x,
                "separator": ";",
                "stop_on_error": "yes"
            }

        The parameters are as follows:
            * commands - The SQL script to be executed (could be multiple statements)
            * limit - Maximum number of rows that will be fetched for each result set
            * separator - SQL statement terminator. A character that is used to mark the end of a SQL statement when
                          the provided SQL script contains multiple statements.
            * stop_on_error - If 'yes', the job stops executing at the first statement that returns an error. If 'no',
                              the job continues executing if one or more statements returns an error.

        RESPONSE:
            {
                "id": "STRING",
                "commands_count": "INTEGER",
                "limit": "INTEGER"
            }

        Keep track of the "id" field as it is used to track the execution of SQL command(s).
        =========================================================================================================
        @param auth_token:
        @param license_plate:
        =========================================================================================================
        """

        print(BColors.HEADER + "\nAttempting to write data in table: {} ...".format(self.logs_table) + BColors.ENDC)
        print(BColors.HEADER + "Performing a SQL Query for License Plate {}".format(license_plate) + BColors.ENDC)

        service = "/sql_jobs"
        headers = {
            'authorization': "Bearer " + auth_token
        }

        sql_command = {
            "commands": "SELECT * "
                        "FROM \"NQL98658\".\"LICENSE_OCR\" "
                        "WHERE \"NQL98658\".\"LICENSE_OCR\".\"CURRENT_DATE\" = '{}' "
                        "AND \"NQL98658\".\"LICENSE_OCR\".\"LICENSE_PLATE\" = '{}'".format(self.date,
                                                                                           license_plate),
            "limit": 5,
            "separator": ";",
            "stop_on_error": "yes"
        }
        print("SQL Statement: {}".format(sql_command["commands"]))

        print(BColors.OKBLUE + "API CALL: ", self.host + service + BColors.ENDC)
        r = requests.post(self.host + service, headers=headers, json=sql_command)
        if r.status_code == 201:
            print(BColors.OKGREEN + "SQL Query Successful!" + BColors.ENDC)

            # Storing the Job_ID
            job_id = r.json()["id"]
            rows = self.retrieve_sql(service, job_id, headers)

            if not rows:
                self.insert_sql(service, license_plate, headers)
            else:
                update_flag = False
                # Parse the SQL Data to check if Exit_Time IS NULL
                for entry in rows:
                    if entry[-2] == '':
                        update_flag = True
                if update_flag:
                    self.update_item(service, license_plate, headers)
                else:
                    self.insert_sql(service, license_plate, headers)

        else:
            print(BColors.FAIL + "Error executing SQL Statement."
                                 "\nSQL Statement: {}"
                                 "\nStatus Code: {}"
                                 "\nERROR Message: {}".format(sql_command["commands"],
                                                              r.status_code, r.reason) + BColors.ENDC)


def main():
    # Get Credentials
    # TODO: Ask best practices for credentials when dockerizing the application
    f = open("credentials.txt", "r")
    credentials = json.loads(f.read())
    f.close()

    # Create a Db2Connection Object
    db2 = Db2Connection(credentials)

    # Authenticate with the database
    auth_req = db2.authenticate()
    auth_token = auth_req.json()["token"]

    # Check if required tables already exists; if not - create new tables
    schema_info = db2.schema_info(auth_token)
    if not schema_info["Logs"]:
        db2.create_table(auth_token, db2.logs_table)
    if not schema_info["Emp"]:
        db2.create_table(auth_token, db2.employee_details_table)

    # Write Data
    # TODO: Ensure that the license_plate, time parameters are passed appropriately
    #  ##### Auth_Token expires after 1 hr. => ensure to renew token every 55 mins
    license_plate = "22233"
    db2.write_data(auth_token, license_plate)


if __name__ == "__main__":
    main()
