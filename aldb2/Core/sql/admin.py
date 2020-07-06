###############  installed_apps
@util.row_factory_saver
def getinstalledapps(connection):
    """ Returns a list of apps registered with the database.

    The return is a list of dictionaries with keys "app" and "version".
    """
    installed = connection.execute("""SELECT module,version FROM "installed_apps";""").fetchall()
    return [dict(app=app[0],version=app[1]) for app in installed]

@util.row_factory_saver
def getappbyname(connection,appname):
    """ Returns an app's information based on app name """
    result = connection.execute("""SELECT * FROM "installed_apps" WHERE module = :appname;""",dict(appname=appname)).fetchone()
    if result:
        return {"installid":result[0],"module":result[1],"version":result[2]}
    return None


def installapp(connection,app):
    """ Registers a new app with the database. Returns module and config """
    try:
        module,config = util.loadapp(app)
    except:
        raise FileNotFoundError("Could not locate App in Program Directory")
    if not module or not config:
        raise AttributeError("Could not load App's module or configuration file.")
    util.loadtables(module,config,connection)
    connection.execute("""INSERT INTO "installed_apps" (module, version) VALUES (:app, :version);""",dict(app = app, version = config['version']))
    return module,config

############## user_apps

def getuserapps(connection,userid):
    """ Returns a list of installed apps that the user has elected to use.

    Returns a list of dictionaries with keys: "installation id", "app", and "version".
    """
    userapps = connection.execute("""
SELECT "installed_apps".installid, "installed_apps".module, "installed_apps".version
FROM "user_apps"
LEFT JOIN "installed_apps" ON "user_apps".installid = "installed_apps".installid
WHERE userid = :userid;""",
dict(userid=userid) ).fetchall()
    return [ { "installation id":uapp[0], "app":uapp[1], "version":uapp[2]} for uapp in userapps]


def registeruserapp(connection,installationid,userid):
    """ Registers an app for a user's account using the installationid and userid. """
    connection.execute("""INSERT INTO "user_apps" (userid, installid) VALUES (:userid, :installationid);""",dict(userid=userid, installationid = installationid))


