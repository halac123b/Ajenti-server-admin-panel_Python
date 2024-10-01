import logging
import os
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
            if os.geteuid() == 0:
                os.chmod(self.path, 384)  # 0o600
                with open(self.path, 'r') as smtp:
                    self.data = yaml.load(smtp, Loader=yaml.SafeLoader) or {}
                    # Prevent password leak
                    self.ensure_structure()
                    self.data['smtp']['password'] = ''