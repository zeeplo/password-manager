#! python3
# config.py - Read and store user configs
import os,re,sys, logging
from pathlib import Path
import shelve, pyinputplus as pyip
from databaseManager import DatabaseManager as dm
from typing import Dict

# Logging settings
logging.disable()
logging.basicConfig(level=logging.INFO, format='%(funcName)s:%(lineno)s %(levelname)s - %(message)s')
logging.basicConfig(level=logging.debug, format='%(fincName)s %(levelname)s - %(message)s')

class Config:

    def __init__(self):
        self.validate_path()
        self.read_user_config()

    def set_name(self, name):
        logging.info('name: %s' % name)
        self.name = name
    
    def set_user(self, user):
        logging.info('user: %s' % user)
        self.user = user
    
    def set_password(self, password):
        logging.info('password: %s' % password)
        self.password = password
    
    def set_email(self, email):
        logging.info('email: %s ' % email)
        self.email = email

    def get_name(self):
        return self.name
    
    def get_user(self):
        return self.user
    
    def get_password(self):
        return self.password
    
    def get_email(self):
        return self.email

    def validate_path(self) -> None:
        """
        Check if the config file exisits\n
        Create a config directory 
        """
        path = Path('./config')
        if not path.exists():
            os.mkdir('./config')
    
    def read_user_config(self) -> None:
        """
        Read the user config file
        """
        path = Path('./config')
        # Check if the user_config file does not exists
        if list(path.glob('user_config.*')) == []:
            self.user_menu()
        else:
            # If user_config file exists
            # Read the contents of it 
            sFile = shelve.open('./config/user_config')
            self.set_name(sFile['name'])
            self.set_user(sFile['user'])
            self.set_password(sFile['password'])
            self.set_email(sFile['email'])
            # Check if the config file username exists in mysql
            # True = table does not exist
            if self.check_sql_table(self.get_user):
                # remove all the purge user config file and start over
                for filename in Path('./config/').glob('user_config.*'):
                    os.unlink(filename)
                self.user_menu()
                pass
            sFile.close()    

    def user_menu(self) -> None:
        """
        User can chose between creating a new sql table or enter an exisiting one
        """
        logging.debug('user_menu BEGIN')

        menuArr = ["Create a new user",
            "Already have a username",
            "QUIT"]
        print('=' * 20 + ' USER ' + '=' * 20)
        option = pyip.inputMenu(menuArr, numbered=True)
        logging.debug('User select: %s' % option)
        # If the user wants to create a new user/new sql table 
        if option == menuArr[0]:
            self.create_user_config()
        # If the user already has a sql table
        if option == menuArr[1]:
            self.existing_user()
        # If the user wants to quit
        if option == menuArr[-1]:
            sys.exit()
        
        logging.debug('user_menu END')
    
    def existing_user(self) -> None:
        """
        If the user already have an existing user
        """
        logging.debug("existing_user BEGIN")

        name = pyip.inputStr("Enter your name:\n")
        user = pyip.inputStr("Enter your username:\n").lower()
        while self.check_sql_table(user):
            user = pyip.inputStr("Username Does not exist. Please enter it again.\n").lower()
            user = re.compile(r'\s*').sub('',user)
        
        password = self.validate_password()
        email = self.validate_email()
        
        logging.debug("Values - name: %s, user: %s, password: %s" % (name,user,password))

        self.write_user_config(name, user, password)
        logging.debug('existing_user END')
    
    def write_user_config(self, name: str, user:str, password:str, email="") -> None:
        """
        Writes the local user information into a shelf file
        """
        # write the user info into shelve file
        shelfFile = shelve.open('./config/user_config')
        shelfFile['name'] = name
        shelfFile['user'] = user
        shelfFile['password'] = password
        shelfFile['email'] = email
        shelfFile.close()
        
            
    def check_sql_table(self, user: str) -> bool:
        """
        Check if the table name exists\n
        True -> table name does not exist\n
        False -> table name exists
        """
        checkUser = dm().execute_query("SHOW TABLES LIKE '%s'" % user,2)
        # if table doesn't exist in database
        if checkUser == []:
            return True
        return False
    
    def create_sql_table(self, user) -> None:
        """
        Creating an sql table with the username
        """
        dm().execute_query("""
            create table %s(
            account_id varchar(255) primary key,
            username varchar(255) not null,
            psword varchar(255) not null,
            app_name varchar(255) not null,
            note varchar(255) default null
            );
        """ % user.lower(), 0)

    def validate_password(self) -> str:
        """
        User enters password and confirms that p1 == p2
        """
        while True:
            p1 = pyip.inputPassword("Create a password:\n")
            p2 = pyip.inputPassword("Confirm password:\n")
            if p1 == p2:
                return p1
            print("Password does not match please try again")

    def validate_email(self):
        """
        Validate user email\n
        User enters email twice, both email values must match and in the right email format
        """
        emailRegx = re.compile(r'''
            [a-zA-Z0-9._%+-]+       # username
            @                       # @ symbol
            [a-zA-Z0-9.-]+          # domain name
            (\.[a-zA-Z]{2,4})       # dot something
        ''', re.VERBOSE)

        while True:
            e1 = pyip.inputStr("Enter your email:\n")
            e2 = pyip.inputStr("Confirm your email\n")
            # If the email format is incorrect, user types in their information again
            if not (re.search(emailRegx,e1)):
                print("Email format incorrect")
                continue
            # Return the email if e1 == e2
            if e1 == e2:
                return e1

    def create_user_config(self) -> None:
        """
        Creates a user config file
        """
        logging.debug('create_user_config BEGIN')
        
        print("Seems like you're information is not on file. Let's set up")
        # User input their name
        name = pyip.inputStr("Please enter your name:\n")
        while True:
            # User input their username which is also used as table name in mysql
            user = pyip.inputStr("Please enter a username:\n").lower()
            # Remove spaces in the username
            user = re.compile(r'\s*').sub('',user)
            
            # If the table does not exist
            if self.check_sql_table(user):
                # Create the table
                self.create_sql_table(user)
                break
            # If the table exist
            print("Username is unavailable. Please try again")
        
        password = self.validate_password()
        email = self.validate_email()
        logging.debug('Values - name: %s, user: %s, password: %s' % (name,user,password))

        self.write_user_config(name, user, password)