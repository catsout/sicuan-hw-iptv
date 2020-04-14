
import requests
from requests_toolbelt.adapters import source
from bs4 import BeautifulSoup
from Crypto.Cipher import _DES3
from Crypto.Random import random
import re
import types
import time
import os
import json


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-cn",
    "Accept-Charset": "utf-8, *;q=0.7",
}

def genAuthInfo(rep,ctc_conf):
    #3DES(Random+“$”+EncryToken+”$”+UserID +”$”+STBID+”$”+IP+”$”+MAC+”$”+Reserved+ ”$”+ “CTC”) \x01
    key = ctc_conf['mpassword'].ljust(24,'0')
    random_8 = str(random.getrandbits(100))[0:8]
    #for the case that usertoken have not get
    if type(ctc_conf.get('usertoken')) != type('') :
        ctc_conf['usertoken'] = getUserToken(rep,ctc_conf)

    authText = random_8 + '$' + ctc_conf['usertoken'] +'$'+ ctc_conf['userid'] +'$'+ ctc_conf['stbid'] +'$'+ '10.143.117.158' +'$'+ ctc_conf['mac'] +'$'+''+'$'+ 'CTC'
    #seems that v'\x01' is the end of js string
    authBytes = bytes(authText, encoding='ascii').ljust(128,b'\x01')
    print(authBytes)
    crypt = _DES3.new(key, _DES3.MODE_ECB)
    return crypt.encrypt(authBytes).hex()

def getUserToken(rep,ctc_conf):
    re_token = re.search('Token = \"([0-9A-Za-z]+?)\"',rep.text)
    if re_token is not None:
        return re_token.group(1)
    else:
        return None
    
conf = {
    'src': None
}

ctc_conf = {
    'authenticator': genAuthInfo,
    'usertoken':getUserToken
}

save_dir = './save/'

def goForm(session,rep):
    # parser html
    soup = BeautifulSoup(rep.text, "html.parser")
    if soup.form is None:
        return
    epgip_port = session.cookies["EPGIP_PORT"].strip('\"')
    url = 'http://' + epgip_port + '/EPG/jsp/' + soup.form['action']
    method = soup.form['method'].lower()
    data = None
    if method == 'post':
        data = {}
        # use 'input' get form items
        for i in soup.findAll('input'):
            #lower to match
            low_name = i['name'].lower()
            data[i['name']] = i['value']
            if i['value'] == '' and (ctc_conf.get(low_name) is not None):
                #use specific func for some items
                if type(ctc_conf[low_name]) == types.FunctionType:
                    data[i['name']] = ctc_conf[low_name](rep,ctc_conf)
                else:
                    data[i['name']] = ctc_conf[low_name]
    print(url)
    rep = session.request(method,url,data=data,headers=headers)
    file_path = url.split('/')[-1].split('?')[0]
    with open(save_dir+file_path,'w+') as f:
        f.write(rep.text)
    time.sleep(1)
    return goForm(session,rep)

def go():
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    session = requests.Session()
    if conf['src'] is not None:
        src = source.SourceAddressAdapter(conf['src'])
        session.mount('http://',src)

    portal_url = ctc_conf['portal-url'] + ctc_conf['userid']
    print(portal_url)
    rep = session.request('get',portal_url)
    goForm(session,rep)

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="get channel list from iptv network")
    parser.add_argument('-c','--conf', help='json conf file')
    parser.add_argument('-s','--src-ip', help='specific request source ip')
    args = parser.parse_args()
    conf['src'] = args.src_ip
    conf_file = './ctc.json'
    if args.conf is not None:
        conf_file = args.conf
    if os.path.exists(conf_file):
        with open(conf_file,mode='r') as f:
            ctc_conf.update(json.load(f))
    else:
        pass

    go()

