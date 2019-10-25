# -*- coding:utf-8 -*-

import urllib2,time,multiprocessing,threading
from bs4 import BeautifulSoup

def checker(url,mtimeout=3):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"}
    try:
        request = urllib2.Request(url, headers=header)
        response = urllib2.urlopen(request, timeout=mtimeout)
        return (response.info(),response.read())
    except:
        return ("","")



def getplaylist():
    countrys = []
    info, page = checker("https://github.com/iptv-org/iptv")
    if(info['status']=='200 OK'):
        soup = BeautifulSoup(page, features="html.parser")
        tables = soup.findAll('table')
        tbody = tables[-1].find('tbody')
        if(tbody):
            for tr in tbody.children:
                countrys.append((tr.contents[0].text,tr.contents[2].text))
    return countrys

def parse(country):
    country_name=country[0]
    country_url=country[1]
    print "#"+country_name
    lines = checker(country_url,5)[1].split("\n")
    name=""
    url=""
    list=[]
    for line in lines:
        line=line.decode('u8')
        if(line.startswith("#EXTINF")):
            name = line.split(",")[-1].replace("\r","").replace("\n","").strip()
        elif(line.startswith("http")):
            url = line.replace("\r","").replace("\n","").strip()
        if(name and url):
            list.append((name,url))
            name=""
            url=""
    return list


def checktts(country_name, list):
    msg=""
    for content in list:
        try:
            name, url = content
            movie_url = url
            retry = 0
            while movie_url.endswith(".m3u8") and retry < 5:
                retry += 1
                info, data = checker(url)
                if (len(data) < 10):
                    continue
                lines = data.split('\n')
                for line in lines:
                    if line and not line.startswith("#"):
                        movie_url = line
                        break
                if movie_url:
                    movie_url = url.replace(url.split("/")[-1], movie_url)
            if (movie_url.endswith(".ts")):
                # print movie_url,
                info, data = checker(movie_url, 6)
                if (len(data) > 102400):
                    if(name.strip()==""):
                        name="unkown"
                    print name, " is available"
                    msg += "%s,%s\n" % (name, url)
                # else:
                #     print name, " is not available"
        except:
            pass

    if (len(msg) > 50):
        f = open(r"./channels/available_iptv_address_%s.txt" % country_name, "a")
        f.write(msg.encode('u8'))
        f.close()

def worker(country):
    list = parse(country)
    work_pre = 50
    th_pool_max=len(list) / work_pre
    if(th_pool_max>70):
        th_pool_max=70
        work_pre = len(list) / th_pool_max
    if(th_pool_max==0):
        th_pool_max=1
    msg = "#" + country[0] + "\n"
    f = open(r"./channels/available_iptv_address_%s.txt" % country[0], "a")
    f.write(msg.encode('u8'))
    f.close()
    threads = []
    for i in xrange(work_pre):
        t = threading.Thread(target=checktts, args=(country[0],list[i*work_pre:i*work_pre+work_pre]))
        t.start()
        threads.append(t)
    if (len(list) % th_pool_max > 0):
        t = threading.Thread(target=checktts, args=(country[0], list[work_pre*th_pool_max:]))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def main(countrys):
    print "the worker will work on %d tasks."%len(countrys)
    for country in countrys:
        worker(country)

thread_pool_max=40

if __name__ == '__main__':
    countrys=getplaylist()
    thread_pool_max = len(countrys)
    work_pre = len(countrys)/thread_pool_max
    process=[]
    for i in xrange(thread_pool_max):
        p1 = multiprocessing.Process(target=main, args=(countrys[i*work_pre:i*work_pre+work_pre],))
        p1.start()
        process.append(p1)
    if(len(countrys)%thread_pool_max>0):
        p1 = multiprocessing.Process(target=main, args=(countrys[thread_pool_max*work_pre:],))
        p1.start()
        process.append(p1)
