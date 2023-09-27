import base64
import argparse
import subprocess
import os

import requests
import pandas as pd

EMAIL = os.environ.get("EMAIL")
KEY   = os.environ.get("KEY")

def base64_encode(s):
    s_encode = base64.b64encode(s.encode('utf8'))
    return s_encode.decode()

def base64_decode(s):
    s_decode = base64.b64decode(s.encode('utf8'))
    return s_decode.decode()


def get_ip(base_api_url, query):
    
    query_base64 = base64_encode(query)
    apiurl = base_api_url.format(EMAIL, KEY, query_base64)

    header = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",
    }

    try:
        res = requests.get(apiurl, headers=header, timeout=10)
    except Exception as e:
        print(f"requests error: {e}")
        return None, None
    
    resp = res.json()
    err = resp['error']
    if err:
        # print(f"api response error: {resp['errmsg']}")
        return None, None

    size = resp['size']
    resip = resp['results']
    ips = [ip[1] for ip in resip]
    return size, list(set(ips))

def run_speedtest(testurl):

    cmd = ["./CloudflareST", "-url", testurl, "-f", "./ips.txt", "-httping", "-dd"， "-o", "result.csv"]
    try:
        result = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if 'result.csv' in result.stdout.decode():
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        print(f"{cmd} failed!")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseapi", type=str, required=True)
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--testurl", type=str, required=True)  

    args = parser.parse_args()

    apiurl = args.baseapi
    query = args.query
    testurl = args.testurl

    size, iplist = get_ip(apiurl, query)
    if size is None:
        print("api error!")
        exit(1)
    
    output_file = "./ips.txt"
    with open(output_file, "w", encoding='utf-8') as f:
        f.write("\n".join(iplist))
    
    if run_speedtest(testurl):
        print("success!")
    else:
        exit(1)

    res_file = "./result.csv"
    res = pd.read_csv(
        res_file, 
        sep=',', 
        header=0, 
        skipinitialspace=True
    )

    res_ips = res.iloc[:, 0].tolist()
    print(len(res_ips))
    with open(res_file, "w", encoding='utf-8') as f:
        f.write("\n".join(res_ips))

    print('Done!')
