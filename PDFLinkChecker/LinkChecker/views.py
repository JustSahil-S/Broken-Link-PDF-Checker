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
def index(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links.objects.filter(~Q(dismiss=True), ~Q(ignore = True))
    })
def dismiss(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links.objects.filter(dismiss=True)
    })
def ignore(request):
    return render(request, "LinkChecker/index.html", {
        "links":Links.objects.filter(ignore=True)
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

def update(request):
    urls = []
    dead_urls = []                                                            
    for file in list(glob.glob('/Users/sahilsingamsetty/work/openai/web-crawl-q-n-a/apps/web-crawl-q-and-a/pdf/www.php.com/*')):     
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
                    x = 10 #
                    linkText = page.get_textbox(link["from"] + (-x, -1, x, 1))
                    response = requests.head(url, allow_redirects=True)
                    final_url = response.url
                    if (final_url != url):
                        urls.append(url+" (final url:"+final_url+")")
                    else:
                        urls.append(url)
                    if response.status_code != 200:
                        if response.status_code in [301, 302]:
                            redirected_response = requests.head(final_url)
                            if redirected_response.status_code != 200:
                                dead_urls.append({ "url" : url+"(final_url:"+final_url+")", "status_code" : redirected_response.status_code, "reason": redirected_response.reason+'(redirected)'})
                                if Links.objects.get(url = url):
                                    obj = Links.objects.get(url = url)
                                    if obj.dismiss == True and obj.statusCode != redirected_response.status_code:
                                        obj.statusCode = redirected_response.status_code
                                        obj.lastChecked = datetime.now()
                        else: 
                            dead_urls.append({ "url" : url, "status_code" : response.status_code, "reason": response.reason})
                            if Links.objects.filter(url = url).exists() == False:
                                Links.objects.create(
                                    url = url,
                                    statusCode = response.status_code,
                                    pdfSource = pdf,
                                    finalurl = url,
                                    dismiss = False,
                                    ignore = False,
                                    lastChecked = datetime.datetime.now(),
                                    urlText = linkText,
                                )
            print(dead_urls)
            print(urls)
            doc.close()
    print("done")
    return HttpResponseRedirect("/")