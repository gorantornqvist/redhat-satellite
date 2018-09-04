#!/bin/python
# This script uses the Satellite API to generate different HTML reports like below example reports:
#
# * hosts_by_usergroup (You need to assign User Groups as owner to hosts for this)
# * hosts_by_lifecycle_environment
# * hosts_by_environment
# * hosts_by_model
# * hosts_by_domain
# * hosts_by_operatingsystem
# * hosts_by_fact_java_version
# * hosts_by_fact_uptime_days
# * hosts_by_fact_selinux_current_mode
# * hosts_by_hypervisor
# * hosts_by_myparam (Add a global parameter with a comma seperated list of valid values and group hosts by host parameter)
# * hosts_by_errata_critical_applicable
# * hosts_by_errata_critical_installable
#
# Example usage: satellite-report-html.py hosts_by_lifecycle_environment >/var/www/html/pub/reports/hosts_by_lifecycle_environment.html
#
# Add a new report by just copying one of the functions for example reports to the bottom of this script
# 
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()
import json
import sys, getopt
import os
import fnmatch
import datetime
import urllib

SAT_SERVER = 'mysatellite'
SAT_API = 'https://' + SAT_SERVER + '/api/v2/'
KAT_API = 'https://' + SAT_SERVER + '/katello/api/v2/' 
USERNAME = "myuser"
PASSWORD = "mypassword"
SSL_VERIFY = "/etc/rhsm/ca/katello-server-ca.pem"
POST_HEADERS = {'content-type': 'application/json'}

def print_html_header():
   html_header = '''
<html>
<head>
<style>
button.accordion {
    background-color: #eee;
    color: #444;
    cursor: pointer;
    padding: 18px;
    width: 100%;
    border: none;
    text-align: left;
    outline: none;
    font-size: 15px;
    transition: 0.4s;
}

button.accordion.active, button.accordion:hover {
    background-color: #ccc;
}

button.accordion:after {
    content: "\\002B";
    color: #777;
    font-weight: bold;
    float: right;
    margin-left: 5px;
}

button.accordion.active:after {
    content: "\\2212";
}

div.panel {
    padding: 0 18px;
    background-color: white;
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.2s ease-out;
}
</style>

</head>
<body>
'''
   print html_header

def print_html_footer():
   html_footer_1 = '''
<script>
var acc = document.getElementsByClassName("accordion");
var i;

for (i = 0; i < acc.length; i++) {
  acc[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var panel = this.nextElementSibling;
    if (panel.style.maxHeight){
      panel.style.maxHeight = null;
    } else {
      panel.style.maxHeight = panel.scrollHeight + "px";
    }
  });
}
</script>
'''
   print html_footer_1
   now = datetime.datetime.now()
   print '<i>' + now.strftime('Generated at %Y-%m-%d %H:%M') + '</i>'
   html_footer_2 = '''
</body>
</html>
'''
   print html_footer_2


def post_json(location, json_data):
    """
    Performs a POST and passes the data to the URL location
    """
    result = requests.post(
        location,
        json=json_data,
        auth=(USERNAME, PASSWORD),
        verify=SSL_VERIFY,
        headers=POST_HEADERS).json()
    
    if result.get('error'):
        print("Error: ")
        print(result) #['error']['message']
    else:
        return result

    return None 

def get_json(url):
    # Performs a GET using the passed URL location
    r = requests.get(url, auth=(USERNAME, PASSWORD), verify=SSL_VERIFY)
    return r.json()

def get_results(url):
    """
    Performs a GET and returns the data / error message
    """
    jsn = get_json(url)
    if jsn.get('error'):
        print "Error: " + jsn['error']['message']
    else:
        if jsn.get('results'):
            return jsn['results']
        elif 'results' not in jsn:
            return jsn
    return None


def list_items(url,item_name="name"):
   """
   List an element ('name' is the default, can be 'id', 'title' and more) of all the items of a specific url location
   """
   result = get_results(url)
   item_list = []
   if result is None:
       return ['']
   for item in result:
       item_list.append(str(unicode(item[item_name])))
   return item_list

def check_exists(location):
    """
    Check existance of an element in the Satellite
    """
    if list_items(location,'id') != ['']:
        return True
    else:
        return False

# EXAMPLE REPORTS START HERE

def hosts_by_usergroup():

   usergroups=get_results(SAT_API+'usergroups')

   my_usergroups = []
   for usergroup in usergroups:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=owner_type%20%3D%20Usergroup%20and%20owner_id%20%3D%20'+str(usergroup['id']),'name')
      my_usergroups.append(str(usergroup['id']))
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + usergroup['name'].encode('utf-8') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

   # hosts assigned to other owners than User Groups

   # exclude virt-who hosts
   searchstr="name%20%21~%20virt-who%25%20"
   for my_usergroup in my_usergroups:
      searchstr+="%20and%20owner_id%20%21%3D%20" + my_usergroup  + "%20"
   
   host_list_unassigned=list_items(SAT_API+'hosts?per_page=1000&search='+searchstr,'name')
   if any(host_list_unassigned):
      item_count=str(len(host_list_unassigned))
   else:
      item_count="0"
   print "<button class='accordion'>Unassigned (" + item_count  + ")</button>"
   print "<div class='panel'>"
   for host_unassigned in host_list_unassigned:
     print "<a href='https://" + SAT_SERVER + "/hosts/" + host_unassigned + "'>" + host_unassigned + "</a><br/>"
   print "</div>"

def hosts_by_lifecycle_environment():

   lifecycle_environments=get_results(KAT_API+'environments?organization_id=1')

   for lifecycle_environment in lifecycle_environments:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=lifecycle_environment%20%3D%20'+str(lifecycle_environment['name']),'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + lifecycle_environment['name'].encode('utf-8') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_environment():

   environments=get_results(SAT_API+'environments')

   for environment in environments:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=environment%20%3D%20'+str(environment['name']),'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + environment['name'].encode('utf-8') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_model():

   models=get_results(SAT_API+'models')

   for model in models:
      model_name = { 'model' : '"' + str(model['name']) + '"'}
      model_urlencoded = urllib.urlencode(model_name)
      host_list=list_items(SAT_API+'hosts?per_page=1000&search='+model_urlencoded,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + model['name'].encode('utf-8') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_domain():

   domains=get_results(SAT_API+'domains')

   for domain in domains:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=domain%20%3D%20'+str(domain['name']),'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + domain['name'].encode('utf-8') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_operatingsystem():

   operatingsystems=get_results(SAT_API+'operatingsystems')

   for operatingsystem in operatingsystems:
      os_name = { 'os_title' : '"' + str(operatingsystem['title']) + '"'}
      os_urlencoded = urllib.urlencode(os_name)
      host_list=list_items(SAT_API+'hosts?per_page=1000&search='+os_urlencoded,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + operatingsystem['title'].encode('utf-8') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_fact_java_version():

   fact_values=get_results(SAT_API+'fact_values?per_page=1000&search=fact+%3D+java_version')
   java_versions = []
   for k1, v1 in fact_values.iteritems():
      for k2, v2 in v1.iteritems():
         if v2 not in java_versions:
            java_versions.append(v2)

   for java_version in java_versions:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.java_version%20%3D%20'+java_version,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + java_version + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_fact_uptime_days():

   # a bit ugly sorry, TODO

   for uptime_start in range(1000,0,-100):
      uptime_end = uptime_start+100
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.system_uptime%3A%3Adays%20%3E%3D%20'+str(uptime_start)+'%20and%20facts.system_uptime%3A%3Adays%20%3C%20'+str(uptime_end),'name')
      if any(host_list):
         item_count=str(len(host_list))
         print "<button class='accordion'>" + str(uptime_start)+'-'+str(uptime_end) + " days (" + item_count  + ")</button>"
         print "<div class='panel'>"
         for host in host_list:
            print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
         print "</div>"

   uptime_start=50
   uptime_end = uptime_start+50
   host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.system_uptime%3A%3Adays%20%3E%3D%20'+str(uptime_start)+'%20and%20facts.system_uptime%3A%3Adays%20%3C%20'+str(uptime_end),'name')
   if any(host_list):
      item_count=str(len(host_list))
      print "<button class='accordion'>" + str(uptime_start)+'-'+str(uptime_end) + " days (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
         print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

   uptime_start=10
   uptime_end = uptime_start+40
   host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.system_uptime%3A%3Adays%20%3E%3D%20'+str(uptime_start)+'%20and%20facts.system_uptime%3A%3Adays%20%3C%20'+str(uptime_end),'name')
   if any(host_list):
      item_count=str(len(host_list))
      print "<button class='accordion'>" + str(uptime_start)+'-'+str(uptime_end) + " days (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
         print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

   uptime_start=1
   uptime_end = uptime_start+9
   host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.system_uptime%3A%3Adays%20%3E%3D%20'+str(uptime_start)+'%20and%20facts.system_uptime%3A%3Adays%20%3C%20'+str(uptime_end),'name')
   if any(host_list):
      item_count=str(len(host_list))
      print "<button class='accordion'>" + str(uptime_start)+'-'+str(uptime_end) + " days (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
         print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

   uptime=0
   host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.system_uptime%3A%3Adays%20%3D%20'+str(uptime),'name')
   if any(host_list):
      item_count=str(len(host_list))
      print "<button class='accordion'>" + str(uptime)+ " days (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
         print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_fact_selinux_current_mode():

   selinux_current_modes = ['enforcing','permissive','disabled']
   for selinux_current_mode in selinux_current_modes:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=facts.selinux_current_mode%20%3D%20'+selinux_current_mode,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + selinux_current_mode + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_hypervisor():

   hosts=get_results(SAT_API+'hosts?per_page=10000&search=name%20%20%21~%20virt-who%25')
   hypervisor_list = {}
   for host in hosts:
      host_details=get_results(SAT_API+'hosts/' + str(host['id']))
      if 'subscription_facet_attributes' in host_details:
         for key, value in host_details['subscription_facet_attributes'].iteritems():
            if key == 'virtual_host':
               if value:
                  hypervisor = value['name'].encode('utf-8')
                  if hypervisor in hypervisor_list:
                     hypervisor_list[hypervisor].append(host_details['name'])
                  else:
                     hypervisor_list[hypervisor] = [host_details['name']]


   for hypervisor_name, hypervisor_guests in hypervisor_list.iteritems():
      if any(hypervisor_guests):
         item_count=str(len(hypervisor_guests))
      else:
         item_count="0"
      print "<button class='accordion'>" + hypervisor_name.replace('virt-who-','') + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in hypervisor_guests:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_myparam():

   params=get_results(SAT_API+'common_parameters?search=name%20%3D%20myparams')

   try:
     paramvalue = params[0]['value']
   except KeyError:
     print "No valid value returned from Satellite"
     sys.exit(1)

   myparams = paramvalue.split(',')
   for myparam in my_params:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=params.myparam+%3D+'+myparam,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + myparam + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_errata_critical_applicable():

   erratas=list_items(KAT_API+'errata?per_page=1000&order=issued+desc&organization_id=1&errata_restrict_applicable=true&search=id%20~%20RH%25%20and%20severity%20%3D%20Critical', 'errata_id')

   for errata in erratas:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=applicable_errata%20%3D%20'+errata,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + errata + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def hosts_by_errata_critical_installable():

   erratas=list_items(KAT_API+'errata?per_page=1000&order=issued+desc&organization_id=1&errata_restrict_installable=true&search=id%20~%20RH%25%20and%20severity%20%3D%20Critical', 'errata_id')

   for errata in erratas:
      host_list=list_items(SAT_API+'hosts?per_page=1000&search=applicable_errata%20%3D%20'+errata,'name')
      if any(host_list):
         item_count=str(len(host_list))
      else:
         item_count="0"
      print "<button class='accordion'>" + errata + " (" + item_count  + ")</button>"
      print "<div class='panel'>"
      for host in host_list:
        print "<a href='https://" + SAT_SERVER + "/hosts/" + host + "'>" + host + "</a><br/>"
      print "</div>"

def main():

   try:
      reportname=sys.argv[1]
   except IndexError:
      print 'Must supply reportname!'
      sys.exit(1)

   print_html_header()
   eval(reportname+"()")
   print_html_footer()

   sys.exit(0)
 
if __name__ == "__main__":
    main()
