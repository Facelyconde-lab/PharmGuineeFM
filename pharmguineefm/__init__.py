# PyMySQL fait passer pour "MySQLdb" (évite mysqlclient et son compilateur C,
# utile sous Windows). Mais on tourne en SQLite partout pour l'instant (voir
# settings.py, DB_ENGINE) - pymysql n'est même pas installé sur PythonAnywhere,
# donc import optionnel pour pas planter tout manage.py là-bas.
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
