from django.shortcuts import render
from django.db.utils import OperationalError
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
import os  
#import pandas as pd
from django.db.models import Q
import openpyxl
import smtplib,ssl
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from http.client import responses

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
            print(f'        Found url:{url}')
            if (url in uniqueLinks):
                uniqueLinks[url]['moreInPdf'] = True
                continue  # pick only the first
            else:
                uniqueLinks[url] = {"moreInPdf":False}
                boundingBox = 10 
                uniqueLinks[url]["linkText"] = page.get_textbox(link["from"] + (-boundingBox, -1, boundingBox, 1))
                print(f'        unique_links: {uniqueLinks}')
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
    print(f'Processing iteration #{curIteration}')
    pdfs = get_all_pdfs()

    for pdf in pdfs:
        if (os.path.isdir(pdf)):
            continue
        print(f'  Processing file {pdf}')

        links = get_all_links(pdf)

        for link in links:
            print(f'    Processing url:{link}')
            linkObjs = Links_table.objects.filter(url=link)

            if (len(linkObjs) == 0):
                #there are no objects with this link
                statusCode, reason, finalUrl = make_request(link)
                print('      statusCode:{statusCode}, reason:{reason}, finalUrl:{finalUrl}')
                newObj = Links_table.objects.create(url=link, statusCode=statusCode, reason=reason, pdfSource=pdf,finalUrl=finalUrl, 
                    lastChecked=datetime.datetime.now(), urlText=links[link]["linkText"],moreInPdf=links[link]["moreInPdf"],lastIteration=curIteration)
                if (statusCode != 200):
                    newObj.broken = True
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
            print('      statusCode:{statusCode}, reason:{reason}, finalUrl:{finalUrl}')
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
                Links_table.objects.filter(url=link).update(lastIteration=curIteration, lastChecked=datetime.datetime.now())
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
                    lastChecked=datetime.datetime.now())
        # processed all links
    # processed all pdfs
    #delete all stale links
    Links_table.objects.filter(lastIteration__lt=curIteration).delete()
    globals.iteration = curIteration
    globals.save()


def checkall(request):
    checkall_links()

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

             

                

#/Users/sahilsingamsetty/work/openai/web-crawl-q-n-a/apps/web-crawl-q-and-a/pdf/www.php.com/*'
def update(request):
    urls = []
    dead_urls = []  
    try:
        past_iteration = Links.objects.all().first().iteration  # MS: Why is the global iteration is stored as part of link record?
    except:
        past_iteration = 1
    cur_iteration = past_iteration + 1                                                           
    for file in list(glob.iglob('./pdf/*', recursive=True)):   
        if (os.path.isdir(file)):
            continue  
        print(file)
        doc = fitz.open(file)
        pdf = file
        for page_num in range(doc.page_count):
            try: 
                page = doc.load_page(page_num)
            except:
                continue
            links = page.get_links()
            for link in links:
                if (link["kind"] == fitz.LINK_URI and (not link["uri"].startswith('mailto'))):
                    url = link["uri"]
                    boundingBox = 10 
                    linkText = page.get_textbox(link["from"] + (-boundingBox, -1, boundingBox, 1))
                    #Tries to get the URL, if it can't, assume an error with the link and it adds the link to the records via except
                    try: 
                        response = requests.head(url, allow_redirects=True) # MS: You should check ignore state before making request!  
                        final_url = response.url
                        if (final_url != url):
                            urls.append(url+" (final url:"+final_url+")")
                        else:
                            urls.append(url)
                        #If link is dimissed or already broken then it will do a recheck and update the data. If it's working then it will delete from records.
                        if Links.objects.filter(url = url, pdfSource = pdf).exists():
                            obj = Links.objects.get(url = url)   # MS: can it be from different pdf? as you are not using pdf to get the link!
                            obj.iteration = cur_iteration
                            obj.save() 
                            if not obj.ignore:
                                #if its 200(OK), deletes from records
                                if response.status_code == 200:
                                    obj.delete()  # MS: should we, instead keep it?
                                #if its dimissed, check if status changes and update if true
                                elif obj.dismiss:
                                    try: 
                                        reason = responses[response.status_code]
                                    except:
                                        #response.status_code = 500
                                        reason = 'unknown'
                                    if (obj.statusCode != response.status_code or obj.finalurl != final_url):
                                        obj.statusCode = response.status_code
                                        obj.reason = reason
                                        obj.dismiss = False 
                                        obj.finalurl = final_url  
                                        obj.lastChecked = datetime.datetime.now()
                                        obj.iteration = cur_iteration
                                        obj.save()
                                    else:
                                        obj.lastChecked = datetime.datetime.now()
                                        obj.iteration = cur_iteration
                                        obj.save()
                                #If its already broken, update the record
                                else:
                                    try: 
                                        reason = responses[response.status_code]
                                    except:
                                        #response.status_code = 500
                                        reason = 'unknown'
                                    obj.statusCode = response.status_code 
                                    obj.reason = reason
                                    obj.finalurl = final_url  
                                    obj.lastChecked = datetime.datetime.now()
                                    obj.iteration = cur_iteration
                                    obj.save()
                        #Checks for new broken links that aren't in the system
                        elif response.status_code != 200:
                            if response.status_code in [301, 302]:
                                redirected_response = requests.head(final_url)
                                if redirected_response.status_code != 200:
                                    dead_urls.append({ "url" : url+"(final_url:"+final_url+")", "status_code" : redirected_response.status_code, "reason": redirected_response.reason+'(redirected)'})
                            else: 
                                dead_urls.append({ "url" : url, "status_code" : response.status_code, "reason": response.reason})
                                if Links.objects.filter(url = url).exists() == False:
                                    try:
                                        reason = responses[response.status_code]
                                    except:
                                        #response.status_code = 500
                                        reason = 'unknown'

                                    Links.objects.create(
                                        url = url,
                                        statusCode = response.status_code,
                                        reason = reason,
                                        pdfSource = pdf,
                                        finalurl = url,
                                        dismiss = False,
                                        ignore = False,
                                        lastChecked = datetime.datetime.now(),
                                        urlText = linkText,
                                        iteration = cur_iteration
                                    )
                    except:
                        dead_urls.append({ "url" : url, "status_code" : 500, "reason": responses[500]})
                        if Links.objects.filter(url = url).exists() == False:
                            Links.objects.create(
                                url = url,
                                statusCode = 500,
                                reason = responses[500],
                                pdfSource = pdf,
                                finalurl = url,
                                dismiss = False,
                                ignore = False,
                                lastChecked = datetime.datetime.now(),
                                urlText = linkText,
                                iteration = cur_iteration
                            )
            Links.objects.filter(iteration = past_iteration).delete()
            print(dead_urls)
            print(urls)
            print(past_iteration)
            print(cur_iteration)
            doc.close()
    

    # Create a new Excel workbook
    workbook = openpyxl.Workbook()
    # Select the default sheet (usually named 'Sheet')
    sheet = workbook.active
    # Add data to the Excel sheet
    data = [
        ["URL", "Status", "PDF"]]
    for link in Links.objects.filter(dismiss = False, ignore = False):
        row = [link.url, link.statusCode, link.reason, link.pdfSource]
        data.append(row)
        print(data)
    for row in data:
        sheet.append(row)
    # Save the workbook to a file
    workbook.save("UpdateSheet.xlsx")
    # Print a success message
    print("Excel file created successfully!")


    # msg = MIMEMultipart()
    # sender='murali.singamsetty@gmail,com'
    # recipients='karkidmc@gmail.com'
    # server=smtplib.SMTP('smtp.gmail.com', 587)
    # server.starttls()
    # server.login("murali.singamsetty@gmail.com", "ysxyoczkwjzmswiu")
    # msg['Subject']='Broken Link Checker'
    # msg['From']=sender
    # msg['To']=recipients
    # filename = r'/Users/sahilsingamsetty/work/PHP/Broken Link PDF Checker /PDFLinkChecker/UpdateSheet.xlsx'
    # attachment = open(r'/Users/sahilsingamsetty/work/PHP/Broken Link PDF Checker /PDFLinkChecker/UpdateSheet.xlsx', 'rb')
    # xlsx = MIMEBase('application','vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # xlsx.set_payload(attachment.read())
    # encoders.encode_base64(xlsx)
    # xlsx.add_header('Content-Disposition', 'attachment', filename="Broken Links")
    # msg.attach(xlsx)
    # server.sendmail(sender, recipients, msg.as_string())
    # server.quit()
    # attachment.close()


    return HttpResponseRedirect("/")



# dict = {
# "100":"CONTINUE",
# "101":"SWITCHING_PROTOCOLS",
# "102":"PROCESSING",
# "103":"EARLY_HINTS",
# "200":"OK",
# "201":"CREATED",
# "202":"ACCEPTED",
# "203":"NON_AUTHORITATIVE_INFORMATION",
# "204":"NO_CONTENT",
# "205":"RESET_CONTENT",
# "206":"PARTIAL_CONTENT",
# "207":"MULTI_STATUS",
# "208":"ALREADY_REPORTED",
# "226":"IM_USED",
# "300":"MULTIPLE_CHOICES",
# "301":"MOVED_PERMANENTLY",
# "302":"FOUND",
# "303":"SEE_OTHER",
# "304":"NOT_MODIFIED",
# "305":"USE_PROXY",
# "307":"TEMPORARY_REDIRECT",
# "308":"PERMANENT_REDIRECT",
# "400":"BAD_REQUEST",
# "401":"UNAUTHORIZED",
# "402":"PAYMENT_REQUIRED",
# "403":"FORBIDDEN",
# "404":"NOT_FOUND",
# "405":"METHOD_NOT_ALLOWED",
# "407":"NOT_ACCEPTABLE",
# "408":"PROXY_AUTHENTICATION_REQUIRED",
# "409":"REQUEST_TIMEOUT",
# "410":"CONFLICT",
# "411":"GONE",
# "412":
# "413":
# "414":
# "415":
# "416":
# "417":
# "418":
# "421":
# "422":
# "423":
# "424":
# "425":
# "426":
# "428":
# "429":
# "431":
# "451":
# "500":
# "501":
# "502":
# "503":
# "504":
# "505":
# "506":
# "507":
# "508":
# "510":
# "511":"NETWORK_AUTHENTICATION_REQUIRED"}


















# "NOT_ACCEPTABLE",
# "PROXY_AUTHENTICATION_REQUIRED",
# "REQUEST_TIMEOUT",
# "CONFLICT",
# "GONE",
# "LENGTH_REQUIRED",
# "PRECONDITION_FAILED",
# "REQUEST_ENTITY_TOO_LARGE",
# "REQUEST_URI_TOO_LONG",
# "UNSUPPORTED_MEDIA_TYPE",
# "REQUESTED_RANGE_NOT_SATISFIABLE",
# "EXPECTATION_FAILED",
# "IM_A_TEAPOT",
# "MISDIRECTED_REQUEST",
# "UNPROCESSABLE_ENTITY",
# "LOCKED",
# "FAILED_DEPENDENCY",
# "TOO_EARLY",
# "UPGRADE_REQUIRED",
# "PRECONDITION_REQUIRED",
# "TOO_MANY_REQUESTS",
# "REQUEST_HEADER_FIELDS_TOO_LARGE",
# "UNAVAILABLE_FOR_LEGAL_REASONS",
# "INTERNAL_SERVER_ERROR",
# "NOT_IMPLEMENTED",
# "BAD_GATEWAY",
# "SERVICE_UNAVAILABLE",
# "GATEWAY_TIMEOUT",
# "HTTP_VERSION_NOT_SUPPORTED",
# "VARIANT_ALSO_NEGOTIATES",
# "INSUFFICIENT_STORAGE",
# "LOOP_DETECTED",
# "NOT_EXTENDED",
