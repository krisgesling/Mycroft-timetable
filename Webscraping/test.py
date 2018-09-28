import webscrape

try:
    status = webscrape.get_module_details('cs4067')
    print(type(status))
    print(status.lecturer)
except:
    print('Nope')
