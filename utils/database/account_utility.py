import psycopg2.sql as sql
from psycopg2.extras import RealDictCursor
from .common_utility import Database

class UserAccount(Database):
    def __init__(self):
        super().__init__()
        self.table="USERS"
        self.emailColumn="Email"
        self.nameColumn="Name"
        self.passwordColumn="Password"
        self.idColumn="Id"

    def getUserDetail(self,userEmail,returnValue="Id"):
        command=sql.SQL("SELECT {column} from {schema}.{table} WHERE {table}.{emailColumn} = %s").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier(self.table),
                                                                                            emailColumn=sql.Identifier(self.emailColumn),
                                                                                            column=sql.Identifier(returnValue))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor,argument=[userEmail])
                response=response.fetchone()
                return response.get(returnValue) if response else False
    
    def createUser(self,userEmail,userName,userPassword):
        command = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                                table=sql.Identifier(self.table),
                                                                                                columns=sql.SQL(", ").join([sql.Identifier(self.nameColumn),
                                                                                                                            sql.Identifier(self.emailColumn),
                                                                                                                            sql.Identifier(self.passwordColumn)]),
                                                                                                values=sql.SQL(", ").join([sql.Literal(userName),
                                                                                                                           sql.Literal(userEmail),
                                                                                                                           sql.Literal(userPassword)]),
                                                                                                return_column=sql.Identifier(self.idColumn))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                return response.get(self.idColumn,False) if response else False

    def updatePassword(self,userEmail,userPassword):
        command = sql.SQL("UPDATE {schema}.{table} SET {password}=%s WHERE {email}=%s RETURNING {password}").format(schema=self.schema,
                                                                                                table=sql.Identifier(self.table),
                                                                                                password=sql.Identifier(self.passwordColumn),
                                                                                                email=sql.Identifier(self.emailColumn))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                self.executeCommand(command=command, cursor=cursor,argument=[userPassword,userEmail])
                connection.commit()
                response = cursor.fetchone()
                return response.get(self.passwordColumn,False) if response else False
        
    def getAllUsers(self):
        command = sql.SQL("SELECT * FROM {schema}.{table}").format(schema=sql.Identifier(self.schema),
                                                                    table=sql.Identifier(self.table))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command, cursor=cursor)
                return response.fetchall()