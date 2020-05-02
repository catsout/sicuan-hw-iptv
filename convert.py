import re
import os
import sys
import json

def filter_name(filter_names):
    filter_names = filter_names.split(',')
    def temp(name, url):
        is_find = False
        for i in filter_names:
            if name.find(i) != -1:
                is_find = True
                break
        return is_find
    return temp

def getChannelList(channel_text, f_filter):
    re_channel = re.compile('\(.+?\);')
    channel_list = []
    for i in re.finditer(re_channel,channel_text):
        i = i.group()
        channel_name = re.search('ChannelName=\"(.+?)\"',i)
        channel_url = re.search('ChannelURL=\"(.+?)\"',i)
        if not (channel_name is None or channel_url is None):
            channel_name = channel_name.group(1).strip()
            if f_filter(channel_name, channel_url):
                continue
            channel_url = channel_url.group(1).strip()
            channel_list.append({'channel-name':channel_name,'url':channel_url})
    return channel_list

def parseExtinf(m3u_text):
    info = []
    re_extinf = re.compile('#EXTINF.+?\n')
    re_tvg = re.compile('([a-z\-]+?)=\"(.*?)\"')
    for extinf in re.finditer(re_extinf,m3u_text):
        info_i = {}
        for i in re.finditer(re_tvg,extinf.group()):
            name = i.group(1)
            value = i.group(2)
            if name == 'tvg-logo':
                value = value.split('/')[-1]
            info_i[name] = value
            
        info_i['channel-name'] = extinf.group().split(',')[-1]
        info.append(info_i)
    return info
    #return json.dumps(info, indent=True, ensure_ascii=False)
           
def genM3u(extinf, channel_list, convert_url):
    # exinf [{'k':v,...,'channel-name':['cctv1','cctv1高清']}, ]
    def find_extinf_byname(extinf, channel_name):
        for i in extinf:
            if channel_name in i['channel-name']:
                return i
        return None
    
    m3u = '#EXTM3U\n'
    for i in channel_list:
        m3u += '#EXTINF:-1 '
        info = None
        if extinf is not None:
            info = find_extinf_byname(extinf,i['channel-name'])
        
        if info is not None:
            info_text = ''
            for k,v in info.items():
                if k == 'channel-name':
                    continue
                info_text += k +'="'+ v +'" '
            m3u += info_text
        else:
            #add "tvg-id" for no match
            m3u += 'tvg-id="-1" '
        m3u += ','+ i['channel-name'] +'\n'+ convert_url(i['url']) +'\n'
    print(m3u)

def cv_to_udp(url):
    return url.replace('igmp','udp')
def cv_to_udpxy(dest):
    def temp(url):
        return url.replace('igmp://','http://'+dest+'/udp/')
    return temp

    

if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="conver iptvchannel list to m3u\n usage: convert < listfile")
    parser.add_argument('--parse-m3u', help='parse extinf from m3u to json')
    parser.add_argument('--extinf', help='read extinf from json')
    parser.add_argument('--udpxy', help='convert igmp url to http with udpxy\'s ip:port, like 192.168.1.1:4022')
    parser.add_argument('--filter-name', help='filter by name when parse listfile, usage: str1,str2')

    args = parser.parse_args()
    channel_list = {}
    f_conver_url = cv_to_udp
    f_filter = lambda x,y:False

    if args.udpxy is not None:
        f_conver_url = cv_to_udpxy(args.udpxy)

    if args.filter_name is not None:
        f_filter = filter_name(args.filter_name)

    if (args.parse_m3u is not None) and (args.parser_extinf is not None):
        pass
    elif args.parse_m3u is not None:
        with open(args.parse_m3u,'r') as f:
            info = parseExtinf(f.read())
        print(json.dumps(info, indent=True, ensure_ascii=False))
    elif args.extinf is not None:
        with open(args.extinf,'r') as f:
           exinf_list = json.load(f)
        channel_list = getChannelList(sys.stdin.read(),f_filter)
        genM3u(exinf_list, channel_list, f_conver_url)
    else:
        channel_list = getChannelList(sys.stdin.read(),f_filter)
        genM3u(None, channel_list, f_conver_url)



