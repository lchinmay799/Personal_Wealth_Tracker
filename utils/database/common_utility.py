import psycopg2
import json
import psycopg2.sql as sql
from psycopg2.extras import RealDictCursor


class Database:
    def __init__(self):
        with open('utils/config.json') as f:
            config=json.load(f)
            databaseConfig = config["personal_wealth_tracker"]["database"]
            self.host = databaseConfig["localhost"]
            self.port = databaseConfig["port"]
            self.database = databaseConfig["application_database"]
            self.user = databaseConfig["local_username"]
            # self.host = databaseConfig["host"]
            # self.user = databaseConfig["application_username"]
            # self.password = databaseConfig["application_password"]
            self.password=databaseConfig["default_password"]
            self.schema = databaseConfig["application_schema"]

    def connect(self):
        try:
            # connection =psycopg2.connect(database=self.database,
            #                 user=self.user,
            #                 password=self.password,
            #                 host=self.host,
            #                 port=self.port)
            connection =psycopg2.connect(database=self.database,
                            user=self.user,
                            password=self.password,
                            host=self.host)
            print("Successfully established new connection to the Database : {}\n with User : {}\n Password : {}\n Hosted on {} using the Port {}".format(self.database,self.user,self.password,self.host,self.port))
            return connection
        except Exception as e:
            print("Failed to Connect to the Database : {}\n with User : {}\n Password : {}\n Hosted on {} using the Port {} \n Due to exception {}".format(self.database,self.user,self.password,self.host,self.port,e))
            return None
        
    def executeCommand(self,command,cursor,argument=None):
        print("Executing the command : {}".format(command.as_string(cursor)))
        if argument:
            cursor.execute(command,argument)
        else:
            cursor.execute(command)
        print("Executed the command : {}".format(command.as_string(cursor)))
        return cursor
    
    def addNewInvestment(self,investmentType,userId,stockId=None,mutualFundId=None,bankDepositId=None,isActive=True):
        command = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier("InvestmentType"),
                                                                                                                        sql.Identifier("UserId"),
                                                                                                                        sql.Identifier("StockId"),
                                                                                                                        sql.Identifier("MutualFundId"),
                                                                                                                        sql.Identifier("BankDepositId"),
                                                                                                                        sql.Identifier("Active")]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(investmentType),
                                                                                                                       sql.Literal(userId),
                                                                                                                       sql.Literal(stockId),
                                                                                                                       sql.Literal(mutualFundId),
                                                                                                                       sql.Literal(bankDepositId),
                                                                                                                       sql.Literal(isActive)]),
                                                                                            return_column=sql.Identifier("Id"))
                
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newInvestmentId= response.get("Id",False) if response else False
                return newInvestmentId
            
    def addNewSip(self,sipAmount,sipDate,mutualFundId=None,stockId=None):
        command=sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier("SIP"),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier("MutualFundId"),
                                                                                                                        sql.Identifier("StockId"),
                                                                                                                        sql.Identifier("SIPAmount"),
                                                                                                                        sql.Identifier("SIPDate")]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(mutualFundId),
                                                                                                                       sql.Literal(stockId),
                                                                                                                       sql.Literal(sipAmount),
                                                                                                                       sql.Literal(sipDate)]),
                                                                                            return_column=sql.Identifier("Id"))
        
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newSipId=response.get("Id",False) if response else False
                return newSipId
  
    def addNewInvestmentDetail(self,amount,units,investedDate,mutualFundId=None,stockId=None,vestingDetails=None):
        command=sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier("MutualFundId"),
                                                                                                                        sql.Identifier("StockId"),
                                                                                                                        sql.Identifier("Amount"),
                                                                                                                        sql.Identifier("Units"),
                                                                                                                        sql.Identifier("InvestedDate"),
                                                                                                                        sql.Identifier("VestingDetails")]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(mutualFundId),
                                                                                                                       sql.Literal(stockId),
                                                                                                                       sql.Literal(amount),
                                                                                                                       sql.Literal(units),
                                                                                                                       sql.Literal(investedDate),
                                                                                                                       sql.Literal(vestingDetails)]),
                                                                                            return_column=sql.Identifier("Id"))
        
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newOneTimeInvestmentId=response.get("Id",False) if response else False
                return newOneTimeInvestmentId
            
    def markInvestmentInactive(self,investmentId,withdrawalDate):
        command=sql.SQL("UPDATE {schema}.{table} SET {activeColumn}=%s AND {withdrawalDateColumn}=%s WHERE {investmentId}=%s").format(schema=sql.Identifier(self.schema),
                                                                                                   table=sql.Identifier("INVESTMENTS"),
                                                                                                   investmentId=sql.Identifier("Id"),
                                                                                                   activeColumn=sql.Identifier("Active"),
                                                                                                   withdrawalDateColumn=sql.Identifier(withdrawalDate))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[False,withdrawalDate,investmentId])
                connection.commit()

    def getUserInvestments(self,userId):
        command=sql.SQL("SELECT * FROM {schema}.{table} WHERE {userId}=%s").format(schema=sql.Identifier(self.schema),
                                                                                   table=sql.Identifier("INVESTMENTS"),
                                                                                   userId=sql.Identifier("UserId"))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[userId])
                return response