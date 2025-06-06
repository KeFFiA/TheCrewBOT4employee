from typing import Any

import psycopg2

import config
from Bot.Utils.logging_settings import database_logger
from config import host, user, password, db_name, port


class Database:
    def __init__(self, host, port, db_name, user, password):
        try:
            self.connect = psycopg2.connect(host=host,
                                            port=port,
                                            database=db_name,
                                            user=user,
                                            password=password,
                                            options="-c client_encoding=UTF8")
            self.cursor = self.connect.cursor()
            database_logger.debug(f'DataBase - *{db_name}* connection...')
            with self.connect.cursor() as cursor:
                cursor.execute(
                    "SELECT version();"
                )
                database_logger.debug(f'Server version: {cursor.fetchone()[0]}')
        except Exception as _ex:
            database_logger.critical(f'Can`t establish connection to DataBase with error: {_ex}')

    msg = 'The sql query failed with an error'  # Default error query message, when DEBUG -> False
    def execute_query(self, query: str, values: tuple, fetch: str = None, log_level: int = 40, msg: str = msg, debug: bool = config.debug) -> any or None:
        try:
            if values is None:
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, values)

            if fetch == 'fetchone' or fetch == 'one':
                return self.cursor.fetchone()
            elif fetch == 'fetchall' or fetch == 'all':
                return self.cursor.fetchall()
            elif fetch == 'fetchmany' or fetch == 'many':
                return self.cursor.fetchmany()
            return None
        except Exception as ex:
            if debug:
                database_logger.log(msg=ex, level=log_level)
                self.rollback()
                return None
            else:
                database_logger.log(msg=msg, level=log_level)
                self.rollback()
                return None

    def commit(self):
        self.connect.commit()

    def rollback(self):
        self.connect.rollback()

    def close(self):
        self.cursor.close()
        self.connect.close()

    def query(self, query: str, values: tuple = None, fetch: str = None, log_level: int = 40, msg: str = msg, debug: bool = config.debug) -> any:
        """
        :param query: takes sql query, for example: "SELECT * FROM table"
        :param values: takes tuple of values
        :param fetch: choose of one upper this list
        :param log_level: choose of logging level if needed. Default 40[ERROR]
        :param msg: message for logger
        :param debug: make Exception error message

        - fetch:
            1. fetchone
            2. fetchall
            3. fetchmany - size required(default 10)
            4. None - using for UPDATE, DELETE etc.

        - log_level:
            1. 10 (Debug) - the lowest logging level, intended for debugging messages, for displaying diagnostic information about the application.
            2. 20 (Info) - this level is intended for displaying data about code fragments that work as expected.
            3. 30 (Warning) - this logging level provides for the display of warnings, it is used to record information about events that a programmer usually pays attention to. Such events may well lead to problems during the operation of the application. If you do not explicitly set the logging level, the warning is used by default.
            4. 40 (Error)(default) - this logging level provides for the display of information about errors - that part of the application does not work as expected, that the program could not execute correctly.
            5. 50 (Critical) - this level is used to display information about very serious errors, the presence of which threatens the normal functioning of the entire application. If you do not fix such an error, this may lead to the application ceasing to work.
        """
        try:
            self.cursor.execute("SAVEPOINT point1")
            result = self.execute_query(query, values, fetch, log_level=log_level)
            self.commit()
            return result
        except Exception as ex:
            if debug:
                database_logger.log(msg=ex, level=log_level)
                self.rollback()
                return 'Error'
            else:
                database_logger.log(msg=msg, level=log_level)
                self.rollback()
                return 'Error'


db = Database(host=host, port=port, db_name=db_name, user=user, password=password)

create_users_table = """
CREATE TABLE IF NOT EXISTS users (
    user_id NUMERIC(50) UNIQUE NOT NULL,
    user_name TEXT CHECK (char_length(user_name) <= 500),
    username TEXT CHECK (char_length(username) <= 500),
    user_surname TEXT CHECK (char_length(user_surname) <= 500),
    is_registered BOOLEAN DEFAULT FALSE NOT NULL,
    is_employee BOOLEAN DEFAULT FALSE NOT NULL,
    tg_promo BOOLEAN DEFAULT FALSE NOT NULL,
    sms_promo BOOLEAN DEFAULT FALSE NOT NULL,
    email_promo BOOLEAN DEFAULT FALSE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    is_smm BOOLEAN DEFAULT FALSE NOT NULL,
    id SERIAL PRIMARY KEY
);
"""

create_white_list_table = """
    CREATE TABLE IF NOT EXISTS white_list (
        id SERIAL PRIMARY KEY,
        user_id NUMERIC(50) UNIQUE NOT NULL,
        admin BOOLEAN DEFAULT FALSE,
        super_admin BOOLEAN DEFAULT FALSE
    )
    """

create_tokens_table = """
    CREATE TABLE IF NOT EXISTS tokens (
        id SERIAL PRIMARY KEY,
        org_name TEXT DEFAULT NULL,
        api_token_cloud TEXT UNIQUE UNIQUE NULL,
        token_cloud_endpont TEXT UNIQUE DEFAULT 'Bearer '
    )
    """

create_employee_table = """
    CREATE TABLE IF NOT EXISTS employee_list (
        id SERIAL PRIMARY KEY,
        user_id NUMERIC(50) UNIQUE DEFAULT NULL,
        emp_id TEXT DEFAULT NULL,
        name TEXT DEFAULT NULL,
        phone TEXT DEFAULT NULL,
        term_open TEXT DEFAULT NULL,
        org_open TEXT DEFAULT NULL,
        time_opened TEXT DEFAULT NULL,
        receive_upd_shift BOOLEAN DEFAULT TRUE,
        receive_shift_time BOOLEAN DEFAULT TRUE,
        receive_messages BOOLEAN DEFAULT TRUE
        )
    """

create_employee_server_table = """
    CREATE TABLE IF NOT EXISTS employee_server (
        id SERIAL PRIMARY KEY,
        org_name TEXT DEFAULT NULL,
        employee_id TEXT UNIQUE DEFAULT NULL,
        name TEXT DEFAULT NULL,
        role TEXT DEFAULT NULL
        )
    """

create_organizations_table = """
    CREATE TABLE IF NOT EXISTS organizations (
        id SERIAL PRIMARY KEY,
        name TEXT DEFAULT NULL,
        org_id TEXT UNIQUE DEFAULT NULL,
        terminal_groups TEXT DEFAULT NULL
        )
    """

create_employee_couriers_table = """
    CREATE TABLE IF NOT EXISTS employee_couriers (
        id SERIAL PRIMARY KEY,
        name TEXT DEFAULT NULL,
        employee_id TEXT UNIQUE DEFAULT NULL,
        org_ids TEXT DEFAULT NULL
        )
    """

create_stop_list_table = """
    CREATE TABLE IF NOT EXISTS stop_list (
        org_id TEXT DEFAULT NULL,
        name TEXT DEFAULT NULL,
        item_id TEXT UNIQUE DEFAULT NULL,
        date_add Text DEFAULT NULL,
        balance INTEGER DEFAULT NULL
        )
    """

create_menu_table = """
    CREATE TABLE IF NOT EXISTS menu (
        org_id TEXT DEFAULT NULL,
        name TEXT DEFAULT NULL,
        item_id TEXT UNIQUE DEFAULT NULL
        )
    """

create_iiko_login_table = """
    CREATE TABLE IF NOT EXISTS iiko_login(
    org_name TEXT UNIQUE DEFAULT NULL,
    path TEXT DEFAULT NULL,
    port TEXT DEFAULT NULL,
    login TEXT DEFAULT NULL,
    password TEXT DEFAULT NULL,
    token TEXT DEFAULT NULL
    )
"""

create_loyalty_program_table = """
    CREATE TABLE IF NOT EXISTS loyalty_program (
        org_id TEXT DEFAULT NULL,
        id TEXT UNIQUE DEFAULT NULL,
        name TEXT DEFAULT NULL,
        description TEXT DEFAULT NULL,
        serviceFrom TEXT DEFAULT NULL,
        serviceTo TEXT DEFAULT NULL,
        notifyAboutBalanceChanges BOOLEAN DEFAULT NULL,
        programType INT DEFAULT NULL,
        isActive BOOLEAN DEFAULT NULL,
        walletId TEXT DEFAULT NULL,
        marketingCampaignsIds TEXT DEFAULT NULL,
        appliedOrganizations TEXT DEFAULT NULL,
        templateType INT DEFAULT NULL,
        hasWelcomeBonus BOOLEAN DEFAULT NULL,
        welcomeBonusSum NUMERIC DEFAULT NULL,
        isExchangeRateEnabled BOOLEAN DEFAULT NULL,
        refillType INT DEFAULT NULL
    )
"""

create_loyalty_marketing_campaigns_table = """
    CREATE TABLE IF NOT EXISTS loyalty_marketing_campaigns (
        org_id TEXT DEFAULT NULL,
        programId TEXT DEFAULT NULL,
        id TEXT UNIQUE DEFAULT NULL,
        name TEXT DEFAULT NULL,
        description TEXT DEFAULT NULL,
        isActive BOOLEAN DEFAULT NULL,
        periodFrom TEXT DEFAULT NULL,
        periodTo TEXT DEFAULT NULL,
        orderActionConditionBindings TEXT DEFAULT NULL,
        periodicActionConditionBindings TEXT DEFAULT NULL,
        overdraftActionConditionBindings TEXT DEFAULT NULL,
        guestRegistrationActionConditionBindings TEXT DEFAULT NULL
    )
"""

create_customer_categories_table = """
    CREATE TABLE IF NOT EXISTS customer_categories (
        org_id TEXT DEFAULT NULL,
        id TEXT UNIQUE DEFAULT NULL,
        name TEXT DEFAULT NULL,
        isActive BOOLEAN DEFAULT NULL,
        isDefaultForNewGuests BOOLEAN DEFAULT NULL
    )
"""

create_customers_table = """
    CREATE TABLE IF NOT EXISTS customers (
        user_id NUMERIC(50) UNIQUE NOT NULL,
        guest_id TEXT DEFAULT NULL,
        card_track TEXT DEFAULT NULL,
        card_number TEXT DEFAULT NULL,
        name TEXT DEFAULT NULL,
        middlename TEXT DEFAULT NULL,
        surname TEXT DEFAULT NULL,
        birthday TEXT DEFAULT NULL,
        sex TEXT DEFAULT '0',
        phone TEXT DEFAULT NULL,
        email TEXT DEFAULT NULL,
        referrer_id TEXT DEFAULT NULL,
        receive_promo TEXT DEFAULT TRUE,
        consent_status TEXT DEFAULT '0',
        comment TEXT DEFAULT NULL,
        category TEXT DEFAULT NULL
    )
"""


create_defaults_texts_table = """
    CREATE TABLE IF NOT EXISTS defaults_texts (
        type TEXT DEFAULT NULL,
        name TEXT DEFAULT NULL,
        text TEXT DEFAULT NULL 
    )
"""


db.query(query=create_defaults_texts_table)
db.query(query=create_users_table)
db.query(query=create_white_list_table)
db.query(query=create_tokens_table)
db.query(query=create_employee_table)
db.query(query=create_organizations_table)
db.query(query=create_employee_couriers_table)
db.query(query=create_stop_list_table)
db.query(query=create_menu_table)
db.query(query=create_iiko_login_table)
db.query(query=create_employee_server_table)
db.query(query=create_loyalty_program_table)
db.query(query=create_loyalty_marketing_campaigns_table)
db.query(query=create_customer_categories_table)
db.query(query=create_customers_table)


if __name__ == "__main__":
    db.query(query=create_defaults_texts_table)
    db.query(query=create_users_table)
    db.query(query=create_white_list_table)
    db.query(query=create_tokens_table)
    db.query(query=create_employee_table)
    db.query(query=create_organizations_table)
    db.query(query=create_employee_couriers_table)
    db.query(query=create_stop_list_table)
    db.query(query=create_menu_table)
    db.query(query=create_iiko_login_table)
    db.query(query=create_employee_server_table)
    db.query(query=create_loyalty_program_table)
    db.query(query=create_loyalty_marketing_campaigns_table)
    db.query(query=create_customer_categories_table)
    db.query(query=create_customers_table)
