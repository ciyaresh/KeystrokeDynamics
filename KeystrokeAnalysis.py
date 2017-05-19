from tkinter import *
import numpy as np
import json
from math import fabs
import matplotlib.pyplot as plt
import smtplib
from email.mime.text import MIMEText

current_kd=[]
current_ku=[]
trained = 0
classification_vector=[]
c_vector_overlap=[]
c_vector_undetected=[]
tbutton = None
tmsg=None
pwd = []
usr = ''
matrix=[]

def get_list(l):
    try:
        return json.loads(l)
    except Exception:
        return []

def get_float(f):
    return float(f) if f else 0


def norm(a,b, coeff):
    diff = np.array(a)-np.array(b)
    return np.matmul(np.matmul(diff,coeff),np.reshape(diff,(-1,1)))

def get_inverse_cov(matrix):
    cov_mat = np.cov(list(zip(*(l for l in matrix))))
    if(np.linalg.matrix_rank(cov_mat)<2):
        return False
    coeff = np.linalg.inv(cov_mat) if np.linalg.det(cov_mat) else np.linalg.pinv(cov_mat)
    return coeff

def verify_vector(username, vector):
    global matrix
    extn = ''
    positive = sum(x>=0 for x in vector)
    negative = sum(x<0 for x in vector)
    if(positive+negative==len(current_kd)*2-1):
        if not negative:
            extn='.vector'
            print('using vector')
        else:
            extn='.vector-overlap'
            print('using vector-overlap')
    else:
        extn='.vector-miss'
        print('using vector-miss')
    f=open(username+extn,'r')
    matrix = get_list(f.readline().strip())
    threshold=get_float(f.readline().strip())
    coeff = get_inverse_cov(matrix)
    if coeff is False:
        return False
    norms=[norm(vector,x,coeff) for x in matrix]
    print(str(norms))
    shortest = min(fabs(x)**0.5 for x in norms)
    print('SHORTEST',shortest)
    return True if shortest<4*threshold else False

def train(entry, parent):
    global trained
    global current_kd
    global current_ku
    global usr
    global tmsg
    processed = transform(current_kd,current_ku)
    positive = sum(x>=0 for x in processed)
    negative = sum(x<0 for x in processed)
    if(positive+negative==len(current_kd)*2-1):
        if not negative:
            classification_vector.append(processed)
        else:
            c_vector_overlap.append(processed)
    else:
        c_vector_undetected.append(processed)
    trained +=1
    tmsg.config(text="Trainings completed (out of 10):"+str(trained))
    entry.delete(0,END)
    current_kd =[]
    current_ku=[]
    if(trained >9):
        tbutton=Button(parent, text="register", command=lambda: save(usr.get(),parent))
        tbutton.grid(row=3, column=1, sticky=EW, padx=10,pady=10)
    return

def keyd(event):
    current_kd.append((event.keysym,event.time))
    print(str(current_kd))
    return

def keyu(event):
    current_ku.append((event.keysym,event.time))
    print(str(current_ku))
    return

def clean(vector,up=False):
    y=[]
    for x in vector:
        if(x[0]=='Tab' or x[0]=='Enter' or x[0]=='Return'):
            continue
        elif(x[0]=='BackSpace'):
            if(len(y) !=0):
                del y[-1]
        else:
            y.append(x)
    if up:
        for i in range(len(y)-1):
            if(y[i+1][0] in ['Shift_L', 'Shift_R']):
                y[i], y[i+1] = y[i+1], y[i]
    return y

def authenticate(username, password, screen):
    global usr
    usr=username
    if not username or not password:
        return failure_screen(screen)
    try:
        f=open(username,'r')
    except Exception:
        return failure_screen(screen)
    else:
        actual = f.readline().strip()
        rhythm=False
        match = actual==password
        if not match:
            return failure_screen(screen)
        else:
            rhythm = verify_vector(username, transform(current_kd,current_ku))
        return success_screen(screen) if rhythm else failure_screen(screen)

def transform(vector1, vector2):
    global pwd
    result=[]
    vector1=clean(vector1)
    vector2=clean(vector2,True)
    print("vector1 ",str(vector1))
    print("vector2 ",str(vector2))
    pwd = list(zip(*vector1))[0]
    hold = [vector2[i][1]-vector1[i][1] for i in range(len(vector1))]
    flight = [vector1[x+1][1]-vector2[x][1] for x in range(len(vector1)-1)]
    print('hold ',str(hold))
    print('flight ',str(flight))
    for x in range(len(vector1)-1):
        result.append(hold[x])
        result.append(flight[x])
    result.append(hold[len(vector1)-1])
    print('Password is: '+str(pwd))
    print('transformed vector is: '+str(result))
    return result

def save(fname, regscreen):
    if not fname:
        return reg_failure_screen(regscreen)
    f = open(fname,'w')
    f.write(''.join(pwd))
    f.close()
    f=open(fname+'.vector','w')
    f.write(str(classification_vector)+'\n')
    f.write(str((150*np.amax(get_inverse_cov(classification_vector)))**0.5))
    f.close()
    f=open(fname+'.vector-overlap','w')
    f.write(str(c_vector_overlap)+'\n')
    f.write(str((150*np.amax(get_inverse_cov( c_vector_overlap)))**0.5))
    f.close()
    f=open(fname+'.vector-miss','w')
    f.write(str(c_vector_undetected)+'\n')
    f.write(str((150*np.amax(get_inverse_cov(c_vector_undetected)))**0.5))
    f.close()
    regscreen.destroy()
    return

def register():
    global trained
    global tbutton
    global usr
    global tmsg
    regscr = Tk()
    regscr.title('Register')
    Message(regscr, text='').grid(row=0,columnspan=5)
    Label(regscr, text="Enter Username").grid(row=1, column=0,columnspan=1)
    usr = Entry(regscr)
    usr.grid(row=1, column=1, columnspan=3, padx=50)
    Label(regscr, text="Enter password").grid(row=2, column=0, columnspan=1)
    regpassword = Entry(regscr)
    regpassword.grid(row=2, column=1, columnspan=3, padx=50)
    regpassword.bind('<KeyPress>',keyd)
    regpassword.bind('<KeyRelease>',keyu)
    tbutton = Button(regscr, text="Train", command=lambda: train(regpassword, regscr))
    tbutton.grid(row=3, column=1, sticky=EW, padx=10,pady=10)
    tmsg = Label(regscr, text="Trainings completed (out of 10):"+str(trained))
    tmsg.grid(row=4, column=0,columnspan=5, sticky=EW)
    regscr.mainloop()
    return

def login_screen():
    screen = Tk()
    screen.title("Login")
    Message(screen, text='').grid(row=0,columnspan=10)
    Label(screen, text="Enter Username").grid(row=1, column=0,columnspan=1)
    username = Entry(screen)
    username.grid(row=1, column=1, columnspan=3, padx=50)
    Label(screen, text="Enter password").grid(row=2, column=0, columnspan=1)
    password = Entry(screen)
    password.grid(row=2, column=1, columnspan=3, padx=50)
    password.bind('<KeyPress>',keyd)
    password.bind('<KeyRelease>',keyu)
    Button(screen, text="Authenticate", command= lambda: authenticate(username.get(),password.get(),screen)).grid(row=5, column=1, sticky=EW, padx=10,pady=10)
    Label(screen, text='Not registered?').grid(row=6,column=0,sticky=E, columnspan=1, pady=1)
    Button(screen, text="Register", command=register).grid(row=6, column=1, sticky=N, pady=10)
    screen.mainloop()
    return

def success_screen(screen):
    screen.destroy()
    plt.gcf().canvas.set_window_title('Password and rhythm both verified for user: ' +usr+ '  LOGIN SUCCESSFUL')
    plt.title('Typing Rhythm - lines are training data, dots are current attempt')
    tmp=[plt.plot(x) for x in matrix]
    plt.plot(range(2*len(clean(current_kd))-1),transform(current_kd,current_ku),'ro')
    plt.xlabel('Series of Hold and Flight times \n(hold time of 1st char followed by flight time between 1st and 2nd char and so on..)')
    plt.ylabel('Duration (in milliseconds)')
    plt.show()
    return

def failure_screen(screen):
    screen.destroy()
    #fail=Tk()
    #fail.title('login failure')
    #Message(fail, text='Login Failed').grid(row=0, column=0, padx=50, pady=10)
    #Button(fail, text='Quit', command= fail.destroy).grid(row=2, column=0, padx=50, pady=10)
    plt.gcf().canvas.set_window_title('LOGIN FAILED for user: '+usr)
    plt.title('Typing Rhythm FAILED for user: ' +usr+ '- lines are training data, dots are current attempt')
    tmp=[plt.plot(x) for x in matrix]
    plt.plot(range(2*len(clean(current_kd))-1),transform(current_kd,current_ku),'ro')
    plt.xlabel('Series of Hold and Flight times \n(hold time of 1st char followed by flight time between 1st and 2nd char and so on..)')
    plt.ylabel('Duration (in milliseconds)')
    plt.show()
    send_email('failemail.txt')
    #fail.mainloop
    return

def reg_failure_screen(screen):
    screen.destroy()
    regfail=Tk()
    regfail.title('registration failure')
    Message(regfail, text='Registration Failed').grid(row=0, column=0, padx=50, pady=10)
    Button(regfail, text='Quit', command= regfail.destroy).grid(row=2, column=0, padx=50, pady=10)
    regfail.mainloop
    return

def send_email(filename):
    global usr
    f=open(filename,'r')
    gmail_user = f.readline().strip()
    gmail_pwd = f.readline().strip()
    FROM = gmail_user
    TO = f.readline().strip()
    SUBJECT = f.readline().strip()
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, TO, SUBJECT, usr+'\n'+f.readline().strip())
    try:
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.login(gmail_user, gmail_pwd)
        server_ssl.sendmail(FROM, TO, message)
        server_ssl.close()
        print('successfully sent the mail')
    except:
        print('couldn\'t send mail')

login_screen()
