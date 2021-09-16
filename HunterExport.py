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

注：首先接入内网，登录全球鹰Hunter获取用户名（邮箱）和密钥（Key），写入default.conf配置文件
    运行 HunterEcport.py 输入查询指令即可获取数据，并输出至文件。(Ctrl+C终止)

"""
    print("\033[91m" + logo + "\033[0m")
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
    if command.split()[0] == "file":
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
