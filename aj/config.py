import logging
import os
import sys
import yaml

class BaseConfig():
    """
    A base class for config implementations. Your implementation must be able to save
    arbitrary mixture of ``dict``, ``list``, and scalar values.

    .. py:attribute:: data

        currently loaded config content

    """
    def __init__(self):
        # Dictionary chứa các config data
        self.data = None

    def load(self):
        """
        Should load config content into :attr:`data`.
        """
        raise NotImplementedError()
    
    def save(self):
        """
        Should save config content from :attr:`data`.
        """
        raise NotImplementedError()
    
    def ensure_structure(self):
        '''Set up dictionary data với các giá trị default'''
        # Global options
        self.data.setdefault('name', None)
        self.data.setdefault('trusted_domains', [])
        self.data.setdefault('trusted_proxies', [])
        self.data.setdefault('max_sessions', 99)
        self.data.setdefault('session_max_time', 3600)
        self.data.setdefault('language', 'en')
        self.data.setdefault('restricted_user', 'nobody')
        self.data.setdefault('logo', os.path.dirname(__file__) + '/static/images/Logo.png')

        # Main view
        self.data.setdefault('view', {})
        self.data['view'].setdefault('plugin', 'core')
        self.data['view'].setdefault('filepath', 'content/pages/index.html')

         # Authentication
        self.data.setdefault('auth', {})
        self.data['auth'].setdefault('emails', {})
        self.data['auth'].setdefault('provider', 'os')
        self.data['auth'].setdefault('users_file', '/etc/ajenti/users.yml')

        # SSL
        self.data.setdefault('ssl', {})
        self.data['ssl'].setdefault('enable', False)
        self.data['ssl'].setdefault('certificate', None)
        self.data['ssl'].setdefault('fqdn_certificate', None)
        self.data['ssl'].setdefault('force', False)
        self.data['ssl'].setdefault('client_auth', {})
        self.data['ssl']['client_auth'].setdefault('enable', False)
        self.data['ssl']['client_auth'].setdefault('force', False)
        self.data['ssl']['client_auth'].setdefault('certificates', [])
        if self.data['ssl']['client_auth']['certificates'] is None:
            self.data['ssl']['client_auth']['certificates'] = []

        # Emails
        self.data.setdefault('email', {})
        self.data['email'].setdefault('enable', False)
        self.data['email'].setdefault('templates', {})

        # Before Ajenti 2.1.38, the users were stored in config.yml
        if 'users' in self.data['auth'].keys():
            logging.warning(f"Users should be stored in {self.data['auth']['users_file']}, migrating it ...")
            self.migrate_users_to_own_configfile()

    def migrate_users_to_own_configfile(self):
        users_path = self.data['auth']['users_file']

        # Nếu file đã có sẵn, chuyển thành file backup (.bak)
        if os.path.isfile(users_path):
            logging.info(f"{users_path} already existing, backing it up")
            os.rename(users_path, users_path + '.bak')
        
        # Save data from YAML file
        to_write = {'users': self.data['auth']['users']}
        with open(users_path, 'w') as f:
           f.write(yaml.safe_dump(to_write, default_flow_style=False, encoding='utf-8', allow_unicode=True).decode('utf-8'))

        del self.data['auth']['users']  # Xoá data cũ đi
        # self.save()
        logging.info(f"{users_path} correctly written")
        
    def get_non_sensitive_data(self):
        return {
            'color': self.data['color'],
            'language': self.data['language'],
            'name': self.data['name'],
            'session_max_time': self.data['session_max_time'],
        }

# SMTP: Simple mail transfer protocol
class SmtpConfig(BaseConfig):
    """
    Class to handle the smtp config file in order to store credentials of the email
    server relay.
    Config file is located at /etc/ajenti/smtp.yml and should have the following
    structure :
    smtp:
    port: starttls or ssl
    server: myserver.domain.com
    user: user to authenticate
    password: password of the mail user
    """
    def __init__(self):
        BaseConfig.__init__(self)
        self.data = {}
        self.path = '/etc/ajenti/smtp.yml'

    def ensure_structure(self):
        self.data.setdefault('smtp', {})
        self.data['smtp'].setdefault('password', None)
        self.data['smtp'].setdefault('port', None)
        self.data['smtp'].setdefault('server', None)
        self.data['smtp'].setdefault('user', None)

    def get_smtp_password(self):
        # if smtp.yml is not provided
        if self.data['smtp']['password'] is None:
            return ''
        with open(self.path, 'r') as smtp:
            smtp_config = yaml.load(smtp, Loader=yaml.SafeLoader).get('smtp', {})
        return smtp_config.get('password', None)
    
    def load(self):
        if not os.path.exists(self.path):
            logging.error(f'Smtp credentials file "{self.path}" not found')
        else:
            if os.geteuid() == 0:   # If run with admin (sudo)
                os.chmod(self.path, 384)  # 0o600
                with open(self.path, 'r') as smtp:
                    self.data = yaml.load(smtp, Loader=yaml.SafeLoader) or {}
                    # Prevent password leak
                    self.ensure_structure()
                    self.data['smtp']['password'] = ''

    def save(self, data):
        # Prevent emptying password from settings plugin
        if not data['smtp']['password']:
            data['smtp']['password'] = self.get_smtp_password()
        # Mở file ra write data mới vào
        with open(self.path, 'w') as smtp:
            smtp.write(
                yaml.safe_dump(
                    data,
                    default_flow_style=False,
                    encoding='utf-8',
                    allow_unicode=True
                ).decode('utf-8')
            )
        

class AjentiUsers(BaseConfig):
    """
    Class to handle the users config file for the auth-user plugin.
    Config file is located at /etc/ajenti/users.yml and should have the following
    structure:
    users:
      username:
        email: ...@...
        password: hash
        permissions: {}
        uid: int
        fs_root: file system root directory
    """
    def __init__(self, path):
        BaseConfig.__init__(self)
        self.data = None
        self.path = os.path.abspath(path)
    
    def __str__(self):
        return self.path
    
    def load(self):
        '''Load user data from config file'''
        if not os.path.exists(self.path):   # If path not exist
            logging.error(f'Users file "{self.path}" not found')
            self.data = {'users': {}}
        else:
            if os.geteuid() == 0:
                os.chmod(self.path, 384)  # 0o600
            with open(self.path, 'r') as users:
                self.data = yaml.load(users, Loader=yaml.SafeLoader)
            if self.data['users'] is None:
                self.data['users'] = {}
    
    def save(self):
        with open(self.path, 'w') as f:
            f.write(yaml.safe_dump(self.data, default_flow_style=False, encoding='utf-8', allow_unicode=True).decode('utf-8'))

# TFA: Two Factor Auth
class TFAConfig(BaseConfig):
    """
    Class to handle the TFA yaml file which contains secrets for e.g. TOTP
    Time-based one-time password: OTP đc tạo dựa trên data thời gian hiện tại
    Config file is located at /etc/ajenti/tfa.yml and should have the following
    structure :
    totp:
      user@auth_id:
        secret_id:
          created: DATE
          description: DESCRIPTION
          secret: random key in base32 with 32 chars
    """
    def __init__(self):
        BaseConfig.__init__(self)
        self.data = {}
        self.path = '/etc/ajenti/tfa.yml'
        self.verify_totp = {}

    def get_user_totp_secrets(self, userid):
        with open(self.path, 'r') as tfa:
            tfa_config = yaml.load(tfa, Loader=yaml.SafeLoader).get('users', {})
            user_secrets = tfa_config.get(userid, {}).get('totp', [])
        return [details['secret'] for details in user_secrets]
    
    def append_user_totp(self, data):
        config = self._read()
        userid = data['userid']
        if config['users'].get(userid, {}).get('totp', []):
            config['users'][userid]['totp'].append(data['secret_details'])
            self.verify_totp[userid] = None
        else:
            config['users'][userid] = {'totp': [data['secret_details']]}
        self._save(config)
        # Save data rồi clear các cache vừa chạy
        self.load()

    def delete_user_totp(self, data):
        config = self._read()
        userid = data['userid']
        totps = config['users'].get(userid, {}).get('totp', [])
        for secret in totps:
            if str(secret['created']) == data['timestamp']:
                if len(totps) == 1:
                    # Remove completely user entry
                    del config['users'][userid]
                else:
                    config['users'][userid]['totp'].remove(secret)
                break
        self._save(config)
        self.load()

    def _read(self):
        '''Load config data from file'''
        if os.path.exists(self.path):
            with open(self.path, 'r') as tfa:
                return yaml.load(tfa, Loader=yaml.SafeLoader)
        else:
            return {'users': {}}
        
    def _save(self, data):
        '''Save data to file'''
        with open(self.path, 'w') as tfa:
            tfa.write(
                yaml.safe_dump(
                    data,
                    default_flow_style=False,
                    encoding='utf-8',
                    allow_unicode=True
                ).decode('utf-8')
           )
        os.chmod(self.path, 384)  # 0o600

    def load(self):
        if os.path.exists(self.path):
            os.chmod(self.path, 384)  # 0o600
            with open(self.path, 'r') as tfa:
                self.data = yaml.load(tfa, Loader=yaml.SafeLoader).get('users', {})
            # Don't keep secrets in memory and prepare verify values per user involved
            for userid, tfa_methods in self.data.items():
                self.verify_totp[userid] = None
                for _, values in tfa_methods.items():
                    for entry in values:
                        entry['secret'] = ''
        else:
            self.ensure_structure()

    def ensure_structure(self):
        self.data.setdefault('users', {})