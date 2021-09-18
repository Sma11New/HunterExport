#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
# @Author   : Sma11New
# @Github   : https://github.com/Sma11New

import os
import csv
import time
import base64
import datetime
import requests
import configparser
from dateutil.relativedelta import relativedelta

from colorama import init
init(autoreset=True)

from wcwidth import wcswidth as ww
def rpad(s, n, c=" "):
    return s + (n - ww(s)) * c

requests.packages.urllib3.disable_warnings()

def printLogo():
    logo = """
           __ __          __          ____                    __ 
          / // /_ _____  / /____ ____/ __/_ __ ___  ___  ____/ /_
         / _  / // / _ \/ __/ -_) __/ _/ \ \ // _ \/ _ \/ __/ __/
        /_//_/\_,_/_//_/\__/\__/_/ /___//_\_\/ .__/\___/_/  \__/ 
                                            /_/           
        Author：Sma11New
        Version：2.0 (base64Encode)
"""
    msg = """全球鹰Hunter数据导出，仅支持QAX员工接入内网时使用

    Usage: python3 HunterExport.py
        Command> app="***"      (单次查询)
        Command> file filePath  (批量查询)
        Command> help           (查看语法)

注：首先接入内网，登录全球鹰Hunter获取用户名（邮箱）和密钥（Key），写入default.conf配置文件
    运行 HunterEcport.py 输入查询指令即可获取数据，并输出至文件。(Ctrl+C终止)

"""
    print("\033[91m" + logo + "\033[0m")
    print(msg)

# 输出查询文档
def printSearchDocument():
    msg = f"""
精确查询可以使用"=="； 模糊查询可以使用"="；精确剔除可以使用"!=="； 模糊剔除可以使用"!="； 
可以使用 and、 &&或 or、 || 进行多种条件组合查询
    
    {rpad("语法内容", 45)}语法说明
    {"-" * 90}
    {rpad('title="北京"', 45)}从网站标题中搜索"北京"
    {rpad('body="网络空间测绘"', 45)}搜索网站正文包含"网络空间测绘"的资产
    {rpad('app="用友致远oa"', 45)}搜索标记为"用友致远oa"的资产
    {rpad('component_name="nginx"', 45)}搜索组件名称为"nginx"的资产
    {rpad('component_name="nginx/1.18.0"', 45)}搜索组件名称为"nginx"且组件版本为"1.18.0"的资产
    {rpad('cert="baidu"', 45)}搜索证书中带有baidu的资产
    {rpad('ip="1.1.1.1"', 45)}搜索IP为 "1.1.1.1"的资产
    {rpad('ip="220.181.111.1/24"', 45)}搜索起始IP为"220.181.111.1"的C段资产
    {rpad('port="6379"', 45)}搜索开放端口为"6379"的资产
    {rpad('protocol="http"', 45)}搜索协议为"http"的资产
    {rpad('is_domain=true', 45)}搜索域名标记不为空的资产
    {rpad('domain="qq.com"', 45)}搜索域名包含"qq.com"的网站
    {rpad('domain_suffix="qq.com"', 45)}搜索主域为qq.com的网站
    {rpad('icp_number="京ICP备16020626号-8"', 45)}搜索通过域名关联的ICP备案号的网站资产
    {rpad('icp_web_name="谷歌"', 45)}搜索ICP备案网站名中含有"谷歌"的资产
    {rpad('icp_company_name="谷歌"', 45)}搜索ICP备案单位名中含有"谷歌"的资产
    {rpad('icp_company_type="企业"', 45)}搜索ICP备案主体为"企业"的资产
    {rpad('server=="Microsoft-IIS/10"', 45)}搜索server全名为"Microsoft-IIS/10"的服务器
    {rpad('web_content_length="691"', 45)}搜索HTTP消息主体的大小为691的网站
    {rpad('status_code="402"', 45)}搜索HTTP请求返回状态码为"402"的资产
    {rpad('header="elastic"', 45)}搜索HTTP请求头中含有"elastic"的资产
    {rpad('after="2021-01-01"&&before="2021-12-21"', 45)}搜索2021年的资产
    {rpad('country="中国"', 45)}搜索IP对应主机所在国为"中国"的资产
    {rpad('province="江苏"', 45)}搜索IP对应主机在江苏省的资产
    {rpad('city="北京"', 45)}搜索IP对应主机所在城市为"北京"市的资产
    {rpad('isp="电信"', 45)}搜索运营商为"中国电信"的资产
    {rpad('base_protocol="udp"', 45)}搜索传输层协议为"udp"的资产
    {rpad('os="Windows"', 45)}搜索操作系统标记为"Windows"的资产
    {rpad('asn="136800"', 45)}搜索asn为"136800"的资产
    {rpad('as_name="CLOUDFLARENET"', 45)}搜索asn名称为"CLOUDFLARENET"的资产
    {rpad('as_org="PDR"', 45)}搜索asn注册架构为"PDR"的资产
    """
    print(msg)

# 加载配置
def loadConfFile(fileName):
    try:
        conf = configparser.ConfigParser()
        conf.read(fileName, encoding="utf8")
        mail = conf.get("Setting", "mail")
        key = conf.get("Setting", "key")
        countMax = conf.getint("Setting", "countMax")
        searchMonth = conf.getint("Setting", "searchMonth")
        timeSleep = conf.getfloat("Setting", "timeSleep")
        isWeb = conf.getint("Setting", "isWeb")
        return mail, key, countMax, searchMonth, timeSleep, isWeb
    except:
        print("""\033[31mkey.conf Error, for Example: 
        mail = example@qianxin.com
        key = abcdefgh12345678987654321hgfedcba
        countMax = 1000
        searchMonth = 12
        timeSleep = 1
        isWeb = 1\033[0m\n""")
        exit(0)

# 重写print
def newPrint(flag, massage, flush=False, start = "", end="\n"):
    if not os.path.isdir('./log/'):
        os.mkdir('./log/')
    date = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime())
    if flag == "SCMD":
        print(f"{start}[\033[34m{date}\033[0m]  [\033[36mSCMD\033[0m]  {massage}", flush=flush, end=end)
    if flag == "INFO":
        print(f"{start}[\033[34m{date}\033[0m]  [\033[36mINFO\033[0m]  {massage}", flush=flush, end=end)
    elif flag == "ERROR":
        print(f"{start}[\033[34m{date}\033[0m]  [\033[31mERRO\033[0m]  {massage}", flush=flush, end=end)
    else:
        pass
    with open('./log/debug.log', "a", encoding="utf-8") as f:
        f.write(f"[{date}] - {flag} - {massage}\n")

# 查询数据
def searchData(mail, key, command, countMax, searchMonth, timeSleep, isWeb):
    resultList = []
    pageSize = 100  # 每页条数，最大100
    newPrint(flag="SCMD", massage=command)
    endTime = datetime.date.today()
    startTime = datetime.date.today() - relativedelta(months=+searchMonth)
    # 新版做base64编码
    commandBase64Encode = str(base64.encodebytes(command.encode("utf8"))).replace("b'", "").replace("'", "").replace(
        r"\n", "")
    # commandBase64Encode = command
    url = f'https://geagle.qianxin-inc.cn/openApi/search?username={mail}&api-key={key}&search={commandBase64Encode}&start_time={startTime}&end_time={endTime}&page=1&page_size=10&is_web={isWeb}'
    # print(url)
    rep = requests.get(url, verify=False)
    if rep.json()["code"] == 200:
        repCode, dataTotal, timeSpend = rep.json()["code"], rep.json()["data"]["total"], rep.json()["data"]["time"]
        newPrint(flag="INFO", massage=f"Code: {repCode}   Result: {dataTotal}条   Time: {timeSpend / 1000}秒")
        dataTotal = int(dataTotal)
        # 计算需要请求的页数
        if dataTotal > 0:
            nameList = list(rep.json()["data"]["arr"][0].keys())
            if countMax >= dataTotal:
                exportTotal = dataTotal
                pageEnd = int(dataTotal / pageSize) + 1
            else:
                exportTotal = countMax
                pageEnd = int(countMax / pageSize) + 1
            newPrint(flag="INFO", massage=f"Exporting: {exportTotal}条   ExportMax: {countMax}条   ExportTime: {searchMonth}个月")
            # 按页请求
            for page in range(1, pageEnd + 1):
                url = f'https://geagle.qianxin-inc.cn/openApi/search?username={mail}&api-key={key}&search={commandBase64Encode}&start_time={startTime}&end_time={endTime}&page={page}&page_size={pageSize}&is_web={isWeb}'
                r = requests.get(url, verify=False)
                if r.json()["code"] == 200:
                    endFlag = ""
                    if page == pageEnd:
                        endFlag = "\n"
                    newPrint(flag="INFO", massage=f"Exporting, Please Waiting……  \033[32m[page {page}/{pageEnd}]\033[0m", flush=True, start="\r", end=endFlag)
                    dataList = r.json()["data"]["arr"]
                    for i in dataList:
                        result = list(i.values())
                        resultList.append(result)
                else:
                    newPrint(flag="ERROR", massage=f"第{page}页 {r.json()}", start="\n", flush=True)
                time.sleep(timeSleep)
            output(command, nameList, resultList)
    else:
        newPrint(flag="ERROR", massage=rep.json())

# 批量查询
def batchSearchData(mail, key, commandList, countMax, searchMonth, timeSleep, isWeb):
    count = 1
    for command in commandList:
        print(f"\033[32m[>] 当前总进度: {count}/{len(commandList)} \033[0m")
        try:
            searchData(mail, key, command, countMax, searchMonth, timeSleep, isWeb)
        except:
            newPrint(flag="ERROR", massage="Export Error.")
        count += 1
    print(f"\n\033[32m[>] 全部任务已结束\033[0m")

# 解析输入命令
def parseCommand(mail, key, command, countMax, searchMonth, timeSleep, isWeb):
    commandList = []
    if command =="hlep" or command =="?":
        printSearchDocument()
    elif command.split()[0] == "file":
        commandFile = command.split()[1]
        try:
            with open(commandFile, "r", encoding="utf8") as f:
                for line in f.readlines():
                    commandList.append(line.strip())
        except:
            newPrint(flag="ERROR", massage="Load File Error.")
            exit(0)
        batchSearchData(mail, key, commandList, countMax, searchMonth, timeSleep, isWeb)
    else:
        searchData(mail, key, command, countMax, searchMonth, timeSleep, isWeb)

# 输出结果
def output(command, nameList, resultList):
    errorSign = ["\\", "/", ":", "?", "<", ">", "|", "*"]
    date = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
    if not os.path.isdir("./output"):
        os.mkdir("./output")
    fileaName = f"{command}_{date}.csv"
    for sign in errorSign:
        if sign in fileaName:
            fileaName = fileaName.replace(sign, "-")
    outputFile = f"./output/{fileaName}".replace("\"", "")
    with open(outputFile, "a", encoding="GB18030", newline="") as f:
        csvWrite = csv.writer(f)
        csvWrite.writerow(nameList)
        for result in resultList:
            csvWrite.writerow(result)
    newPrint(flag="INFO", massage=outputFile)

if __name__ == "__main__":
    printLogo()
    mail, key, countMax, searchMonth, timeSleep, isWeb = loadConfFile("./default.conf")
    while True:
        try:
            command = input("Command> ")
            parseCommand(mail, key, command, countMax, searchMonth, timeSleep, isWeb)
        except KeyboardInterrupt:
            print("\nBye~")
            break
