from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.http import HttpResponse
from .models import Links
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

def index(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links.objects.filter(~Q(dismiss=True), ~Q(ignore = True)),
        "brokenCount":Links.objects.filter(~Q(dismiss=True), ~Q(ignore = True)).count(),
        "dismissCount":Links.objects.filter(dismiss=True).count(),
        "ignoreCount":Links.objects.filter(ignore=True).count(),
    })
def dismiss(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links.objects.filter(dismiss=True),
        "brokenCount":Links.objects.filter(~Q(dismiss=True), ~Q(ignore = True)).count(),
        "dismissCount":Links.objects.filter(dismiss=True).count(),
        "ignoreCount":Links.objects.filter(ignore=True).count(),
    })
def ignore(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links.objects.filter(ignore=True),
        "brokenCount":Links.objects.filter(~Q(dismiss=True), ~Q(ignore = True)).count(),
        "dismissCount":Links.objects.filter(dismiss=True).count(),
        "ignoreCount":Links.objects.filter(ignore=True).count(),
    })

@csrf_exempt
def dismissAction(request, id):
    obj = Links.objects.get(id = id)
    obj.dismiss = True
    obj.ignore = False
    obj.save()
    return HttpResponse(status=200)
@csrf_exempt
def ignoreAction(request, id):
    obj = Links.objects.get(id = id)
    obj.ignore = True
    obj.dismiss = False
    obj.save()
    return HttpResponse(status=200)
@csrf_exempt
def brokenAction(request, id):
    obj = Links.objects.get(id = id)
    obj.ignore = False
    obj.dismiss = False
    obj.save()
    return HttpResponse(status=200)
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
                    linkText = page.get_textbox(link["from"] + (-boundingBox -1, boundingBox, 1))
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
                                        response.status_code = 500
                                        reason = responses[response.status_code]
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
                                        response.status_code = 500
                                        reason = responses[response.status_code]
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
                                        response.status_code = 500
                                        reason = responses[response.status_code]

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
