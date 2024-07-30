from django.shortcuts import render
from django.db.utils import OperationalError
import pytz
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse
from .models import Links, Globals, Links_table, CheckLinkResult
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import fitz
import requests
import glob
import datetime
import time
import os  
#import pandas as pd
from django.db.models import Q
import openpyxl
import smtplib,ssl
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from http.client import responses

PST = pytz.timezone('US/Pacific')
checkallLock = threading.Lock()

try:
    if (Globals.objects.all().count() == 0):
        Globals.objects.create(iteration=0, pdfDirectory="./pdf")

    globals = Globals.objects.first()
except: 
    pass  # happens when db doesn't exist yet, views.py should be
          # importable without this side effect

def broken(request):
    return render(request, "LinkChecker/index.html", {
        #"links":Links_table.objects.filter(~Q(dismiss=True), ~Q(ignore = True)),
        "links":Links_table.objects.filter(broken=True),
        "allCount":Links_table.objects.all().count(),
        "brokenCount":Links_table.objects.filter(broken=True).count(),
        "dismissCount":Links_table.objects.filter(dismiss=True).count(),
        "ignoreCount":Links_table.objects.filter(ignore=True).count(),
    })

def all(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links_table.objects.all(),
        "allCount":Links_table.objects.all().count(),
        "brokenCount":Links_table.objects.filter(broken=True).count(),
        "dismissCount":Links_table.objects.filter(dismiss=True).count(),
        "ignoreCount":Links_table.objects.filter(ignore=True).count(),
    })


def index(request):
    return broken(request)

def dismiss(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links_table.objects.filter(dismiss=True),
        "allCount":Links_table.objects.all().count(),
       "brokenCount":Links_table.objects.filter(broken=True).count(),
        "dismissCount":Links_table.objects.filter(dismiss=True).count(),
        "ignoreCount":Links_table.objects.filter(ignore=True).count(),
    })
def ignore(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links_table.objects.filter(ignore=True),
        "allCount":Links_table.objects.all().count(),
        "brokenCount":Links_table.objects.filter(broken=True).count(),
        "dismissCount":Links_table.objects.filter(dismiss=True).count(),
        "ignoreCount":Links_table.objects.filter(ignore=True).count(),
    })

@csrf_exempt
def dismissAction(request, id):
    obj = Links_table.objects.get(id = id)
    #obj.dismiss = True
    #obj.ignore = False
    #obj.save()
    Links_table.objects.filter(url=obj.url).update(dismiss=True,ignore=False);
    return HttpResponse(status=200)
@csrf_exempt
def ignoreAction(request, id):
    obj = Links_table.objects.get(id = id)
    #obj.ignore = True
    #obj.dismiss = False
    #obj.save()
    Links_table.objects.filter(url=obj.url).update(dismiss=False,ignore=True);
    return HttpResponse(status=200)
""" @csrf_exempt
def brokenAction(request, id):
    obj = Links_table.objects.get(id = id)
    obj.ignore = False
    obj.dismiss = False
    obj.save()
    return HttpResponse(status=200)
 """
def get_all_pdfs():
    # TODO: handle multiple directories
    return list(glob.iglob(globals.pdfDirectory+"/*.pdf", recursive=True))

def get_first_link_instance(check_link, pdf):
    timesSeen = 0
    urlAnchor = ""
    doc = fitz.open(pdf)
    for page_num in range(doc.page_count):
        try: 
            page = doc.load_page(page_num)
        except:
            continue
    links = page.get_links()
    for link in links:
        if (link["kind"] == fitz.LINK_URI and (not link["uri"].startswith('mailto'))):
            url = link["uri"]
            if (url == check_link):
                timesSeen += 1
                if timesSeen == 1:
                    boundingBox = 10 
                    urlAnchor = page.get_textbox(link["from"] + (-boundingBox, -1, boundingBox, 1))
            if timesSeen == 2:
                break
            else:
                continue
        continue
    return timesSeen > 0, urlAnchor, timesSeen > 1

def get_all_links(pdf):
    # if multiple instances of a link exist, pick only the first and set moreInPdf to True
    uniqueLinks = {}
    doc = fitz.open(pdf)
    for page_num in range(doc.page_count):
        try: 
            page = doc.load_page(page_num)
        except:
            continue
    links = page.get_links()
    for link in links:
        if (link["kind"] == fitz.LINK_URI and (not link["uri"].startswith('mailto'))):
            url = link["uri"]
            # print(f'        Found url:{url}')
            if (url in uniqueLinks):
                uniqueLinks[url]['moreInPdf'] = True
                continue  # pick only the first
            else:
                uniqueLinks[url] = {"moreInPdf":False}
                boundingBox = 10 
                uniqueLinks[url]["linkText"] = page.get_textbox(link["from"] + (-boundingBox, -1, boundingBox, 1))
                # print(f'        unique_links: {uniqueLinks}')
                # TODO: if link anchor is an image, set linkText as "<image>"

    return uniqueLinks

def make_request(url):
    # TODO use proper request header and try different header options
    # TODO collect logs
    try: 
        response = requests.head(url, allow_redirects=True)   
    except:
        return 500, 'Internal Server Error', url
    
    final_url = response.url
    if (response.status_code != 200):
        if (response.status_code in [301, 302]):
            redirected_response = requests.head(final_url)
            if (redirected_response.status_code != 200):
                return redirected_response.status_code, redirected_response.reason, final_url

    return response.status_code, response.reason, response.url

def checkall_links():
    curIteration = globals.iteration + 1
    newBrokenLinksFound = False
    print(f'Processing iteration #{curIteration}')
    pdfs = get_all_pdfs()

    for pdf in pdfs:
        if (os.path.isdir(pdf)):
            continue
        # print(f'  Processing file {pdf}')
        print('+', end="", flush=True)
        links = get_all_links(pdf)

        for link in links:
            # print(f'    Processing url:{link}')
            print('.', end="", flush=True)
            linkObjs = Links_table.objects.filter(url=link)

            if (len(linkObjs) == 0):
                #there are no objects with this link
                statusCode, reason, finalUrl = make_request(link)
                # print(f'      statusCode:{statusCode}, reason:{reason}, finalUrl:{finalUrl}')
                newObj = Links_table.objects.create(url=link, statusCode=statusCode, reason=reason, pdfSource=pdf,finalUrl=finalUrl, 
                    lastChecked=datetime.datetime.now(PST),brokenSince=datetime.datetime.now(PST),urlText=links[link]["linkText"],moreInPdf=links[link]["moreInPdf"],lastIteration=curIteration)
                if (statusCode != 200):
                    newObj.broken = True
                    newBrokenLinksFound = True
                    newObj.brokenSince = newObj.lastChecked
                else:
                    newObj.broken = False
                newObj.save()
                continue  # to next link

            try:
                thisPdfObj = Links_table.objects.get(url=link, pdfSource=pdf)
            except:
                thisPdfObj = None
            
            if (thisPdfObj == None):
                linkObjsProcessed = linkObjs.filter(lastIteration__gte=curIteration)
                if (len(linkObjsProcessed) > 0):
                    # create new obj for this pdf with the same state at already processed
                    #already processed this link
                    linkObjsProcessed[0].pk = None
                    linkObjsProcessed[0]._state.adding = True
                    linkObjsProcessed[0].pdfSource = pdf
                    linkObjsProcessed[0].urlText=links[link]["linkText"]
                    linkObjsProcessed[0].moreInPdf=links[link]["moreInPdf"]
                    linkObjsProcessed[0].save()
                    continue # to next link
                """ else :
                    linkObjs[0].pk = None
                    linkObjs[0]._state.adding = True
                    linkObjs[0].pdfSource = pdf
                    linkObjs[0].urlText=links[link]["linkText"]
                    linkObjs[0].moreInPdf=links[link]["moreInPdf"]
                    linkObjs[0].save()
                continue # to next link """
            else:
                thisPdfObj.urlText = links[link]["linkText"]
                thisPdfObj.moreInPdf = links[link]["moreInPdf"]
                thisPdfObj.save();
        
            if (linkObjs.filter(ignore=True).count() > 0):
                if (thisPdfObj == None):
                    linkObjs[0].pk = None
                    linkObjs[0]._state.adding = True
                    linkObjs[0].pdfSource = pdf
                    linkObjs[0].urlText=links[link]["linkText"]
                    linkObjs[0].moreInPdf=links[link]["moreInPdf"]
                    linkObjs[0].save()
                Links_table.objects.filter(url=link).update(ignore=True, lastIteration=curIteration)
                continue  # to next link

            statusCode, reason, finalUrl = make_request(link)
            # print(f'      statusCode:{statusCode}, reason:{reason}, finalUrl:{finalUrl}')
            if (linkObjs.filter(statusCode=statusCode).exists()):
                if (thisPdfObj == None):
                    linkObjs[0].pk = None
                    linkObjs[0]._state.adding = True
                    linkObjs[0].pdfSource = pdf
                    linkObjs[0].urlText=links[link]["linkText"]
                    linkObjs[0].moreInPdf=links[link]["moreInPdf"]
                    linkObjs[0].status = statusCode
                    linkObjs[0].reason = reason
                    linkObjs[0].finalUrl = finalUrl
                    linkObjs[0].save()
                Links_table.objects.filter(url=link).update(lastIteration=curIteration, lastChecked=datetime.datetime.now(PST))
            else:
                for obj in linkObjs:
                    if (statusCode != 200):
                        obj.broken = true
                        if (obj.status == 200):
                            obj.broken_since = obj.last_checked
                    else: 
                        obj.broken = false
                    obj.dismiss = false #exit out of dismissed state
                    obj.save()

                if (thisPdfObj == None):
                    obj.pk = None
                    obj._state.adding = True
                    obj.pdfSource = pdf
                    obj.urlText=links[link]["linkText"]
                    obj.moreInPdf=links[link]["moreInPdf"]
                    obj.save()
                Links_table.objects.filter(url=link).update(statusCode=statusCode,reason=reason,finalUrl=finalUrl,lastIteration=curIteration, 
                    lastChecked=datetime.datetime.now(PST))
        # processed all links
    # processed all pdfs
    print(' Done!')
    #delete all stale links
    Links_table.objects.filter(lastIteration__lt=curIteration).delete()
    globals.iteration = curIteration
    globals.save()

    if (globals.emailNotifyOnNewLink and newBrokenLinksFound):
        print(f'sending email')
        if (globals.attachListToEmail):
            print(f'preparing attachment')
            attachmentFile = "PDFBrokenLinks.xlsx"
            # Create a new Excel workbook
            workbook = openpyxl.Workbook()
            # Select the default sheet (usually named 'Sheet')
            sheet = workbook.active
            # Add data to the Excel sheet
            data = [["URL", "Status Code", "Status Reason", "PDF Source"]] #top row
            for link in Links_table.objects.filter(broken=True):
                row = [link.url, link.statusCode, link.reason, link.pdfSource]
                data.append(row)
                #print(data)
            for row in data:
                sheet.append(row)
            # Save the workbook to a file
            workbook.save(attachmentFile)
            # Print a success message
            print("Excel file created successfully!")

        # send e-mail
        msg = MIMEMultipart()
        sender='murali.singamsetty@gmail,com'
        recipients= globals.emailAddress
        server=smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("murali.singamsetty@gmail.com", "ysxyoczkwjzmswiu")
        msg['Subject']='PDF Broken Link Report'
        msg['From']=sender
        msg['To']=recipients
        mail_body = """\
            This is an automated report, sent from PDF Broken Link Checker.
            
            To disable email notifications, see click Settings on PDF Broken Link Checker

            """
        msg.attach(MIMEText(mail_body, "plain"))
        if (globals.attachListToEmail):
            print(f'adding attachment to email')
            attachment = open(attachmentFile, 'rb')
            xlsx = MIMEBase('application','vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            xlsx.set_payload(attachment.read())
            encoders.encode_base64(xlsx)
            xlsx.add_header('Content-Disposition', 'attachment', filename="Broken PDF Links")
            msg.attach(xlsx)
        
        server.sendmail(sender, recipients, msg.as_string())
        print(f'sent email')
        server.quit()
        if (globals.attachListToEmail):
            attachment.close()


def bgnd_task():

    while True:
        print('background task: acquiring lock')
        checkallLock.acquire(blocking=1)
        print(f'background task: got lock, processing at {datetime.datetime.now(PST)}')
        checkall_links()
        print('background task: releasing lock')
        checkallLock.release()
        next_at = datetime.datetime.now(PST)
        while (True):
            next_at = datetime.datetime(year=next_at.year, month=next_at.month, day=next_at.day, 
                        hour=globals.checkAllStartAtHour, minute=globals.checkAllStartAtMin).replace(tzinfo=PST) + datetime.timedelta(hours=globals.checkAllIntervalHours, 
                        minutes=globals.checkAllIntervalMins)

            if (next_at > datetime.datetime.now(PST)):
                break
            next_at += datetime.timedelta(hours=globals.checkAllIntervalHours, minutes=globals.checkAllIntervalMins)

        print(f'background task: scheduled to run again at {next_at}')
        total_seconds = (next_at - datetime.datetime.now(PST)).total_seconds()
        time.sleep(total_seconds)


def checkall(request):
    print('checkall request: acquiring lock')
    checkallLock.acquire(blocking=1)
    print(f'checkall request: got lock, processing at {datetime.datetime.now(PST)}')
    checkall_links()
    print('checkall request: releasing lock')
    checkallLock.release()
    return HttpResponseRedirect("/")


@csrf_exempt
def recheckAction(request, id):
    try:
        Obj = Links_table.objects.get(id = id)
    except:
        result =  CheckLinkResult.NO_SUCH_LINK.value
        print(f'Record for is {id} not found!')
        return JsonResponse({"result": result, "statusChanged": False, "delete": True})

    link = Obj.url
    pdf = Obj.pdfSource

    # does pdf still exist?
    if (os.path.isfile(pdf) == False):
        Obj.delete()
        result =  CheckLinkResult.NO_SUCH_PDF.value
        print(f'pdf:{pdf} not found!')
        return JsonResponse({"result": result, "statusChanged": False, "delete": True})

    # process the pdf to check if link still exists
    found, urlAnchor, moreInPdf = get_first_link_instance(link, pdf)
    if (found == False):
        Obj.delete()
        result =  CheckLinkResult.NO_SUCH_LINK.value
        print(f'url:{link} not found in pdf:{pdf}!')
        return JsonResponse({"result": result, "statusChanged": False, "delete": True})

    statusCode, reason, finalUrl = make_request(link)
 
    if (statusCode == 200):
        if (Obj.statusCode != statusCode):
            Obj.statusCode = statusCode
            Obj.broken = False
            Obj.dismiss = False
            Obj.ignore = False
            Obj.urlText = urlAnchor
            Obj.moreInPdf = moreInPdf
            Obj.save()
            return JsonResponse({"result": CheckLinkResult.LINK_OK.value, "statusChanged": True, "delete": False})
        return JsonResponse({"result": CheckLinkResult.LINK_OK.value, "statusChanged": False, "delete": False})
    else:
        if (Obj.statusCode != statusCode):
            Obj.dismiss = False
            Obj.broken = True
            Obj.statusCode = statusCode
            Obj.urlText = urlAnchor
            Obj.moreInPdf = moreInPdf
            Obj.save()
            result =  CheckLinkResult.LINK_BROKEN_STATUS_CHANGED.value
            return JsonResponse({"result": result, "statusChanged": True, "delete": False})
        result =  CheckLinkResult.LINK_BROKEN_SAME_STATUS.value
    # send response back with result 
    # result = one of (pdf does not exist, link does not exist, link ok, link broken same status, link broken status changed
    return JsonResponse({"result": result, "statusChanged": False, "delete": False})

