## Builtin
import binascii
import datetime
import hashlib
import secrets

AUTHLIMIT = datetime.timedelta(hours = 8)

class SecurityError(Exception): pass

def validatepassword(connection,username,password):
    """ Validates a user's login 
    
    Chceks username.
    Checks hash of password.
    If valid, generates and registers a new auth token.
    If it fails for any reason, returns False.
    Otherwise, returns a dictionary with keys "userid" and "authtoken".
    """
    try:
        user = connection.execute(""" SELECT userid,salt,hash FROM "users" WHERE name = :username; """,dict(username=username)).fetchone()
        if not user:
            return False
        userid,mysalt,myhash = user
        mysalt = binascii.unhexlify(mysalt)
        mypass = password.encode()
        yourhash = gethash(mysalt,mypass)
        if yourhash != binascii.unhexlify(myhash):
            return False
        authtoken = secrets.token_urlsafe()
        authtime = datetime.datetime.now()
        connection.execute("""INSERT INTO "sessions" (userid, authtoken, authtime) VALUES (:userid,:authtoken,:authtime);""",dict(userid=userid,authtoken=authtoken,authtime=authtime))
    except:
        return False
    else:
        return dict(userid=userid,authtoken=authtoken)


def registerpassword(connection,username,password):
    """ Registers a new password hash in the database """
    duplicateuser = connection.execute("""SELECT * FROM "users" WHERE name = :username;""",dict(username=username)).fetchall()
    if duplicateuser:
        raise KeyError("User already exists")
    mysalt = secrets.randbits(1000)
    mypass = password.encode()
    myhash = gethash(mysalt,mypass)
    connection.execute("""INSERT INTO "users" (name, salt, hash) VALUES (:name, :salt, :hash);""",dict(name = username,
                                                                                  salt = binascii.hexlify(mysalt),
                                                                                  hash = binascii.hexlify(myhash))
                       )
    return True

def gethash(mysalt,mypass):
    """ Function for generating hash from salt and password """
    return hashlib.pbkdf2_hmac("sha512",mypass,mysalt,100000)

def checktoken(connection, userid, authtoken):
    """ Validates a userid/authtoken combination against the stored value """
    old = getoldauthtime()
    return bool(connection.execute("""SELECT * FROM "sessions" WHERE userid = :userid and authtoken = :authtoken and authtime > :old;""",
                               dict(userid=userid, authtoken = authtoken, old = old)).fetchone())

def logout(connection, userid,authtoken):
    """ Logs a user out via his authtoken.
   
    Returns True on success and False on failure.
    """
    try:
        connection.execute("""DELETE FROM "sessions" WHERE userid = :userid and authtoken = :authtoken;""")
    except:
        return False
    else:
        return True

def getoldauthtime():
    """ Convenience function for getting the oldest possible authtime """
    return datetime.datetime.now() - AUTHLIMIT

def purgeoldsessions(connection):
    """ Drops all old sessions from the sessions table """
    old = getoldauthtime()
    connection.execute("""DELETE FROM "sessions" WHERE authtime < :old;""",dict(old=old))

## SECURE FUNCTIONS
import functools
from aldb2.Core import sql

def securedecorator(function):
    """ A decorator to have a function check the user's authtoken before executing.
   
    decorated function should have userid and authtoken as parameters.
    """
    functools.wraps(function)
    def wrapper(*args,userid = None, authtoken = None,**kw):
        if not checktoken(userid,authtoken):
            raise SecurityError("Invalid Token")
        return function(*args,userid=userid,authtoken=authtoken,**kw)
    return wrapper

@securedecorator
def secure_getuserapps(connection,userid,authtoken):
    return sql.getuserapps(connection,userid)

@securedecorator
def secure_getinstalledapps(connection,userid,authtoken):
    return sql.getinstalledapps(connection)


__all__ = ["checktoken", "logout", "registerpassword", "securedecorator", "validatepassword",
           "secure_getuserapps", "secure_getinstalledapps"]