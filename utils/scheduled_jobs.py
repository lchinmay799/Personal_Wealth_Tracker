import logging
import json
from dateutil.relativedelta import relativedelta
from utils.generic_util import UserBankInvestment,UserStockInvestment,UserMutualFundInvestment

class Jobs:
    def __init__(self):
        self.bankDepositUtility=UserBankInvestment()
        self.stockUtility=UserStockInvestment()
        self.mutualFundUtility=UserMutualFundInvestment()

    def renewMaturedBankDeposits(self):
        maturityDate=self.bankDepositUtility.today()
        maturityDate=self.bankDepositUtility.convertStrToDate("2025-12-27")
        maturingBankDeposits=self.bankDepositUtility.getMaturingBankDepositsWithAutoRenew(maturityDate=maturityDate)
        if maturityDate.day in [28,29,30]:
            nextToMaturityDay=maturityDate+relativedelta(days=1)
            if nextToMaturityDay.month!=maturityDate.month:
                while nextToMaturityDay.day%32!=0:
                    maturingBankDeposits.extend(self.bankDepositUtility.getMaturingBankDepositsWithAutoRenew(maturityDate=nextToMaturityDay))
                    nextToMaturityDay=nextToMaturityDay+relativedelta(days=1)
        print("Maturing deposits : ",maturingBankDeposits)
        interestTypeConverter={
            1:"MONTHLY",
            3:"QUARTERLY",
            12:"YEARLY",
            None:"NONE"
        }
        for deposit in maturingBankDeposits:
            renewalDate=deposit.get("RenewalDate")
            # uncomment below line if you want to renew old investments
            # maturityDate=deposit.get("MaturityDate")
            if renewalDate is None:
                renewalDate=deposit.get("InvestedDate")
            if deposit.get("InterestType") == "SIMPLE" or (deposit.get("InterestType") == "COMPOUND" and deposit.get("InterestCalculateDuration") is not None):
                renewalDate,maturityDate=maturityDate,maturityDate+relativedelta(days=(maturityDate-renewalDate).days)
                isValid,interestRateJson=self.bankDepositUtility.prepareInterestJson(interestRates=float(deposit.get("InterestRate").get("0").get("interestRate")),
                                                startDate=deposit.get("InvestedDate"),
                                                maturityDate=maturityDate,
                                                interestCalculateType=interestTypeConverter.get(deposit.get("InterestCalculateDuration")),
                                                interestType=deposit.get("InterestType"))
            else:
                rateOfInterest=[]
                interestRateJson=deposit.get("InterestRate")
                for i,interestRate in interestRateJson.items():
                    interestRate["startDate"]=self.bankDepositUtility.convertStrToDate(interestRate.get("startDate"))
                    interestRate["endDate"]=self.bankDepositUtility.convertStrToDate(interestRate.get("endDate"))
                    startDate=interestRate.get("startDate")
                    if startDate>=renewalDate:
                        endDate=interestRate.get("endDate")
                        rateOfInterest.append({
                            "startDate":startDate+relativedelta(days=(maturityDate-renewalDate).days+1),
                            "endDate":endDate+relativedelta(days=(maturityDate-renewalDate).days+1),
                            "interestRate":interestRate.get("interestRate")
                        })
                i=int(i)
                for interestRate in rateOfInterest:
                    i+=1
                    interestRateJson[i]=interestRate

                renewalDate,maturityDate=maturityDate,maturityDate+relativedelta(days=(maturityDate-renewalDate).days)
                isValid=self.bankDepositUtility.isValidInterestDurationRange(rateOfInterest=interestRateJson)
                interestRateJson=json.dumps(interestRateJson,indent=4)

            if isValid:
                self.bankDepositUtility.updateBankDeposit(bankDepositId=deposit.get("Id"),
                                                        columns=["InterestRate","RenewalDate","MaturityDate"],
                                                        values=[interestRateJson,renewalDate,maturityDate])
                
    def addNewSip(self):
        sipDate=self.stockUtility.today()
        # sipDate=self.stockUtility.convertStrToDate("2025-06-08")
        sips=self.stockUtility.getSIPToday(sipDate)

        print("SIPS: ",sips)

        for sip in sips:
            sipAmount=sip.get("SIPAmount")
            nextSipDate=self.stockUtility.getNextSipDate(sipDate=sipDate.day)
            if sip.get("StockId") is not None:
                stockName=self.stockUtility.getStockName(stockId=int(sip.get("StockId")))
                isValid,stockValue=self.stockUtility.searchStockInfo(stockName=stockName.get("StockName"),period="daily")
                sipUnit=round(sipAmount/self.stockUtility.getStockAmountOnDate(stockInfo=stockValue,
                                                               date=sipDate),2)
            else:
                mutualFundName=self.mutualFundUtility.getMutualFundName(mutualFundId=sip.get("MutualFundId"))
                schemeId=mutualFundName.get("Scheme").split(".")[1]
                isValid,mutualFundValue=self.mutualFundUtility.searchMutualFund(schemeId=schemeId)
                sipUnit=round(sipAmount/self.mutualFundUtility.getMutualFundNavOnDate(mutualFundData=mutualFundValue,
                                                                      date=sipDate),2)
            if isValid:
                self.stockUtility.addNewSip(sipAmount=sip.get("SIPAmount"),
                                                sipDate=sipDate,
                                                stockId=sip.get("StockId"),
                                                mutualFundId=sip.get("MutualFundId"),
                                                sipId=sip.get("Id"),
                                                sipUnits=sipUnit)
                self.stockUtility.updateSIP(sipId=sip.get("Id"),sipDate=nextSipDate)
