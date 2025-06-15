import requests

class APIRequest():
    def make_request(self,url,method,query_params=None,request_headers=None,request_body=None):
        response=requests.request(method=method,url=url,
                                  headers=request_headers,
                                  data=request_body,
                                  params=query_params)
        return response