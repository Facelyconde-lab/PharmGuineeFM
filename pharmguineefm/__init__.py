# PyMySQL se fait passer pour le driver "MySQLdb" que Django attend par
# défaut. On l'utilise à la place de mysqlclient car PyMySQL est écrit en
# pur Python : aucune compilation nécessaire, ce qui évite des soucis
# d'installation sous Windows (mysqlclient demande normalement un
# compilateur C et les en-têtes MySQL).
import pymysql

pymysql.install_as_MySQLdb()
