import psycopg2.sql as sql
from psycopg2.extras import RealDictCursor
from .common_utility import Database

class BankDeposits(Database):
    def __init__(self):
        super().__init__()
        self.investmentType=3
        self.table="BANK_DEPOSITS"
        self.idColumn="Id"
        self.bankNameColumn="BankName"
        self.amountColumn="Amount"
        self.interestRateColumn="InterestRate"
        self.investedDateColumn="InvestedDate"
        self.interestTypeColumn="InterestType"
        self.maturityDateColumn="MaturityDate"
        self.interestDurationColumn="InterestCalculateDuration"

    def addNewDeposit(self,userId,bank,amount,interest,investmentDate,interestType,maturityDate,interestDuration=None,newInvestment=True):
        command=sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier(self.table),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier(self.bankNameColumn),
                                                                                                                        sql.Identifier(self.amountColumn),
                                                                                                                        sql.Identifier(self.interestRateColumn),
                                                                                                                        sql.Identifier(self.investedDateColumn),
                                                                                                                        sql.Identifier(self.interestTypeColumn),
                                                                                                                        sql.Identifier(self.maturityDateColumn),
                                                                                                                        sql.Identifier(self.interestDurationColumn)]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(bank),
                                                                                                                       sql.Literal(amount),
                                                                                                                       sql.Literal(interest),
                                                                                                                       sql.Literal(investmentDate),
                                                                                                                       sql.Literal(interestType),
                                                                                                                       sql.Literal(maturityDate),
                                                                                                                       sql.Literal(interestDuration)]),
                                                                                            return_column=sql.Identifier(self.idColumn))
        
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newBankDepositId= response.get(self.idColumn,False) if response else False
                if newInvestment:
                    return self.addNewInvestment(userId=userId,investmentType=self.investmentType,bankDepositId=newBankDepositId)
                return newBankDepositId
    
    def getUserBankInvestments(self,userId):
        returnColumns=list(map(lambda columnName:sql.Identifier(columnName),[self.amountColumn,
                                                                             self.bankNameColumn,
                                                                             self.interestRateColumn,
                                                                             self.interestTypeColumn,
                                                                             self.investedDateColumn,
                                                                             self.maturityDateColumn,
                                                                             "Active",
                                                                             "WithdrawalDate"]))
        returnColumns.append(sql.Composed(sql.Identifier(self.schema)+sql.SQL(".")+
                                          sql.Identifier("INVESTMENTS")+sql.SQL(".")+
                                          sql.Identifier(self.idColumn)+sql.SQL(" AS {investmentId}").format(investmentId=sql.Identifier("investmentId"))))
        command=sql.SQL("""SELECT {columns} FROM {schema}.{table} JOIN {schema}.{investmentTable} ON {schema}.{table}.{id}={schema}.{investmentTable}.{bankDepositIdColumn}
                        WHERE {schema}.{investmentTable}.{userIdColumn} = %s""").format(schema=sql.Identifier(self.schema),
                                                                            table=sql.Identifier(self.table),
                                                                            columns=sql.SQL(", ").join(returnColumns),
                                                                            investmentTable=sql.Identifier("INVESTMENTS"),
                                                                            id=sql.Identifier(self.idColumn),
                                                                            bankDepositIdColumn=sql.Identifier("BankDepositId"),
                                                                            userIdColumn=sql.Identifier("UserId"))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[userId])
                return response.fetchall()
    
    def getBankDeposit(self,bankInvestmentId):
        returnColumns=list(map(lambda columnName:sql.Identifier(columnName),[self.bankNameColumn,
                                                                             self.amountColumn,
                                                                             self.interestRateColumn,
                                                                             self.interestTypeColumn,
                                                                             self.investedDateColumn,
                                                                             self.maturityDateColumn,
                                                                             "Active",
                                                                             "WithdrawalDate"]))
        returnColumns.extend([sql.Composed(sql.Identifier(self.schema)+
                                          sql.SQL(".")+sql.Identifier("INVESTMENTS")+
                                          sql.SQL(".")+sql.Identifier(self.idColumn)+
                                          sql.SQL("AS {investmentIdColumn}").format(investmentIdColumn=sql.Identifier("investmentId"))),
                              sql.Composed(sql.Identifier(self.schema)+
                                          sql.SQL(".")+sql.Identifier(self.table)+
                                          sql.SQL(".")+sql.Identifier(self.idColumn)+
                                          sql.SQL("AS {investmentIdColumn}").format(investmentIdColumn=sql.Identifier("bankDepositId")))])
        
        command = sql.SQL("""SELECT {columns} FROM {schema}.{table} JOIN {schema}.{investmentTable} ON {schema}.{table}.{bankDepositId}={schema}.{investmentTable}.{bankDepositIdColumn}
        WHERE {schema}.{investmentTable}.{bankInvestmentId} = %s""").format(schema=sql.Identifier(self.schema),
                                                table=sql.Identifier(self.table),
                                                columns=sql.SQL(", ").join(returnColumns),
                                                bankDepositId=sql.Identifier(self.idColumn),
                                                bankDepositIdColumn=sql.Identifier("BankDepositId"),
                                                investmentTable=sql.Identifier("INVESTMENTS"),
                                                bankInvestmentId=sql.Identifier(self.idColumn))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor,argument=[bankInvestmentId])
                return response.fetchall()
    
    def getAllBankDeposits(self):
        command = sql.SQL("SELECT * FROM {schema}.{table}").format(schema=sql.Identifier(self.schema),
                                                                    table=sql.Identifier(self.table))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command, cursor=cursor)
                return response.fetchall()
            
class Stock(Database):
    def __init__(self):
        super().__init__()
        self.investmentType=1
        self.table="STOCKS"
        self.idColumn="Id"
        self.stockNameColumn="StockName"
        self.sipColumn="SIP"
        self.oneTimeColumn="OneTime"
        self.investedDateColumn="InvestedDate"

    def addNewStockInvestment(self,userId,stockName,investedDate,sip=False,oneTime=True,vestingDetails=None,
                              sipAmount=None,units=None,sipDate=None,
                              oneTimeInvestmentAmount=None):
        command=sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier(self.table),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier(self.stockNameColumn),
                                                                                                                        sql.Identifier(self.sipColumn),
                                                                                                                        sql.Identifier(self.oneTimeColumn),
                                                                                                                        sql.Identifier(self.investedDateColumn)]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(stockName),
                                                                                                                       sql.Literal(sip),
                                                                                                                       sql.Literal(oneTime),
                                                                                                                       sql.Literal(investedDate)]),
                                                                                            return_column=sql.Identifier(self.idColumn))
        
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newStockId= response.get(self.idColumn,False) if response else False
                if sip:
                    return self.addNewSip(sipAmount=sipAmount,sipDate=sipDate,stockId=newStockId)
                elif oneTime:
                    self.addNewInvestmentDetail(amount=oneTimeInvestmentAmount,units=units,investedDate=investedDate,stockId=newStockId,vestingDetails=vestingDetails)
                return self.addNewInvestment(userId=userId,investmentType=self.investmentType,stockId=newStockId)

    def getUserStocks(self,userId):
        returnColumns = list(map(lambda columnName:sql.Identifier(columnName),[self.stockNameColumn,"Active","WithdrawalDate"]))
        groupByColumns=[*returnColumns]
        returnColumns.append(sql.SQL("{schema}.{table}.{id} AS {id}").format(schema=sql.Identifier(self.schema),
                                                                     table=sql.Identifier("INVESTMENTS"),
                                                                     id=sql.Identifier(self.idColumn)))
        returnColumns.append(sql.SQL("COALESCE(SUM({schema}.{investmentDetailsTable}.{investmentDetailsUnits}),0) AS {unitsColumn}").format(unitsColumn=sql.Identifier("Units"),
                                                                                                        table=sql.Identifier(self.table),
                                                                                                        schema=sql.Identifier(self.schema),
                                                                                                        investmentDetailsUnits=sql.Identifier("Units"),
                                                                                                        investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS")))
        groupByColumns.append(sql.SQL("{schema}.{table}.{id}").format(schema=sql.Identifier(self.schema),
                                                                     table=sql.Identifier("INVESTMENTS"),
                                                                     id=sql.Identifier(self.idColumn)))

        command=sql.SQL("""SELECT {columns} FROM {schema}.{table} JOIN {schema}.{investmentTable} ON {schema}.{table}.{id}={schema}.{investmentTable}.{stockIdColumn}
                        LEFT JOIN {schema}.{investmentDetailsTable} ON {schema}.{table}.{id} = {schema}.{investmentDetailsTable}.{stockIdColumn}
                        WHERE {schema}.{investmentTable}.{userIdColumn} = %s GROUP BY {groupByColumns}""").format(schema=sql.Identifier(self.schema),
                                                                            table=sql.Identifier(self.table),
                                                                            columns=sql.SQL(", ").join(returnColumns),
                                                                            investmentTable=sql.Identifier("INVESTMENTS"),
                                                                            id=sql.Identifier(self.idColumn),
                                                                            stockIdColumn=sql.Identifier("StockId"),
                                                                            userIdColumn=sql.Identifier("UserId"),
                                                                            investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                                            groupByColumns=sql.SQL(", ").join(groupByColumns))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[userId])
                return response.fetchall()
    
    def getStock(self,stockInvestmentId):
        returnColumns = list(map(lambda columnName:sql.Identifier(columnName),[self.stockNameColumn,
                                                                               "VestingDetails",
                                                                               "Active",
                                                                               "WithdrawalDate"]))
        returnColumns.append(sql.SQL("COALESCE({sqlColumn},0) AS {sqlColumn}").format(sqlColumn=sql.Identifier("Amount")))
        returnColumns.extend([sql.SQL("{schema}.{investmentTable}.{idColumn}").format(schema=sql.Identifier(self.schema),
                                                                            investmentTable=sql.Identifier("INVESTMENTS"),
                                                                            idColumn=sql.Identifier(self.idColumn)),
                              sql.SQL("COALESCE({schema}.{investmentDetailsTable}.{unitsColumn},0) AS {unitsColumn}").format(schema=sql.Identifier(self.schema),
                                                                                                 investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                 unitsColumn=sql.Identifier("Units")),
                              sql.SQL("{schema}.{investmentDetailsTable}.{investedDate}").format(schema=sql.Identifier(self.schema),
                                                                                                 investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                 investedDate=sql.Identifier(self.investedDateColumn))])
        

        command=sql.SQL("""SELECT {columns} FROM {schema}.{table} JOIN {schema}.{investmentTable} ON {schema}.{table}.{id}={schema}.{investmentTable}.{stockIdColumn}
                        LEFT JOIN {schema}.{investmentDetailsTable} ON {schema}.{table}.{id} = {schema}.{investmentDetailsTable}.{stockIdColumn}
                        WHERE {schema}.{investmentTable}.{id} = %s""").format(schema = sql.Identifier(self.schema),
                                                        table = sql.Identifier(self.table),                                                        investmentDetailsTable = sql.Identifier("INVESTMENT_DETAILS"),
                                                        investmentTable=sql.Identifier("INVESTMENTS"),
                                                        id=sql.Identifier(self.idColumn),
                                                        stockIdColumn=sql.Identifier("StockId"),
                                                        columns = sql.SQL(", ").join(returnColumns))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(cursor=cursor,command=command,argument=[stockInvestmentId])
                return response.fetchall()
    
    def getAllStocks(self):
        command = sql.SQL("SELECT * FROM {schema}.{table}").format(schema=sql.Identifier(self.schema),
                                                                    table=sql.Identifier(self.table))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command, cursor=cursor)
                return response.fetchall()
            
class MutualFund(Database):
    def __init__(self):
        super().__init__()
        self.investmentType=1
        self.table="MUTUAL_FUNDS"
        self.idColumn="Id"
        self.schemeColumn="Scheme"
        self.sipColumn="SIP"
        self.oneTimeColumn="OneTime"
        self.investedDateColumn="InvestedDate"

    def addNewMutualFundInvestment(self,userId,scheme,investedDate,sip=False,oneTime=True,
                              sipAmount=None,units=None,sipDate=None,
                              oneTimeInvestmentAmount=None):
        command=sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values}) RETURNING {return_column}").format(schema=sql.Identifier(self.schema),
                                                                                            table=sql.Identifier(self.table),
                                                                                            columns=sql.SQL(", ").join([sql.Identifier(self.schemeColumn),
                                                                                                                        sql.Identifier(self.sipColumn),
                                                                                                                        sql.Identifier(self.oneTimeColumn),
                                                                                                                        sql.Identifier(self.investedDateColumn)]),
                                                                                            values=sql.SQL(", ").join([sql.Literal(scheme),
                                                                                                                       sql.Literal(sip),
                                                                                                                       sql.Literal(oneTime),
                                                                                                                       sql.Literal(investedDate)]),
                                                                                            return_column=sql.Identifier(self.idColumn))
        
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command,cursor=cursor)
                connection.commit()
                response=response.fetchone()
                newMutualFundId= response.get(self.idColumn,False) if response else False
                if sip:
                    return self.addNewSip(sipAmount=sipAmount,sipDate=sipDate,mutualFundId=newMutualFundId)
                elif oneTime:
                    return self.addNewInvestmentDetail(amount=oneTimeInvestmentAmount,units=units,investedDate=investedDate,mutualFundId=newMutualFundId)
                return self.addNewInvestment(userId=userId,investmentType=self.investmentType,mutualFundId=newMutualFundId)

    def getUserMutualFunds(self,userId):
        returnColumns=list(map(lambda columnName:sql.Identifier(columnName),[self.schemeColumn,"Active","WithdrawalDate","Amount"]))
        groupByColumns=[*returnColumns]
        returnColumns.append(sql.SQL("COALESCE(SUM({schema}.{investmentDetailsTable}.{units}),0) AS {units}").format(schema=sql.Identifier(self.schema),
                                                                                                                     investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                                     units=sql.Identifier("Units")))
        returnColumns.append(sql.SQL("{schema}.{investmentTable}.{id} AS {id}").format(schema=sql.Identifier(self.schema),
                                                                                                 investmentTable=sql.Identifier("INVESTMENTS"),
                                                                                                 id=sql.Identifier(self.idColumn)))
        groupByColumns.append(sql.SQL("{schema}.{investmentTable}.{id}").format(schema=sql.Identifier(self.schema),
                                                                                investmentTable=sql.Identifier("INVESTMENTS"),
                                                                                id=sql.Identifier(self.idColumn)))

        command=sql.SQL("""SELECT {columns} FROM {schema}.{table} JOIN {schema}.{investmentTable} ON {schema}.{table}.{id}={schema}.{investmentTable}.{mutualFundId}
                        LEFT JOIN {schema}.{investmentDetailsTable} ON {schema}.{table}.{id}={schema}.{investmentDetailsTable}.{mutualFundId}
                        WHERE {schema}.{investmentTable}.{userIdColumn} = %s GROUP BY {groupByColumns}""").format(schema=sql.Identifier(self.schema),
                                                                            table=sql.Identifier(self.table),
                                                                            columns=sql.SQL(", ").join(returnColumns),
                                                                            investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                                            investmentTable=sql.Identifier("INVESTMENTS"),
                                                                            id=sql.Identifier(self.idColumn),
                                                                            mutualFundId=sql.Identifier("MutualFundId"),
                                                                            userIdColumn=sql.Identifier("UserId"),
                                                                            groupByColumns=sql.SQL(", ").join(groupByColumns))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[userId])
                return response.fetchall()
            
    def getMutualFund(self,investmentId):
        columns=list(map(lambda column:sql.Identifier(column),["Scheme","Active","WithdrawalDate"]))
        columns.extend(list(map(lambda column:sql.SQL("COALESCE({schema}.{table}.{column},0) AS {column}").format(schema=sql.Identifier(self.schema),
                                                                              table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                              column=sql.Identifier(column)),["Amount","Units"])))
        columns.extend([sql.SQL("{schema}.{investmentDetailsTable}.{investedDate} AS {investedDate}").format(schema=sql.Identifier(self.schema),
                                                                                                                   investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                                   investedDate=sql.Identifier(self.investedDateColumn)),
                      sql.SQL("{schema}.{investmentTable}.{id} AS {id}").format(schema=sql.Identifier(self.schema),
                                                                         investmentTable=sql.Identifier("INVESTMENTS"),
                                                                         id=sql.Identifier(self.idColumn))])
        command=sql.SQL("""SELECT {columns} FROM {schema}.{table} JOIN {schema}.{investmentTable} ON {schema}.{table}.{id}={schema}.{investmentTable}.{mutualFundId}
                    LEFT JOIN {schema}.{investmentDetailsTable} ON {schema}.{table}.{id}={schema}.{investmentDetailsTable}.{mutualFundId}
                    WHERE {schema}.{investmentTable}.{id}=%s""").format(columns=sql.SQL(", ").join(columns),
                                                             schema=sql.Identifier(self.schema),
                                                             table=sql.Identifier(self.table),
                                                             investmentTable=sql.Identifier("INVESTMENTS"),
                                                             investmentDetailsTable=sql.Identifier("INVESTMENT_DETAILS"),
                                                             mutualFundId=sql.Identifier("MutualFundId"),
                                                             id=sql.Identifier(self.idColumn))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response=self.executeCommand(command=command,cursor=cursor,argument=[investmentId])
                return response.fetchall()
    
    def getAllMutualFunds(self):
        command = sql.SQL("SELECT * FROM {schema}.{table}").format(schema=sql.Identifier(self.schema),
                                                                    table=sql.Identifier(self.table))
        with self.connect() as connection:
            with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                response = self.executeCommand(command=command, cursor=cursor)
                return response.fetchall()