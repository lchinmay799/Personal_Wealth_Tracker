import logging
import json
from dateutil.relativedelta import relativedelta
from utils.generic_util import UserBankInvestment,UserStockInvestment,UserMutualFundInvestment
from utils.logger import logger

class Jobs:
    def __init__(self):
        self.bankDepositUtility=UserBankInvestment()
        self.stockUtility=UserStockInvestment()
        self.mutualFundUtility=UserMutualFundInvestment()
        self.logger=logger()
        self.logger=self.logger.getLogger()

    def renewMaturedBankDeposits(self):
        maturityDate=self.bankDepositUtility.today()
        maturingBankDeposits=self.bankDepositUtility.getMaturingBankDepositsWithAutoRenew(maturityDate=maturityDate)
        self.logger.info("Maturing deposits : {}".format(maturingBankDeposits))
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
            amountAfterRenewal=deposit.get("RenewalAmount")
            if deposit.get("InterestType") == "SIMPLE" or (deposit.get("InterestType") == "COMPOUND" and deposit.get("InterestCalculateDuration") is not None):
                renewalDate,maturityDate=maturityDate,maturityDate+relativedelta(days=(maturityDate-renewalDate).days)
                amountAfterRenewal+=round(amountAfterRenewal*(maturityDate-renewalDate).days*float(deposit.get("InterestRate").get("0").get("interestRate")/36500))
                isValid,interestRateJson=self.bankDepositUtility.prepareInterestJson(interestRates=float(deposit.get("InterestRate").get("0").get("interestRate")),
                                                startDate=renewalDate,
                                                maturityDate=maturityDate,
                                                interestCalculateType=interestTypeConverter.get(deposit.get("InterestCalculateDuration")),
                                                interestType=deposit.get("InterestType"))
            else:
                interestRateJson=deposit.get("InterestRate")
                for i,interestRate in interestRateJson.items():
                    interestRate["startDate"]=self.bankDepositUtility.convertStrToDate(interestRate.get("startDate"))
                    interestRate["endDate"]=self.bankDepositUtility.convertStrToDate(interestRate.get("endDate"))
                    startDate=interestRate.get("startDate")
                    endDate=interestRate.get("endDate")
                    interestRateJson[i]=({
                        "startDate":startDate+relativedelta(days=(maturityDate-renewalDate).days),
                        "endDate":endDate+relativedelta(days=(maturityDate-renewalDate).days),
                        "interestRate":interestRate.get("interestRate")
                    })
                amountAfterRenewal+=round(amountAfterRenewal*(maturityDate-renewalDate).days*float(interestRateJson.get(i).get("interestRate"))/36500)
                renewalDate,maturityDate=maturityDate,maturityDate+relativedelta(days=(maturityDate-renewalDate).days)
                isValid=self.bankDepositUtility.isValidInterestDurationRange(rateOfInterest=interestRateJson)
                interestRateJson=json.dumps(interestRateJson,indent=4)

            if isValid:
                self.bankDepositUtility.updateBankDeposit(bankDepositId=deposit.get("Id"),
                                                        columns=["InterestRate","RenewalDate","MaturityDate","RenewalAmount"],
                                                        values=[interestRateJson,renewalDate,maturityDate,amountAfterRenewal])
                
    def addNewSip(self):
        sipDate=self.stockUtility.today()
        sips=self.stockUtility.getSIPToday(sipDate)
        self.logger.info("SIPS: {}".format(sips))
        for sip in sips:
            sipAmount=sip.get("SIPAmount")
            nextSipDate=self.stockUtility.getNextSipDate(sipDate=sipDate.day,investedDate=self.stockUtility.today())
            if sip.get("StockId") is not None:
                if self.stockUtility.getInvestmentStatus(stockId=int(sip.get("StockId"))).get("Active"):
                    stockName=self.stockUtility.getStockName(stockId=int(sip.get("StockId")))
                    isValid,stockValue=self.stockUtility.searchStockInfo(stockName=stockName.get("StockName"),period="daily")
                    sipUnit=round(sipAmount/self.stockUtility.getStockAmountOnDate(stockInfo=stockValue,
                                                                date=sipDate),2)
            else:
                if self.stockUtility.getInvestmentStatus(mutualFundId=int(sip.get("MutualFundId"))).get("Active"):
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
