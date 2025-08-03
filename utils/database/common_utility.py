import psycopg2
import json
import psycopg2.sql as sql
from psycopg2.extras import RealDictCursor
from utils.logger import logger

class Database:
    def __init__(self):
        self.logger=logger()
        self.logger=self.logger.getLogger()
        with open('utils/config.json') as f:
            config=json.load(f)
            databaseConfig = config["personal_wealth_tracker"]["database"]
            # self.host = databaseConfig["localhost"]
            self.port = databaseConfig["port"]
            self.database = databaseConfig["application_database"]
            # self.user = databaseConfig["local_username"]
            self.host = databaseConfig["host"]
            self.user = databaseConfig["application_username"]
            self.password = databaseConfig["application_password"]
            # self.password=databaseConfig["default_password"]
            self.schema = databaseConfig["application_schema"]

    def connect(self):
        try:
            connection =psycopg2.connect(database=self.database,
                            user=self.user,
                            password=self.password,
                            host=self.host,
                            port=self.port)
            # connection =psycopg2.connect(database=self.database,
            #                 user=self.user,
            #                 password=self.password,
            #                 host=self.host)
            self.logger.info("Successfully established new connection to the Database : {}\n with User : {}\n Password : {}\n Hosted on {} using the Port {}".format(self.database,self.user,self.password,self.host,self.port))
            return connection
        except Exception as e:
            self.logger.info("Failed to Connect to the Database : {}\n with User : {}\n Password : {}\n Hosted on {} using the Port {} \n Due to exception {}".format(self.database,self.user,self.password,self.host,self.port,e))
            return None
        
    def executeCommand(self,command,cursor,argument=None):
        self.logger.info("Executing the command : {} with argument {}".format(command.as_string(cursor),argument))
        if argument:
            cursor.execute(command,argument)
        else:
            cursor.execute(command)
        self.logger.info("Executed the command : {}".format(command.as_string(cursor)))
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
  
    def addNewInvestmentDetail(self,amount,units,investedDate,mutualFundId=None,stockId=None,sipId=None):
        command=sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier("MutualFundId"),
                                                                                                                        sql.Identifier("StockId"),
                                                                                                                        sql.Identifier("Amount"),
                                                                                                                        sql.Identifier("Units"),
                                                                                                                        sql.Identifier("InvestedDate"),
                                                                                                                        sql.Identifier("SIPID")]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(mutualFundId),
                                                                                                                       sql.Literal(stockId),
                                                                                                                       sql.Literal(amount),
                                                                                                                       sql.Literal(units),
                                                                                                                       sql.Literal(investedDate),
                                                                                                                       sql.Literal(sipId)]),
                                                                                            return_column=sql.Identifier("Id"))
        
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newOneTimeInvestmentId=response.get("Id",False) if response else False
                return newOneTimeInvestmentId
            
    def markInvestmentInactive(self,investmentId,withdrawalDate):
        command=sql.SQL("UPDATE {schema}.{table} SET {activeColumn}=%s, {withdrawalDateColumn}=%s WHERE {investmentId}=%s").format(schema=sql.Identifier(self.schema),
                                                                                                   table=sql.Identifier("INVESTMENTS"),
                                                                                                   investmentId=sql.Identifier("Id"),
                                                                                                   activeColumn=sql.Identifier("Active"),
                                                                                                   withdrawalDateColumn=sql.Identifier("WithdrawalDate"))
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
            
    def updateSIP(self,columns,values,investmentId=None,investmentTypeId=None,sipId=None):
        updateColumns=[sql.SQL("{column} = {value}").format(column=sql.Identifier(column),
                                                            value=sql.Literal(value)) for column,value in zip(columns,values)]
        if sipId is None:
            command=sql.SQL("""UPDATE {schema}.{table} SET {updateColumns} WHERE {schema}.{table}.{investmentTypeId} = 
                    (SELECT {investmentTypeId} FROM {schema}.{investmentTable} WHERE {schema}.{investmentTable}.{id} = %s)""").format(schema=sql.Identifier(self.schema),
                                                                                                            table=sql.Identifier("SIP"),
                                                                                                            updateColumns=sql.SQL(", ").join(updateColumns),
                                                                                                            investmentTypeId=sql.Identifier(investmentTypeId),
                                                                                                            investmentTable=sql.Identifier("INVESTMENTS"),
                                                                                                            id=sql.Identifier("Id"))
            argument=[investmentId]
        else:
            command=sql.SQL("""UPDATE {schema}.{table} SET {updateColumns} WHERE {sipId} = %s""").format(schema=sql.Identifier(self.schema),
                                                                                                         table=sql.Identifier("SIP"),
                                                                                                         updateColumns=sql.SQL(", ").join(updateColumns),
                                                                                                         sipId=sql.Identifier("Id"))
            argument=[sipId]
            
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                self.executeCommand(command=command,cursor=cursor,argument=argument)
                connection.commit()

    def getInvestmentType(self,investmentId):
        command=sql.SQL("SELECT {investmentType} FROM {schema}.{table} WHERE {investmentId}=%s").format(schema=sql.Identifier(self.schema),
                                                                                                        table=sql.Identifier("INVESTMENTS"),
                                                                                                        investmentType=sql.Identifier("InvestmentType"),
                                                                                                        investmentId=sql.Identifier("Id"))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[investmentId])
                return response.fetchone()
            
    def getSIPToday(self,sipDate):
        command=sql.SQL("""SELECT {columns} FROM {schema}.{table}  WHERE {sipDate}=%s""").format(schema=sql.Identifier(self.schema),
                                                                                        table=sql.Identifier("SIP"),
                                                                                        columns=sql.SQL(", ").join(list(map(lambda column:sql.Identifier(column),
                                                                                                                            ["Id","StockId","MutualFundId",
                                                                                                                             "SIPAmount"]))),
                                                                                        sipDate=sql.Identifier("SIPDate"))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[sipDate])
                return response.fetchall()
            
    def getInvestmentStatus(self,stockId=None,mutualFundId=None):
        if stockId is not None:
            argument=[stockId]
            command=sql.SQL("""SELECT {active} FROM {schema}.{investmentsTable} JOIN {schema}.{stocks} ON {schema}.{stocks}.{id}={schema}.{investmentsTable}.{stockId}
            WHERE {schema}.{stocks}.{id}=%s""").format(schema=sql.Identifier(self.schema),
                                                    active=sql.Identifier("Active"),
                                                    stocks=sql.Identifier("STOCKS"),
                                                    investmentsTable=sql.Identifier("INVESTMENTS"),
                                                    id=sql.Identifier("Id"),
                                                    stockId=sql.Identifier("StockId"))
        elif mutualFundId is not None:
            argument=[mutualFundId]
            command=sql.SQL("""SELECT {active} FROM {schema}.{investmentsTable} JOIN {schema}.{mutualFunds} ON {schema}.{mutualFunds}.{id}={schema}.{investmentsTable}.{mutualFundId}
            WHERE {schema}.{mutualFunds}.{id}=%s""").format(schema=sql.Identifier(self.schema),
                                                    active=sql.Identifier("Active"),
                                                    mutualFunds=sql.Identifier("MUTUAL_FUNDS"),
                                                    investmentsTable=sql.Identifier("INVESTMENTS"),
                                                    id=sql.Identifier("Id"),
                                                    mutualFundId=sql.Identifier("MutualFundId"))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,argument=argument,cursor=cursor)
                return response.fetchone()