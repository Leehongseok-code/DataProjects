import requests

api_key = "test_9a21fd22af452bb384e7ef20bc0fc87caa8bec8e9862e268169a061dc7bf0a2aefe8d04e6d233bd35cf2fabdeb93fb0d"

headers = {
"x-nxopen-api-key": api_key
}

characterName = "CHARACTER NAME"
urlString = "https://open.api.nexon.com/maplestory/v1/ranking/overall?date=2023-12-22&world_type=0"
response = requests.get(urlString, headers = headers)



result = response.json()

print(result)

rank_dict = result['ranking']

n = len(rank_dict)
print(n)