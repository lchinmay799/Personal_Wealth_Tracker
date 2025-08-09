import string
import random
import logging

import base64
from jwt.exceptions import InvalidSignatureError,ExpiredSignatureError
from flask import Flask,render_template,request,redirect,url_for,make_response,flash
from datetime import timedelta
from flask_jwt_extended import JWTManager,unset_jwt_cookies,jwt_required
from apscheduler.schedulers.background import BackgroundScheduler

from utils.logger import logger
from utils.database.account_utility import UserAccount
from utils.generic_util import UserSession,UserBankInvestment,UserStockInvestment,UserMutualFundInvestment,UserInvestments
from utils.scheduled_jobs import Jobs

logger=logger()
logger=logger.getLogger()

app=Flask(__name__)
jwt=JWTManager(app)
# secret_key="".join(random.choices(string.ascii_letters+string.digits,k=15))
# app.config["JWT_SECRET_KEY"] = secret_key
app.config["JWT_SECRET_KEY"] = "testing_key"
app.secret_key="testing_key"
app.config["JWT_ACCESS_TOKEN_EXPIRES"]=timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"]=timedelta(days=5)
app.config['JWT_TOKEN_LOCATION']= "cookies"
app.config['JWT_ACCESS_COOKIE_NAME']="access_token"
app.config['JWT_REFRESH_COOKIE_NAME']="refresh_token"
app.config['JWT_COOKIE_CSRF_PROTECT']=False

jobs=Jobs()
scheduler=BackgroundScheduler()
autoRenewJob=scheduler.add_job(jobs.renewMaturedBankDeposits,'cron',hour=0,minute=5)
addSipJob=scheduler.add_job(jobs.addNewSip,'cron',hour=9,minute=35)
scheduler.start()

@app.route('/',methods=["POST","GET"])
def homePage():
    userAction = request.form.get("userAction")
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    if userAction:
        user = UserAccount()
        if userAction == "login":
            userEmail = request.form.get("userEmail")
            userPassword = request.form.get("userPassword")
            actualPassword = user.getUserDetail(userEmail=userEmail,returnValue="Password")
            if userPassword == actualPassword:
                userName = user.getUserDetail(userEmail=userEmail,returnValue="Name")
                userId = user.getUserDetail(userEmail=userEmail)
                is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
                response = make_response(render_template('homePage.html',logged_in=True))
                if not is_access_token_valid:
                    access_token=userSession.createAccessToken(userName=userName,userId=userId)
                    response.set_cookie("access_token",access_token,httponly=True)
                if not is_refresh_token_valid:
                    refresh_token=userSession.createRefreshToken(userName=userName,userId=userId)
                    response.set_cookie("refresh_token",refresh_token,httponly=True,samesite="Strict")
                return response
            else:
                flash(message="Login Failed !! Invalid Email or Password",category="error")
                response = make_response(redirect(url_for('login')))
                return redirect(url_for('login'))
            
        elif userAction == "signup":
            userName = request.form.get("userName")
            userEmail = request.form.get("userEmail")
            userPassword = request.form.get("userPassword")
            confirmPassword = request.form.get("confirmPassword")
            if userPassword == confirmPassword:
                if not user.getUserDetail(userEmail=userEmail):
                    userId = user.createUser(userEmail=userEmail,userName=userName,userPassword=userPassword)
                    if userId:
                        access_token=userSession.createAccessToken(userName=userName,userId=userId)
                        refresh_token=userSession.createRefreshToken(userName=userName,userId=userId)
                        response = make_response(render_template('homePage.html',logged_in=True))
                        response.set_cookie("access_token",access_token,httponly=True,samesite="Strict")
                        response.set_cookie('refresh_token',refresh_token,httponly=True,samesite="Strict")
                        return response
                    else:
                        flash(message="Failed to Create an Account !! Try Again.",category="error")
                        return redirect(url_for('signup'))
                else:
                    flash(message="User with the same Email already exists !! Try to Login.",category="error")
                    return redirect(url_for('signup'))
            else:
                flash(message="Passwords Do not Match !!",category="error")
                return redirect(url_for('signup')) 
            
        elif userAction == "resetPassword":
            userEmail = request.form.get("userEmail")
            userPassword = request.form.get("userPassword")
            confirmPassword = request.form.get("confirmPassword")
            if userPassword == confirmPassword:
                if user.getUserDetail(userEmail=userEmail,returnValue="Id"):
                    newPassword = user.updatePassword(userEmail=userEmail,userPassword=userPassword)
                    if newPassword == userPassword:
                        return redirect(url_for('login'))
                    else:
                        flash(message="Failed to Reset Password !! Try Again.",category="error")
                        return redirect(url_for('resetPassword'))
                else:
                    flash(message="User with this Email does not exist !! Create an Account.",category="error")
                    return redirect(url_for('signup'))
            else:
                flash(message="Passwords Do not Match !!",category="error")
                return redirect(url_for('resetPassword'))
    else:
        logger.info("Checking Token Expiry ... ...")
        is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
        if is_access_token_valid:
            userId=userSession.getUserId(token=is_access_token_valid)
            logger.info("Valid Refresh Token for the user : {}".format(userId))
            return render_template('homePage.html',logged_in=True)
        elif is_refresh_token_valid:
            userId=userSession.getUserId(token=is_refresh_token_valid)
            logger.info("Refresh Token expired for the user : {}".format(userId))
            return redirect(url_for('refreshToken'))
        else:
            logger.info("Tokens expired for the user")
            flash(message="Your Session Expired !! Login Again.",category="error")
            return redirect(url_for("login"))

@app.route('/refreshToken',methods=["GET"])
@jwt_required(refresh=True)
def refreshToken():
    userSession=UserSession()
    try:
        refresh_token = request.cookies.get('refresh_token')
        identity = userSession.getClaimFromToken(refresh_token,"sub")
        access_token = userSession.createAccessToken(userName=userSession.getUserName(token=refresh_token),userId=userSession.getUserId(token=refresh_token),identity=identity)
        response = make_response(redirect(url_for('homePage')))
        response.set_cookie("access_token",access_token,httponly=True,samesite="Strict")
        return response
    except (ExpiredSignatureError,InvalidSignatureError) as e:
        return redirect(url_for('login'))

@app.route('/login',methods=["GET"])
def login():
    return render_template('login.html')

@app.route('/signup',methods=["GET"])
def signup():
    return render_template('signup.html')

@app.route('/resetPassword',methods=["GET"])
def resetPassword():
    return render_template('resetPassword.html')

@app.route('/logout',methods=["GET"])
def logout():
    response = make_response(render_template('homePage.html',logged_in=False))
    unset_jwt_cookies(response)
    return response

@app.route('/myinvestments',methods=["GET"])
def trackInvestments():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility = UserInvestments()
        combinedInvestment=utility.getUserCombinedInvestments(userId=userSession.getUserId(token=is_access_token_valid))
        logger.info("Combined Investment of the User {} is {}".format(userId,combinedInvestment))
        return render_template('myInvestments.html',combinedInvestment=combinedInvestment)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/stocks',methods=["GET"])
def stocksInvested():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility = UserStockInvestment()
        stocks,individualAmount = utility.getUserStocks(userId=userSession.getUserId(token=is_access_token_valid))
        logger.info("Stocks Invested : {}".format(stocks))
        return render_template('myStocks.html',stocks=stocks,combinedInvestment=individualAmount)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/stocks/<stockId>')
def getStockInfo(stockId):
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility=UserStockInvestment()
        stockId = int(base64.b64decode(stockId))
        combinedStocksInfo=utility.getStockInformation(stockId=stockId)
        # logger.info("stocksInfo: ",stocksInfo)
        logger.info("combinedStocksInfo: {}".format(combinedStocksInfo))
        return render_template('stockInfo.html',combinedStocksInfo=combinedStocksInfo,
                               vestingStock=combinedStocksInfo.get("vestingInfo") is not None)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/stocks/addInvestment',methods=["GET"])
def addStockInvestment():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        return render_template('addStockInvestment.html')
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/stocks/addInvestment/searchStockInfo',methods=["POST"])
def searchStockInfo():
    utility=UserStockInvestment()
    stockExchange=request.json.get("stockExchange")
    stockName=request.json.get("stockName").upper()
    period=request.json.get("period")
    validStock,stockInfo= utility.searchStockInfo(stockName=stockName+stockExchange,period=period)
    if not validStock:
        flash(message="Invalid Stock Name or Stock Exchange Selected !! Try Again with a Valid Value",category="error")
        return redirect(url_for("addStockInvestment"))
    logger.info("Stock Search response : {}".format(stockInfo))
    openPrice,closePrice,volume,date,volumeLabel=utility.formatStock(stockInfo,period)
    currency=utility.getCurrencySymbol(stockExchange=stockExchange.replace(".",""))
    logger.info("stockExchange is {} and {} and {}".format(currency,stockExchange,stockExchange.replace(".","")))
    return {"open":openPrice,"close":closePrice,"volume":volume,"date":date,"volumeLabel":volumeLabel,"currency":currency}

@app.route('/myinvestments/stocks/addInvestment/addStockInvestment',methods=["POST"])
def newStockInvestment():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        userId=userSession.getUserId(token=is_access_token_valid)
        utility=UserStockInvestment()
        stockExchange=request.form.get("stockExchange")
        stockName=request.form.get("stockName")
        stockName=stockName+stockExchange
        stockPrice=float(request.form.get("stockPrice"))
        stockInvestmentType=request.form.get("stockInvestmentType")
        investedDate=request.form.get("investedDate")
        if stockInvestmentType == "SIP":
            sipAmount=float(request.form.get("sipAmount"))
            sipDate = int(request.form.get("sipDate"))
            sipDate = utility.getNextSipDate(sipDate=sipDate,investedDate=investedDate)
            utility.addStockInvestment(userId=userId,stockName=stockName,investedDate=investedDate,
                                    sip=True,oneTime=False,sipAmount=sipAmount,sipDate=sipDate)
        else:
            stockUnits=int(request.form.get("stockUnits"))
            vestingStock = request.form.get("vestingStock")
            vestingDetailJson=None
            if vestingStock:
                vestingDates=request.form.getlist("vestingDate[]")
                vestingUnits=request.form.getlist("vestingUnits[]")
                valid,vestingDetailJson=utility.prepareVestingJson(vestingDates=vestingDates,vestingUnits=vestingUnits,stockUnits=stockUnits)
                if not valid:
                    flash(message="Incorrect Vesting Information !! Kindly Resubmit with Correct Information.",category="error")
                    response = make_response(redirect(url_for('addStockInvestment')))
                    return response
            utility.addStockInvestment(userId=userId,stockName=stockName,investedDate=investedDate,
                                    sip=False,oneTime=True,vestingDetails=vestingDetailJson,units=stockUnits,oneTimeInvestmentAmount=stockUnits*stockPrice)
        return redirect(url_for('stocksInvested'))
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/stocks/updateVestingDetail',methods=["POST"])
def updateVestingDetail():
    userSession=UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility=UserStockInvestment()
        investmentId=request.form.get("investmentId")
        vestingDates=request.form.getlist("vestingDate[]")
        vestingUnits=request.form.getlist("vestingUnits[]")
        logger.info("vestingDates: {} vestingUnits: {}".format(vestingDates,vestingUnits))
        if not utility.isEmptyStringList(vestingDates) and not utility.isEmptyStringList(vestingUnits):
            stockUnits=utility.getStockUnits(investmentId=investmentId)
            logger.info("stockUnits: {}".format(stockUnits))
            valid,vestingDetailJson=utility.prepareVestingJson(vestingDates=vestingDates,vestingUnits=vestingUnits,stockUnits=stockUnits)
            logger.info("vestingDetailJson: {}".format(vestingDetailJson))
            if not valid:
                flash(message="Incorrect Vesting Information !! Kindly Resubmit with Correct Information.",category="error")
                response = make_response(redirect(url_for('stocksInvested')))
                return response
            else:
                utility.updateStock(investmentId=investmentId,vestingDetails=vestingDetailJson)
                return redirect(url_for('stocksInvested'))
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/mutualfunds',methods=["GET"])
def mutualFundsInvested():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        userId=userSession.getUserId(token=is_access_token_valid)
        utility=UserMutualFundInvestment()
        mutualFunds,combinedMutualFundInfo=utility.getUserMutualFunds(userId=userId)
        logger.info("combinedMutualFundInfo: {}".format(combinedMutualFundInfo))
        logger.info("mutualFunds: {}".format(mutualFunds))
        return render_template('myMutualFunds.html',mutualFunds=mutualFunds,combinedInvestment=combinedMutualFundInfo)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/mutualfunds/<mutualFundId>')
def getMutualFundInfo(mutualFundId):
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility=UserMutualFundInvestment()
        mutualFundId = int(base64.b64decode(mutualFundId))
        mutualFundInfo=utility.getMutualFund(investmentId=mutualFundId)
        logger.info("mutualFundInfo: {}".format(mutualFundInfo))
        return render_template('mutualFundInfo.html',combinedMutualFundsInfo=mutualFundInfo)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/mutualfunds/addInvestment',methods=["GET"])
def addMutualFundInvestment():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        return render_template('addMutualFundInvestment.html')
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/mutualfunds/addInvestment/searchMutualFundInfo',methods=["POST"])
def searchMutualFund():
    utility=UserMutualFundInvestment()
    mutualFundSchemeId=request.json.get("mutualFundSchemeId")
    period=request.json.get("period")
    mutualFundName=request.json.get("mutualFundName")
    isValid,mutualFundInfo=utility.searchMutualFund(schemeId=mutualFundSchemeId)
    if not isValid: 
        flash(message="Incorrect Mutual Fund Scheme Information Submitted. Kindly Resubmit with Correct ID.",category="error")
        return redirect(url_for("addMutualFundInvestment"))
    mutualFundInfo=utility.formatMutualFund(mutualFundData=mutualFundInfo,
                                            period=period)
    if mutualFundName.upper() not in mutualFundInfo:
        flash(message="Incorrect Mutual Fund Scheme Information Submitted. Kindly Resubmit with Correct ID.",category="error")
        return redirect(url_for("addMutualFundInvestment"))
    return {"date":list(reversed(mutualFundInfo[mutualFundName.upper()].keys())),"price":list(reversed(mutualFundInfo[mutualFundName.upper()].values()))}
    
@app.route('/myinvestments/mutualfunds/addInvestment/addMutualFundInvestment',methods=["POST"])
def newMutualFund():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        userId=userSession.getUserId(token=is_access_token_valid)
        utility=UserMutualFundInvestment()
        mutualFundName=request.form.get("mutualFundName").upper()
        mutualFundId=request.form.get("mutualFundId")
        isValid,mutualFundInfo=utility.searchMutualFund(schemeId=mutualFundId)
        if not isValid:
            flash(message="Incorrect Mutual Fund Scheme Information Submitted. Kindly Resubmit with Correct ID.",category="error")
            return redirect(url_for("addMutualFundInvestment"))
        mutualFundInfo=utility.formatMutualFund(mutualFundData=mutualFundInfo)
        if mutualFundName.upper() not in mutualFundInfo:
            flash(message="Incorrect Mutual Fund Scheme Information Submitted. Kindly Resubmit with Correct ID.",category="error")
            return redirect(url_for("addMutualFundInvestment"))
        investedDate=request.form.get("investedDate")
        mutualFundInvestmentType=request.form.get("mutualFundInvestmentType")
        if mutualFundInvestmentType == "SIP":
            sipDate = int(request.form.get("sipDate"))
            sipDate = utility.getNextSipDate(sipDate=sipDate,investedDate=investedDate)
            sipAmount=float(request.form.get("sipAmount"))
            utility.addMutualFundInvestment(userId=userId,schemeName="{}.{}".format(mutualFundName,mutualFundId),investedDate=investedDate,
                                            sip=True,oneTime=False,sipAmount=sipAmount,sipDate=sipDate)
        else:
            mutualFundAmount=float(request.form.get("mutualFundAmount"))
            mutualFundUnitPrice=float(request.form.get("mutualFundUnitPrice"))
            utility.addMutualFundInvestment(userId=userId,schemeName="{}.{}".format(mutualFundName,mutualFundId),investedDate=investedDate,
                                            sip=False,oneTime=True,
                                            units=round(mutualFundAmount/mutualFundUnitPrice,1),oneTimeInvestmentAmount=mutualFundAmount)

        return redirect(url_for('mutualFundsInvested'))
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/<investmentType>/updateSIP',methods=["POST"])
def updateSIP(investmentType):
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility=UserInvestments()
        investmentId=request.form.get("investmentId")
        sipAmount=request.form.get("sipAmount")
        sipDate = int(request.form.get("sipDate"))
        sipDate = utility.getNextSipDate(sipDate=sipDate,investedDate=utility.today())
        updateInfo={}
        if sipAmount!='':
            updateInfo["SIPAmount"]=sipAmount
        if sipDate!='':
            updateInfo["SIPDate"]=sipDate
        utility.updateSIP(updateInfo=updateInfo,
                          investmentId=investmentId,
                          investmentType=investmentType)
        if investmentType=="stocks":
            return redirect(url_for('stocksInvested'))
        elif investmentType=="mutualfunds":
            return redirect(url_for('mutualFundsInvested'))
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/bankdeposits',methods=["GET"])
def bankDepositsInvested():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        userId=userSession.getUserId(token=is_access_token_valid)
        utility=UserBankInvestment()
        bankDeposits,amount=utility.getUserCombinedBankDepositAmount(userId=userId)
        logger.info("Current Amount of user {} is {} and {}".format(userId,amount,bankDeposits))

        return render_template('myBankDeposits.html',combinedInvestment=amount,bankDeposits=bankDeposits)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/bankdeposits/<bankInvestmentId>')
def getBankDepositInfo(bankInvestmentId):
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        utility=UserBankInvestment()
        bankInvestmentId = int(base64.b64decode(bankInvestmentId))
        combinedDepositInfo=utility.getBankDepositInfomation(bankInvestmentId=bankInvestmentId)
        return render_template('bankDepositInfo.html',combinedDepositInfo=combinedDepositInfo)
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/bankdeposits/addInvestment',methods=["GET"])
def addBankDeposit():

    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        return render_template('addBankDeposits.html')
    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))

@app.route('/myinvestments/bankdeposits/addInvestment/addBankDeposit',methods=["POST","GET"])
def newBankDeposit():
    logger.info("Checking Token Expiry ...")
    userSession = UserSession()
    is_access_token_valid,is_refresh_token_valid=userSession.checkTokenExpiry()
    if is_access_token_valid:
        userId=userSession.getUserId(token=is_access_token_valid)
        logger.info("Valid Refresh Token for the user : {}".format(userId))
        userId=userSession.getUserId(token=is_access_token_valid)
        bankName=request.form.get("Bank").upper()
        principalAmount = float(request.form.get("Amount"))
        interestType = request.form.get("InterestType")
        invsetmentDate = request.form.get("InvestedDate")
        maturityYears=request.form.get("maturityYears")
        maturityMonths=request.form.get("maturityMonths")
        maturityDays=request.form.get("maturityDays")
        autoRenew=request.form.get("autoRenew",False)

        utility=UserBankInvestment()
        invsetmentDate=utility.convertStrToDate(invsetmentDate)
        isValid,maturityDate=utility.isValidMaturityDate(maturityDate=[maturityDays,maturityMonths,maturityYears],startDate=invsetmentDate)
        if not isValid:
            flash(message="Invalid Maturity Date Submitted !! Kindly Resubmit.",category="error")
            response = make_response(redirect(url_for('addBankDeposit')))
            return response
        if not autoRenew:
            autoRenew=True
        if interestType == "SIMPLE":
            rateOfInterest = request.form.get("simpleInterestRate")
            interestCalculateType = request.form.get("simpleInterestCalculateType")
            logger.info("simple-periodic: {} {} {}".format(rateOfInterest,invsetmentDate,maturityDate))
            isValid,interestRateJson=utility.prepareInterestJson(interestRates=rateOfInterest,startDate=invsetmentDate,maturityDate=maturityDate,
                                                                 interestCalculateType=interestCalculateType,interestType=interestType)
        else:
            interestCalculateType = request.form.get("compoundInterestCalculateType")
            if interestCalculateType == "NONE":
                startYears=request.form.getlist("startyears[]")
                startMonths=request.form.getlist("startmonths[]")
                startDays=request.form.getlist("startdays[]")
                endYears=request.form.getlist("endyears[]")
                endMonths=request.form.getlist("endmonths[]")
                endDays=request.form.getlist("enddays[]")
                interestRates =request.form.getlist("compoundInterestRates[]")
                logger.info("compound-fd {} {} {} \n {} {} {}\n {}".format(startDays,startMonths,startYears,endDays,endMonths,endYears,interestRates))
                isValid,interestRateJson=utility.prepareInterestJson(interestRates,invsetmentDate,startDays=startDays,startMonths=startMonths,startYears=startYears,
                                                                     endDays=endDays,endMonths=endMonths,endYears=endYears,maturityDate=maturityDate,
                                                                     interestCalculateType=interestCalculateType,interestType=interestType)
                if not isValid:
                    flash(message="Invalid Compound Interest Submitted !! Kindly Resubmit.",category="error")
                    response = make_response(redirect(url_for('addBankDeposit')))
                    return response
            else:
                rateOfInterest = request.form.get("compoundInterestRate")
                logger.info("compound-periodic: {} {} {}".format(rateOfInterest,invsetmentDate,maturityDate))
                isValid,interestRateJson=utility.prepareInterestJson(interestRates=rateOfInterest,startDate=invsetmentDate,maturityDate=maturityDate,
                                                                     interestCalculateType=interestCalculateType,interestType=interestType)
        logger.info("interestRateJson is : {} and its type is {}".format(interestRateJson,type(interestRateJson)))
        utility.addNewBankDeposit(userId=userId,bank=bankName,amount=principalAmount,interest=interestRateJson,interestCalculateType=interestCalculateType,
                                  investmentDate=invsetmentDate,maturityDate=maturityDate,interestType=interestType,autoRenew=autoRenew)
        deposits=utility.getAllBankInvestments()
        for i in deposits:
            logger.info("{}".format(i))
        return redirect(url_for('bankDepositsInvested'))

    elif is_refresh_token_valid:
        userId=userSession.getUserId(token=is_refresh_token_valid)
        logger.info("Refresh Token expired for the user : {}".format(userId))
        return redirect(url_for('refreshToken'))
    else:
        logger.info("Tokens expired for the user")
        flash(message="Your Session Expired !! Login Again.",category="error")
        return redirect(url_for("login"))
    
@app.route('/myinvestments/setInactive',methods=["POST"])
def markInvestmentInactive():
    utility=UserInvestments()
    investmentId=request.json.get("InvestmentId")
    investmentType=request.json.get("InvestmentType")
    utility.markInvestmentAsInactive(investmentId=int(investmentId))
    return {"redirect":"/myinvestments/{}".format(investmentType)}

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=5000)