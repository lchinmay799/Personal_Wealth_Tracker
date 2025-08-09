import requests
from utils.logger import logger

class APIRequest():
    def __init__(self):
        self.logger=logger()
        self.logger=self.logger.getLogger()

    def make_request(self,url,method,query_params=None,request_headers=None,request_body=None):
        response=requests.request(method=method,url=url,
                                  headers=request_headers,
                                  data=request_body,
                                  params=query_params)
        self.logger.info("Request with URL: {} \n METHOD: {} \n QUERY PARAM : {} \n REQUEST HEADERS: {} \n REQUEST BODY : {} \n received RESPONSE: {}".format(url,method,query_params,request_headers,request_body,response.json()))
        return response