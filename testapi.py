import requests

url="http://api.open-notify.org/iss-now.json"

responce=requests.get(url)
data=responce.json()
print(responce.status_code)
# this should be 200 if everything is okay
print(data)