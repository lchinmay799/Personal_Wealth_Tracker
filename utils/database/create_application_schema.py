import psycopg2
import psycopg2.sql as sql
import json

class Database:
    def __init__(self):
        with open('utils/config.json') as f:
            config=json.load(f)
            self.databaseConfig = config["personal_wealth_tracker"]["database"]

    def connect(self,database,user,password,host,port=None):
        try:
            # connection =psycopg2.connect(database=database,
            #                 user=user,
            #                 password=password,
            #                 host=host,
            #                 port = port)
            connection =psycopg2.connect(database=database,
                            user=user,
                            password=password,
                            host=host)
            print("Successfully established new connection to the Database : {}\n with User : {}\n Password : {}\n Hosted on {} using the Port {}".format(database,user,password,host,port))
            return connection
        except Exception as e:
            print("Failed to Connect to the Database : {}\n with User : {}\n Password : {}\n Hosted on {} using the Port {} \n Due to exception {}".format(database,user,password,host,port,e))
    
    def createUser(self,user,password,connection):
        command = sql.SQL("CREATE USER {user} WITH PASSWORD {password} CREATEDB").format(user=sql.Identifier(user),password=sql.Placeholder())
        self.executeCommand(command=command,connection=connection,argument=[password])
        print("Created the User : {}".format(user))

    def grantRole(self,user,role,connection):
        command=sql.SQL("GRANT {role} TO {user}").format(role=sql.Identifier(role),user=sql.Identifier(user))
        self.executeCommand(command=command,connection=connection)
        print("Granted the Permissions of {} to {}".format(role,user))

    def createSchema(self,connection,schema,user):
        command=sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION {user}").format(schema=sql.Identifier(schema),user=sql.Identifier(user))
        self.executeCommand(command=command,connection=connection)
        print("Created the Schema : {} under the ownership of {}".format(schema,user))

    def dropSchema(self,connection,schema,user):
        command=sql.SQL("DROP SCHEMA {schema} CASCADE").format(schema=sql.Identifier(schema),user=sql.Identifier(user))
        self.executeCommand(command=command,connection=connection)
        print("Dropped the Schema : {} owned by {}".format(schema,user))

    def createDatabase(self,connection,database,user):
        command=sql.SQL("CREATE DATABASE {database} OWNER {user}").format(database=sql.Identifier(database),user=sql.Identifier(user))
        try:
            with connection.cursor() as cursor:
                connection.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                cursor.execute(command)
        finally:
            connection.commit()
        print("Created the Database : {} under the ownership of {}".format(database,user))

    def createTable(self,connection,schema,table,columns):
        command=sql.SQL("CREATE TABLE IF NOT EXISTS {schema}.{table} ({columns})").format(schema=sql.Identifier(schema),
                                                                                          table=sql.Identifier(table),
                                                                                          columns=sql.SQL(", ").join([sql.Composed(sql.Identifier(columnName)+sql.SQL(" ")+sql.SQL(columnType))  for columnName,columnType in columns.items()]))
        self.executeCommand(command=command,connection=connection)
        print("Created the Table : {} within the schema : {} with columns : {}".format(table,schema,columns))

    def executeCommand(self,command,connection,argument=None):
        print("Executing the command : {}".format(command.as_string(connection)))
        with connection.cursor() as cursor:
            if argument:
                cursor.execute(command,argument)
            else:
                cursor.execute(command)
            connection.commit()
        print("Executed the command : {}".format(command.as_string(connection)))

if __name__ == '__main__':
    database = Database()
    connection = database.connect(database=database.databaseConfig["default_database"],
                                  user=database.databaseConfig["default_username"],
                                  password=database.databaseConfig["default_password"],
                                  host=database.databaseConfig["host"],
                                  port=database.databaseConfig["port"])
    database.createUser(user=database.databaseConfig["application_username"],
                        password=database.databaseConfig["application_password"],
                        connection=connection)
    database.grantRole(user=database.databaseConfig["application_username"],
                       role=database.databaseConfig["application_username"],
                       connection=connection)
    database.createDatabase(database=database.databaseConfig["application_database"],
                            user=database.databaseConfig["application_username"],
                            connection=connection)
    connection = database.connect(database=database.databaseConfig["application_database"],
                                  user=database.databaseConfig["application_username"],
                                  password=database.databaseConfig["application_password"],
                                  host=database.databaseConfig["host"],
                                  port=database.databaseConfig["port"])
    
    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="USERS",
                         columns={"Id":"SERIAL","Name":"VARCHAR(32)","Email":"VARCHAR(320) NOT NULL","Password":"VARCHAR(32) NOT NULL"},
                         connection=connection)
    
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_users PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("USERS"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    
    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="INVESTMENT_TYPES",
                         columns={"Id":"SERIAL","InvestmentType":"VARCHAR(32)"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_investment_types PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENT_TYPES"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                table=sql.Identifier("INVESTMENT_TYPES"),
                                                                                                columns=sql.SQL(", ").join([sql.Identifier("InvestmentType")]),
                                                                                                values=sql.SQL(", ").join([sql.Literal("Stock")]))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                table=sql.Identifier("INVESTMENT_TYPES"),
                                                                                                columns=sql.SQL(", ").join([sql.Identifier("InvestmentType")]),
                                                                                                values=sql.SQL(", ").join([sql.Literal("Mutual Funds")]))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("INSERT INTO {schema}.{table} ({columns}) VALUES ({values})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                table=sql.Identifier("INVESTMENT_TYPES"),
                                                                                                columns=sql.SQL(", ").join([sql.Identifier("InvestmentType")]),
                                                                                                values=sql.SQL(", ").join([sql.Literal("Bank Deposits")]))
    database.executeCommand(command=command,connection=connection)
    
    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="MUTUAL_FUNDS",
                         columns={"Id":"SERIAL","Scheme":"VARCHAR(128) NOT NULL","SIP":"BOOLEAN DEFAULT false","OneTime":"BOOLEAN DEFAULT false","InvestedDate":"TIMESTAMP NOT NULL"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_mutual_funds PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("MUTUAL_FUNDS"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    
    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="STOCKS",
                         columns={"Id":"SERIAL","StockName":"VARCHAR(32) NOT NULL","SIP":"BOOLEAN DEFAULT false","OneTime":"BOOLEAN DEFAULT false","InvestedDate":"TIMESTAMP NOT NULL","VestingDetails":"JSONB"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_stocks PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("STOCKS"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)

    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="SIP",
                         columns={"Id":"SERIAL","MutualFundId":"INTEGER","StockId":"INTEGER","SIPDate":"TIMESTAMP","SIPAmount":"BIGINT DEFAULT 0"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_sip PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("SIP"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_sip_mutualFunds FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("SIP"),
                                                                                                            column=sql.Identifier("MutualFundId"),
                                                                                                            foreignTable=sql.Identifier("MUTUAL_FUNDS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_sip_stocks FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("SIP"),
                                                                                                            column=sql.Identifier("StockId"),
                                                                                                            foreignTable=sql.Identifier("STOCKS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)

    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="INVESTMENT_DETAILS",
                         columns={"Id":"SERIAL","MutualFundId":"INTEGER","StockId":"INTEGER","Amount":"BIGINT DEFAULT 0","Units":"NUMERIC(10,2) DEFAULT 0","SIPID":"INTEGER","InvestedDate":"TIMESTAMP"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_oti PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_oti_mutualFunds FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                            column=sql.Identifier("MutualFundId"),
                                                                                                            foreignTable=sql.Identifier("MUTUAL_FUNDS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_oti_stocks FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                            column=sql.Identifier("StockId"),
                                                                                                            foreignTable=sql.Identifier("STOCKS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_oti_sip FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENT_DETAILS"),
                                                                                                            column=sql.Identifier("SIPID"),
                                                                                                            foreignTable=sql.Identifier("SIP"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    
    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="BANK_DEPOSITS",
                         columns={"Id":"SERIAL","BankName":"VARCHAR(50)","Amount":"BIGINT NOT NULL","InterestRate":"JSONB NOT NULL","InvestedDate":"TIMESTAMP NOT NULL","InterestType":"VARCHAR(10) DEFAULT 'COMPOUND'","MaturityDate":"TIMESTAMP NOT NULL","InterestCalculateDuration":"INTEGER","AutoRenew":"BOOLEAN DEFAULT true"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_BANK_DEPOSITS PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("BANK_DEPOSITS"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT const_interest_type CHECK ({column} in ({possible_values}))").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("BANK_DEPOSITS"),
                                                                                                            column=sql.Identifier("InterestType"),
                                                                                                            possible_values=sql.SQL(', ').join([sql.Literal(value) for value in ['SIMPLE','COMPOUND']]))
    database.executeCommand(command=command,connection=connection)

    database.createTable(schema=database.databaseConfig["application_schema"],
                         table="INVESTMENTS",
                         columns={"Id":"SERIAL","InvestmentType":"INTEGER","UserId":"INTEGER","StockId":"INTEGER","MutualFundId":"INTEGER","BankDepositId":"INTEGER","Active":"BOOLEAN DEFAULT true","WithdrawalDate":"TIMESTAMP"},
                         connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT pk_investments PRIMARY KEY ({column})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                                            column=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_investments_users FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                                            column=sql.Identifier("UserId"),
                                                                                                            foreignTable=sql.Identifier("USERS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_investments_investmentTypes FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                                            column=sql.Identifier("InvestmentType"),
                                                                                                            foreignTable=sql.Identifier("INVESTMENT_TYPES"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_investments_mutualFunds FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                                            column=sql.Identifier("MutualFundId"),
                                                                                                            foreignTable=sql.Identifier("MUTUAL_FUNDS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_investments_stocks FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                                            column=sql.Identifier("StockId"),
                                                                                                            foreignTable=sql.Identifier("STOCKS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    
    database.executeCommand(command=command,connection=connection)
    command = sql.SQL("ALTER TABLE {schema}.{table} ADD CONSTRAINT fk_investments_deposits FOREIGN KEY ({column}) REFERENCES {schema}.{foreignTable}({foreignColumn})").format(schema=sql.Identifier(database.databaseConfig["application_schema"]),
                                                                                                            table=sql.Identifier("INVESTMENTS"),
                                                                                                            column=sql.Identifier("BankDepositId"),
                                                                                                            foreignTable=sql.Identifier("BANK_DEPOSITS"),
                                                                                                            foreignColumn=sql.Identifier("Id"))
    
    database.executeCommand(command=command,connection=connection)
    
    connection.commit()
    connection.close()