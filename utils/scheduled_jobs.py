import logging
from dateutil.relativedelta import relativedelta
from utils.generic_util import UserBankInvestment,UserStockInvestment,UserMutualFundInvestment

class Jobs:
    def __init__(self):
        self.bankDepositUtility=UserBankInvestment()
        self.stockUtility=UserStockInvestment()
        self.mutualFundUtility=UserMutualFundInvestment()

    def renewMaturedBankDeposits(self):
        maturityDate=self.bankDepositUtility.today()
        maturityDate=self.stockUtility.convertStrToDate("2025-07-26")
        maturingBankDeposits=self.bankDepositUtility.getMaturingBankDepositsWithAutoRenew(maturityDate=maturityDate)
        print("Maturing deposits : ",maturingBankDeposits)
        interestTypeConverter={
            1:"MONTHLY",
            3:"QUARTERLY",
            12:"YEARLY",
            None:"NONE"
        }
        for deposit in maturingBankDeposits:
            renewalDate=deposit.get("RenewalDate")
            if renewalDate == None:
                renewalDate=deposit.get("InvestedDate")
            maturityDate=maturityDate+relativedelta(days=(maturityDate-renewalDate).days)
            if deposit.get("InterestType") == "SIMPLE" or (deposit.get("InterestType") == "COMPOUND" and deposit.get("InterestCalculateDuration") is not None):
                isValid,interestRateJson=self.bankDepositUtility.prepareInterestJson(interestRates=float(deposit.get("InterestRate").get("0").get("interestRate")),
                                                startDate=deposit.get("InvestedDate"),
                                                maturityDate=maturityDate,
                                                interestCalculateType=interestTypeConverter.get(deposit.get("InterestCalculateDuration")),
                                                interestType=deposit.get("InterestType"))
                if isValid:
                    self.bankDepositUtility.updateBankDeposit(bankDepositId=deposit.get("Id"),
                                                              columns=["InterestRate","RenewalDate","MaturityDate"],
                                                              values=[interestRateJson,renewalDate,maturityDate])
            else:
                self.bankDepositUtility.prepareInterestJson(interestRates=deposit.get("InterestRate"),
                                                startDate=deposit.get("InvestedDate"),
                                                maturityDate=maturityDate,
                                                interestCalculateType=interestTypeConverter.get(deposit.get("InterestCalculateDuration")),
                                                interestType="COMPOUND")
                
    def addNewSip(self):
        sipDate=self.stockUtility.today()
        # sipDate=self.stockUtility.convertStrToDate("2025-06-08")
        sips=self.stockUtility.getSIPToday(sipDate)

        print("SIPS: ",sips)

        for sip in sips:
            sipAmount=sip.get("SIPAmount")
            nextSipDate=self.stockUtility.getNextSipDate(sipDate=sipDate.day)
            print("Next sip date is ",nextSipDate)
            if sip.get("StockId") is not None:
                stockName=self.stockUtility.getStockName(stockId=int(sip.get("StockId")))
                valid,stockValue=self.stockUtility.searchStockInfo(stockName=stockName.get("StockName"),period="daily")
                sipUnit=round(sipAmount/self.stockUtility.getStockAmountOnDate(stockInfo=stockValue,
                                                               date=sipDate),2)
            else:
                mutualFundName=self.mutualFundUtility.getMutualFundName(mutualFundId=sip.get("MutualFundId"))
                schemeId=mutualFundName.get("Scheme").split(".")[1]
                isValid,mutualFundValue=self.mutualFundUtility.searchMutualFund(schemeId=schemeId)
                print("Searched the mutualFund {}. Values: {}".format(mutualFundName,mutualFundValue))
                sipUnit=round(sipAmount/self.mutualFundUtility.getMutualFundNavOnDate(mutualFundData=mutualFundValue,
                                                                      date=sipDate),2)
            self.stockUtility.addNewSip(sipAmount=sip.get("SIPAmount"),
                                                sipDate=sipDate,
                                                stockId=sip.get("StockId"),
                                                mutualFundId=sip.get("MutualFundId"),
                                                sipId=sip.get("Id"),
                                                sipUnits=sipUnit)
            self.stockUtility.updateSIP(sipId=sip.get("Id"),sipDate=nextSipDate)
