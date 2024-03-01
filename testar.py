str = ': ping - 2024-02-28 06:03:06.287647'
try:
    str.split('data: ', 1)[1]
except Exception as e:
    print(e)