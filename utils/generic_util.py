from flask_jwt_extended import decode_token,verify_jwt_in_request,get_jwt_identity,get_jwt,create_access_token,create_refresh_token,jwt_required
from flask import request
import json
import random
import math
from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils.database.investment_utility import BankDeposits,Stock,MutualFund
from utils.database.common_utility import Database
from utils.request_util import APIRequest

class UserSession:
    def __init__(self):
        pass

    def formatUserId(self,userId):
        userId=hex(userId).replace("0x","").zfill(16)
        l,i=[],0
        while i<len(userId):
            l.append(userId[i:min(i+4,len(userId))])
            i+=4
        return "-".join(l)

    def deformatUserId(self,userId):
        return int(userId.replace("-",""),16) if userId else None

    def checkTokenExpiry(self):
        def checkRefreshTokenExpiry(refresh_token):
            try:
                print("Refresh Token: ",refresh_token)
                if refresh_token:
                    verify_jwt_in_request(optional=True,refresh=True)
                    identity = get_jwt_identity()
                    print("Refresh Identity1: ",identity)
                    if identity is not None:
                        return False,refresh_token
                    else:
                        return False,False
                else:
                    return False,None
            except Exception as e:
                return False,False
        
        try:
            access_token = request.cookies.get('access_token')
            refresh_token = request.cookies.get('refresh_token')
            if access_token is None and refresh_token is None:
                return None,None
            
            verify_jwt_in_request(optional=True,refresh=False)
            identity = get_jwt_identity()
            print("Access Identity: ",identity)
            if identity:
                print("Access Token: ",decode_token(access_token))
                print("Refresh Token: ",decode_token(refresh_token))
                return access_token,None
            else:
                return checkRefreshTokenExpiry(refresh_token)
        except Exception as e:
            return checkRefreshTokenExpiry(refresh_token)
        
    def getUserId(self,token):
        return int(self.deformatUserId(self.getClaimFromToken(token,"userID")))

    def getUserName(self,token):
        return self.getClaimFromToken(token,"userName")
    
    def createAccessToken(self,userName,userId,identity=None):
        if not identity:
            print("username is {}".format(userName))
            identity=userName
        return create_access_token(identity=userName,additional_claims={"userID":self.formatUserId(userId=userId),"userName":userName})
    
    def createRefreshToken(self,userName,userId,identity=None):
        if not identity:
            identity=userName
        return create_refresh_token(identity=identity,additional_claims={"userID":self.formatUserId(userId=userId),"userName":userName})
        
    def getClaimFromToken(self,token,key):
        print("token: ",token)
        token=token.encode('utf-8')
        print("decoded ",decode_token(token))
        print("key ",decode_token(token).get(key))
        return decode_token(token).get(key)

class Utility:
    def __init__(self):
        super().__init__()
        with open('utils/config.json') as f:
            config=json.load(f)
            self.currencyExchangeConfig = config["personal_wealth_tracker"]["currency_exchange"]

    def convertToInt(self,array):
        return list(map(lambda x:int(x),array))
    
    def convertStrToDate(self,date,format="%Y-%m-%d"):
        if isinstance(date,str):
            return datetime.strptime(date,format)
        return date
    
    def convertDateToStr(self,date,format="%Y-%m-%d"):
        if isinstance(date,datetime):
            return datetime.strftime(date,format)
        return date
    
    def formatDeposit(self,investment):
        investment=dict(investment)
        investment["MaturityDate"]=self.convertDateToStr(investment["MaturityDate"])
        investment["InvestedDate"]=self.convertDateToStr(investment["InvestedDate"])
        return investment
    
    def combineDepositsFromInvestments(self,deposits,bankInvestment):
        if bankInvestment.get("investmentId") in deposits:
            deposits[bankInvestment.get("investmentId")]["Amount"]+=bankInvestment["Amount"]
        else:
            deposits[bankInvestment.get("investmentId")]=bankInvestment
        return deposits
    
    def formatDeposits(self,investments):
        deposits={}
        for row in range(len(investments)):
            investments[row]=self.formatDeposit(investments[row])
            deposits=self.combineDepositsFromInvestments(deposits=deposits,bankInvestment=investments[row])
        
        return list(deposits.values())
    
    def getExchangeRate(self,amount,targetConversion="INR",stockExchange=""):
        stockExchange_exchangeRate_mapping={
            "":"USD",
            "LON":"GBP",
            "BSE":"INR",
            "LON":"EUR",
            "TRT":"CAD",
            "TRV":"CAD",
            "SHH":"CNY",
            "SHZ":"CNY"
        }
        url="{}/{}/pair/{}/{}/{}".format(self.currencyExchangeConfig.get("base_url"),self.currencyExchangeConfig.get("api_key"),
                                         stockExchange_exchangeRate_mapping.get(stockExchange),targetConversion,amount)
        method="GET"
        try:
            session=APIRequest()
            response=session.make_request(method=method,url=url)
            if response.status_code == 200:
                return response.json().get("conversion_result")
            else:
                return None
        except Exception as e:
            print("Failed to get currency exchange {}".format(e))
            return None 

    def isValidVestingJson(self,stockUnits,vestingUnits):
        vestingUnits=list(map(int,vestingUnits))
        return sum(vestingUnits) == stockUnits 
    
    def prepareVestingJson(self,vestingDates,vestingUnits,stockUnits):
        vestingJson={date:int(unit) for date,unit in zip(vestingDates,vestingUnits)}
        if self.isValidVestingJson(stockUnits=stockUnits,vestingUnits=vestingUnits):
            return True,json.dumps(vestingJson,indent=4)
        return False,None
    
    def getCurrencySymbol(self,stockExchange=""):
        stockExchange_exchangeRate_mapping={
            "":"$",
            "SHH":"¥",
            "SHZ":"¥",
            "DEX":"€",
            "LON":"£",
            "BSE":"₹",
            "TRT":"C$",
            "TRV":"C$"
        }
        return stockExchange_exchangeRate_mapping.get(stockExchange)
    
    def formatInvestments(self,bankInvestment,stockInvestment,mutualFundInvestment):
        combinedInvestment=[["STOCKS",0],
                            ["MUTUAL FUNDS",0],
                            ["BANK DEPOSITS",0]]
        for investment in bankInvestment:
            combinedInvestment[2][1]+=investment[1]
        for investment in stockInvestment:
            combinedInvestment[0][1]+=investment[1]
        for investment in mutualFundInvestment:
            combinedInvestment[1][1]+=investment[1]
        
        return combinedInvestment
    
    def isEmptyStringList(self,array):
        for i in array:
            if i != '':
                return False
        return True
    
class UserBankInvestment(Utility):
    def __init__(self):
        self.interestTypeConverter={
            "MONTHLY":1,
            "QUARTERLY":3,
            "YEARLY":12,
            "NONE":None
        }
        self.bankInvestment=BankDeposits()
    
    def isValidInterestDurationRange(self,rateOfInterest):
        interestRates=list(rateOfInterest.values())
        for i in range(len(interestRates)-1):
            # print(interestRates[i+1]["startDate"],interestRates[i]["endDate"],(interestRates[i+1]["startDate"]-interestRates[i]["endDate"]).days)
            if (interestRates[i+1]["startDate"]-interestRates[i]["endDate"]).days!=1:
                return False
            interestRates[i]["startDate"]=self.convertDateToStr(interestRates[i]["startDate"])
            interestRates[i]["endDate"]=self.convertDateToStr(interestRates[i]["endDate"])
        interestRates[-1]["startDate"]=self.convertDateToStr(interestRates[-1]["startDate"])
        interestRates[-1]["endDate"]=self.convertDateToStr(interestRates[-1]["endDate"])
        return True

    def isValidMaturityDate(self,maturityDate,startDate):
        maturityDate=self.convertToInt(maturityDate)
        startDate=self.convertStrToDate(startDate)
        maturityDate=startDate+relativedelta(days=maturityDate[0],months=maturityDate[1],years=maturityDate[2])
        if maturityDate > startDate:
            return True,maturityDate
        return False,maturityDate

    def prepareInterestJson(self,interestRates,startDate,startDays=None,startMonths=None,startYears=None,endDays=None,endMonths=None,endYears=None,maturityDate=None,interestCalculateType=None,interestType='COMPOUND'):
        rateOfInterest = {}
        startDate=self.convertStrToDate(startDate)
        if interestType=="COMPOUND":
            if interestCalculateType == "None":
                startDays=self.convertToInt(startDays)
                startMonths=self.convertToInt(startMonths)
                startYears=self.convertToInt(startYears)
                endDays=self.convertToInt(endDays)
                endMonths=self.convertToInt(endMonths)
                endYears=self.convertToInt(endYears)

                for i in range(len(interestRates)):
                    interestStartDate=startDate+relativedelta(days=startDays[i],months=startMonths[i],years=startYears[i])
                    if interestStartDate<maturityDate:
                        rateOfInterest[i]={
                            "startDate":interestStartDate,
                            "endDate":min(maturityDate,startDate+relativedelta(days=endDays[i],months=endMonths[i],years=endYears[i])),
                            "interestRate":float(interestRates[i])
                        }
                return self.isValidInterestDurationRange(rateOfInterest),json.dumps(rateOfInterest,indent=4)
        
        i=0
        while startDate<maturityDate:
            print("interestCalculateType",interestCalculateType)
            endDate=startDate+relativedelta(months=self.interestTypeConverter.get(interestCalculateType))
            rateOfInterest[i]={
                "startDate":startDate,
                "endDate":min(endDate,maturityDate),
                "interestRate":float(interestRates)
            }
            i+=1
            startDate=endDate+relativedelta(days=1)        
        return self.isValidInterestDurationRange(rateOfInterest),json.dumps(rateOfInterest,indent=4)
    
    def addNewBankDeposit(self,userId,bank,amount,interest,investmentDate,maturityDate,interestCalculateType=None,interestType='COMPOUND'):
        self.bankInvestment.addNewDeposit(userId=userId,bank=bank,amount=amount,interest=interest,investmentDate=investmentDate,
                                  interestType=interestType,maturityDate=maturityDate,interestDuration=self.interestTypeConverter.get(interestCalculateType))
        
    def getAllBankInvestments(self):
        return self.bankInvestment.getAllBankDeposits()
            
    def getCurrentAmount(self,deposit):
        if deposit.get("Active"):
            currentDay=datetime.today()
        else:
            currentDay=self.convertStrToDate(deposit.get("WithdrawalDate"))
        currentAmount=float(deposit.get("Amount"))
        for interestRate in deposit.get("InterestRate").values():
            if self.convertStrToDate(interestRate.get('endDate'))<=currentDay:
                period=(self.convertStrToDate(interestRate.get('endDate'))-self.convertStrToDate(interestRate.get('startDate'))).days
                if deposit.get('InterestType')=='SIMPLE':
                    currentAmount+=(float(deposit.get('Amount'))*interestRate.get('interestRate')*period/36500)
                if deposit.get('InterestType')=='COMPOUND':
                    currentAmount+=(currentAmount*interestRate.get('interestRate')*period/36500)
        return round(currentAmount,2)

    def getUserCombinedBankDepositAmount(self,userId):
        bankDeposits=self.bankInvestment.getUserBankInvestments(userId=userId)
        combinedDeposit={}
        for deposit in bankDeposits:
            combinedDeposit[deposit["BankName"]]=combinedDeposit.get(deposit["BankName"],0)+self.getCurrentAmount(deposit=deposit)

        return self.formatDeposits(bankDeposits),list(map(lambda deposit:[deposit,combinedDeposit[deposit]], combinedDeposit))

    def getBankDepositInfomation(self,bankInvestmentId):
        bankDeposits=self.formatDeposits(self.bankInvestment.getBankDeposit(bankInvestmentId=bankInvestmentId))
        deposits={}
        for deposit in bankDeposits:
            deposits=self.combineDepositsFromInvestments(deposits=deposits,bankInvestment=deposit)
        deposits[bankInvestmentId]["CurrentAmount"]=self.getCurrentAmount(deposit=deposits[bankInvestmentId])
        print("deposits: ",deposits)
        # return bankDeposits,deposits[bankInvestmentId]
        return deposits[bankInvestmentId]
    
class UserStockInvestment(Utility):
    def __init__(self):
        super().__init__()
        self.stockInvestment=Stock()
        with open('utils/config.json') as f:
            config=json.load(f)
            self.stockConfig = config["personal_wealth_tracker"]["stocks"]

    def searchStockInfo(self,stockName,period="yearly",outputSize="compact"):
        url=self.stockConfig.get("base_url")
        period_map = {
            "intraday":{
                "function":"TIME_SERIES_INTRADAY",
                "outputsize":outputSize,
                "interval":"5min"
            },
            "daily":{
                "function":"TIME_SERIES_DAILY",
                "outputsize":outputSize
            },
            "monthly":{
                "function":"TIME_SERIES_MONTHLY"
            },
            "yearly":{
                "function":"TIME_SERIES_MONTHLY"
            }

        }
        query_params=period_map.get(period)
        query_params.update({"symbol":stockName,
                             "apikey":self.stockConfig.get("api_key")
                            })

        method="GET"
        try:
            session=APIRequest()
            response=session.make_request(method=method,query_params=query_params,url=url)
            if response.status_code == 200:
                stockInfo=response.json()
                # if "Meta Data" not in stockInfo:
                #     return False,None
                return True,stockInfo
            return False,None
        except:
            return False,None
        
    def addStockInvestment(self,userId,stockName,investedDate,sip=False,oneTime=False,vestingDetails=None,
                              sipAmount=None,units=None,sipDate=None,
                              oneTimeInvestmentAmount=None):
        self.stockInvestment.addNewStockInvestment(userId=userId,stockName=stockName,investedDate=investedDate,
                                                   sip=sip,sipAmount=sipAmount,sipDate=sipDate,units=units,
                                                   oneTime=oneTime,vestingDetails=vestingDetails,oneTimeInvestmentAmount=oneTimeInvestmentAmount)

    def getStockAmountOnDate(self,stockInfo,date):
        date=self.convertStrToDate(date=date)
        try:
            for key in stockInfo.get("Time Series (Daily)"):
                if self.convertStrToDate(key)<=date:
                    return float(stockInfo.get("Time Series (Daily)").get(key).get("4. close"))
        except Exception as e:
            print("getting amount on in except {}",date,e)
            return float(random.randint(1,200))
            
    def formatStock(self,stockData,period="yearly"):
        period_map={
            "daily":"Time Series (Daily)",
            "weekly":"Weekly Time Series",
            "monthly":"Monthly Time Series",
            "yearly":"Monthly Time Series"
        }
        openPrice,closePrice,volume,date=[],[],[],[]
        try:
            print("formatting in try")
            entryCount = 0
            for key,value in stockData.get(period_map.get(period)).items():
                if period == "monthly" and entryCount == 60:
                    break
                if period == "yearly" and entryCount!=0:
                    if self.convertStrToDate(key).month not in [3,6,9,12]:
                        continue
                date.insert(0,key)
                openPrice.insert(0,float(value.get("1. open",0)))
                closePrice.insert(0,float(value.get("4. close",0)))
                volume.insert(0,int(value.get("5. volume")))
                entryCount+=1
        except Exception as e:
            print("formatting in except",e)
            for i in range(6500):
                if i%100==0:
                    date.append(datetime.today()-relativedelta(days=i))
                    openPrice.append(random.randint(1,200))
                    closePrice.append(random.randint(1,200))
                    volume.append(random.randint(100000,1000000))

        maxVolume = 10**math.floor(math.log10(max(volume)))
        maxRange = 10**math.floor(math.log10(max(max(openPrice),max(closePrice))))
        dividingFactor = maxVolume // maxRange
        volume = list(map(lambda x:x/dividingFactor,volume))
        volumeLabel = "Volume ( X{} )".format(dividingFactor)
        return openPrice,closePrice,volume,date,volumeLabel
    
    def combineStockFromInvestments(self,stockInfo):
        combinedStockInfo={"Amount":0,
                           "Units":0,
                           "investmentInfo":defaultdict(lambda:[0,0,0]),
                           "investmentValue":{},
                           "vestingInfo":None,
                           "Active":True,
                           "Id":None}
        stockName = stockInfo[0].get("StockName")
        valid,stockValue=self.searchStockInfo(stockName=stockName,period="daily",outputSize="full")
        for stock in stockInfo:
            combinedStockInfo["Amount"]+=float(stock.get("Amount",0))
            combinedStockInfo["Amount"]+=float(stock.get("SIPAmount",0))
            combinedStockInfo["Units"]+=float(stock.get("Units",0))
            
            if stock.get("VestingDetails") is not None:
                if combinedStockInfo["vestingInfo"] is None:
                    combinedStockInfo["vestingInfo"]={self.convertDateToStr(stock["InvestedDate"]):0}
                dates = sorted(stock["VestingDetails"].keys())
                if len(dates)>1:
                    for i in range(1,len(dates)):
                        stock["VestingDetails"][dates[i]]+=stock["VestingDetails"][dates[i-1]]
                for vestingDate in stock["VestingDetails"].keys():
                    combinedStockInfo["vestingInfo"][vestingDate]=combinedStockInfo["vestingInfo"].get(vestingDate,0)+stock["VestingDetails"][vestingDate]

            stock["InvestedDate"]=self.convertDateToStr(stock["InvestedDate"])
            combinedStockInfo["investmentInfo"][stock["InvestedDate"]][0]+=float(stock["Units"])
            combinedStockInfo["investmentInfo"][stock["InvestedDate"]][1]+=float(stock["Amount"])
            combinedStockInfo["investmentInfo"][stock["InvestedDate"]][2]+=(float(stock["Units"])*self.getStockAmountOnDate(stockInfo=stockValue,
                                                                                                                          date=stock["InvestedDate"]))

            combinedStockInfo["investmentInfo"]=dict(combinedStockInfo["investmentInfo"])

        combinedStockInfo["StockName"]=stockName
        combinedStockInfo["Id"]=stock.get("Id")
        combinedStockInfo["currentAmount"]=round(self.getStockAmountOnDate(stockInfo=stockValue,
                                                                           date=datetime.today())*combinedStockInfo.get("Units"),2)
        combinedStockInfo["Active"]=stock.get("Active",True)
        combinedStockInfo["INRAmount"]=round(self.getExchangeRate(combinedStockInfo["currentAmount"],
                                                            targetConversion="INR",
                                                            stockExchange=stockName.split(".")[1] if "." in stockName else ""),2)
        return combinedStockInfo
    
    def getUserStocks(self,userId):
        individualAmount={}
        stockInfo =  list(map(lambda x: dict(x),self.stockInvestment.getUserStocks(userId=userId)))
        for stock in stockInfo:
            stockName = stock.get("StockName")
            stockExchange = stockName.split(".")[1] if "." in stockName else ""
            valid,stockValue=self.searchStockInfo(stockName=stockName,period="daily")
            stockAmount=self.getExchangeRate(amount=float(stock.get("Units"))*self.getStockAmountOnDate(stockInfo=stockValue,
                                                                                                        date=datetime.today()),
                                             targetConversion="INR",
                                             stockExchange=stockExchange)
            stock["Amount"]="₹ {}".format(stockAmount)
            individualAmount[stockName]=individualAmount.get(stockName,0)+stockAmount
        return stockInfo,list(map(lambda stock:[stock,individualAmount[stock]],individualAmount))
    
    def getStockInformation(self,stockId):
        stockInfo=self.stockInvestment.getStock(stockInvestmentId=stockId)
        print("stockInfo: ",stockInfo)
        # return list(map(lambda x: dict(x),stockInfo)),self.combineStockFromInvestments(stockInfo=stockInfo)
        return self.combineStockFromInvestments(stockInfo=stockInfo)
    
    def updateStock(self,investmentId,vestingDetails):
        self.stockInvestment.updateStock(columns=["VestingDetails"],
                                         values=vestingDetails,
                                         investmentId=investmentId)
        
    def getStockUnits(self,investmentId):
        stockUnits= self.stockInvestment.getStockUnits(investmentId=investmentId)
        return int(stockUnits.get("Units"))

class UserMutualFundInvestment(Utility):
    def __init__(self):
        super().__init__()
        self.mutualFund=MutualFund()
        with open('utils/config.json') as f:
            config=json.load(f)
            self.mutualFundConfig = config["personal_wealth_tracker"]["mutual_funds"]

    def searchMutualFund(self,schemeId):
        url="{}/{}".format(self.mutualFundConfig["base_url"],schemeId)
        method="GET"
        try:
            session=APIRequest()
            response=session.make_request(url=url,method=method)
            if response.status_code==200:
                mutualFundInfo=response.json()
                if len(mutualFundInfo)==0:
                    return False,None
                else:
                    return True,mutualFundInfo
        except Exception as e:
            print("Failed to get the Mutual Fund Info. {}".format(e))
            return False,None

    def addMutualFundInvestment(self,userId,schemeName,investedDate,sip=False,oneTime=False,
                                sipAmount=None,sipDate=None,
                                oneTimeInvestmentAmount=None,units=None):
        self.mutualFund.addNewMutualFundInvestment(userId=userId,scheme=schemeName,investedDate=investedDate,
                                                   sip=sip,oneTime=oneTime,sipAmount=sipAmount,sipDate=sipDate,
                                                   units=units,oneTimeInvestmentAmount=oneTimeInvestmentAmount)

    def getMutualFundNavOnDate(self,mutualFundData,date):
        date=self.convertStrToDate(date=date)
        for nav in mutualFundData["data"]:
            if self.convertStrToDate(date=nav["date"],format="%d-%m-%Y")<=date:
                return round(float(nav["nav"]),2)
        return 0
    
    def formatMutualFund(self,mutualFundData,period="yearly"):
        print("mutualFundData: ",mutualFundData)
        data={}
        entryCount=0
        for nav in mutualFundData["data"]:
            date=self.convertStrToDate(nav["date"],format="%d-%m-%Y")
            if entryCount !=0:
                if period=='daily' and entryCount>90:
                    break
                elif period=='monthly':
                    if entryCount>60:
                        break
                    elif date.day!=1:
                        continue
                elif period=='yearly':
                    if entryCount>60:
                        break
                    elif date.day!=1 or date.month not in [1,4,7,10]:
                        continue
                elif period=="latest":
                    if entryCount>=1:
                        break
            data[self.convertDateToStr(date=date)]=round(float(nav["nav"]),2)
            entryCount+=1
        return {mutualFundData["meta"]["scheme_name"].upper():data}
    
    def combineMutualFundsFromInvestmentDetails(self,mutualFunds):
        combinedMutualFund={"Amount":0,
                            "Units":0,
                            "Scheme":None,
                            "SchemeId":None,
                            "Active":True,
                            "investmentInfo":defaultdict(lambda:[0,0]),
                            "currentValue":{"Units":[0],"Amount":[0]},
                            "Id":None,
                            "SIP":True}
        # for mutualFund in mutualFunds:
        #     investedDate=self.convertDateToStr(mutualFund["InvestedDate"])         
            # combinedMutualFund["Amount"]+=float(mutualFund["Amount"])
            # combinedMutualFund["Units"]+=float(mutualFund["Units"])
            # combinedMutualFund["investmentInfo"][investedDate][0]+=float(mutualFund["Units"])
            # combinedMutualFund["investmentInfo"][investedDate][1]+=float(mutualFund["Amount"])
            # combinedMutualFund["investmentInfo"][investedDate][2]+=float(mutualFund["Units"])*self.getMutualFundNavOnDate(mutualFundData=mutualFundInfo,
            #                                                                                                               date=investedDate)

        # combinedMutualFund["investmentInfo"]=dict(combinedMutualFund["investmentInfo"])
        
        today=self.convertStrToDate(self.convertDateToStr(date=datetime.today()))
        # combinedMutualFund["investmentInfo"][self.convertDateToStr(today)]=[combinedMutualFund["investmentInfo"][investedDate][0],
        #                                                                     combinedMutualFund["investmentInfo"][investedDate][1]]
        combinedMutualFund["Scheme"],combinedMutualFund["SchemeId"]=mutualFunds[0]["Scheme"].split(".")
        isValid,mutualFundInfo=self.searchMutualFund(schemeId=combinedMutualFund["SchemeId"])
        currentMutualFundData= self.formatMutualFund(mutualFundData=mutualFundInfo,period="latest")
        for i,mutualFund in enumerate(sorted(mutualFunds,key=lambda fund:fund["InvestedDate"])):
            combinedMutualFund["Amount"]+=float(mutualFund["Amount"])
            combinedMutualFund["Units"]+=float(mutualFund["Units"])
            if float(mutualFund["Amount"])!=0:
                investedDate=self.convertDateToStr(mutualFund["InvestedDate"])
                combinedMutualFund["investmentInfo"][investedDate][0]+=float(mutualFund["Units"])
                combinedMutualFund["investmentInfo"][investedDate][1]+=float(mutualFund["Amount"])
                combinedMutualFund["currentValue"]["Units"].append(combinedMutualFund["currentValue"]["Units"][i]+combinedMutualFund["investmentInfo"][investedDate][0])
                combinedMutualFund["currentValue"]["Amount"].append(combinedMutualFund["currentValue"]["Units"][i+1]*self.getMutualFundNavOnDate(mutualFundData=mutualFundInfo,
                                                                                                                                             date=investedDate))
        combinedMutualFund["currentValue"]["Units"].append(combinedMutualFund["currentValue"]["Units"][-1])
        combinedMutualFund["currentValue"]["Amount"].append(combinedMutualFund["currentValue"]["Units"][-1]*self.getMutualFundNavOnDate(mutualFundData=mutualFundInfo,
                                                                                                                                         date=today))
        combinedMutualFund["investmentInfo"][self.convertDateToStr(today)]=[combinedMutualFund["investmentInfo"][self.convertDateToStr(today)][0],
                                                                            combinedMutualFund["investmentInfo"][self.convertDateToStr(today)][1]]
        combinedMutualFund["currentValue"]["Units"].pop(0)
        combinedMutualFund["currentValue"]["Amount"].pop(0)
        
        combinedMutualFund["investmentInfo"]=dict(combinedMutualFund["investmentInfo"])
        combinedMutualFund["Active"]=mutualFund["Active"]
        combinedMutualFund["Id"]=mutualFund["Id"]
        combinedMutualFund["SIP"]=mutualFund["SIP"]
        currentMutualFundNav=float(list(currentMutualFundData[combinedMutualFund["Scheme"].upper()].values())[0])
        combinedMutualFund["currentAmount"]=round(combinedMutualFund["Units"]*currentMutualFundNav,2)
        return combinedMutualFund
        
    def getUserMutualFunds(self,userId):
        mutualFunds= self.mutualFund.getUserMutualFunds(userId=userId)
        print("mutualFunds: ",mutualFunds)
        combinedMutualFund={}
        for mutualFund in mutualFunds:
            schemeName,schemeId=mutualFund["Scheme"].split(".")
            mutualFund["Scheme"]=schemeName
            combinedMutualFund[schemeName]=float(combinedMutualFund.get(schemeName,0)+mutualFund["Amount"])
        return mutualFunds,list(map(lambda mutualFund:[mutualFund,combinedMutualFund[mutualFund]],combinedMutualFund))

    def getMutualFund(self,investmentId):
        mutualFundInfo = list(map(lambda mutualFund:dict(mutualFund),self.mutualFund.getMutualFund(investmentId=investmentId)))
        print("mutualFundInfo: ",mutualFundInfo)
        return self.combineMutualFundsFromInvestmentDetails(mutualFunds=mutualFundInfo)
    
class UserInvestments(Utility):
    def __init__(self):
        super().__init__()
        self.bankInvestment=UserBankInvestment()
        self.stockInvestment=UserStockInvestment()
        self.mutualFundInvestment=UserMutualFundInvestment()
        self.investments=Database()

    def getUserCombinedInvestments(self,userId):
        bankInvestments=self.bankInvestment.getUserCombinedBankDepositAmount(userId=userId)[1]
        stockInvestments=self.stockInvestment.getUserStocks(userId=userId)[1]
        mutualFundInvestments=self.mutualFundInvestment.getUserMutualFunds(userId=userId)[1]
        return self.formatInvestments(bankInvestment=bankInvestments,
                                      stockInvestment=stockInvestments,
                                      mutualFundInvestment=mutualFundInvestments)
    
    def markInvestmentAsInactive(self,investmentId):
        self.investments.markInvestmentInactive(investmentId=investmentId,withdrawalDate=datetime.today())

    def updateSIP(self,updateInfo,investmentId,investmentType):
        investmentTypes={
            "stocks":1,
            "mutualfunds":2
        }
        investmentTypeDB=self.investments.getInvestmentType(investmentId=investmentId)
        if int(investmentTypeDB)==investmentTypes.get(investmentType) and investmentTypes[investmentType]==1:
            self.investments.updateSIP(columns=list(updateInfo.keys()),
                                       values=list(updateInfo.values()),
                                       investmentId=investmentId,
                                       investmentTypeId="StockId")
        elif int(investmentTypeDB)==investmentTypes.get(investmentType) and investmentTypes[investmentType]==2:
            self.investments.updateSIP(columns=list(updateInfo.keys()),
                                       values=list(updateInfo.values()),
                                       investmentId=investmentId,
                                       investmentTypeId="MutualFundId")