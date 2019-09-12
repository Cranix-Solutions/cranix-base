# -*- coding: utf-8 -*-

# Copyright (c) Peter Varkoly <peter@varkoly.de> All rights reserved.

"""Some python modules for OSS/CRANIX
Works with Python versions from 3.6.
"""
import json
import os
import sys
import time
import csv
from configobj import ConfigObj

from . import _vars
from ._vars import attr_ext_name
from ._vars import user_attributes

from . import _functions
from ._functions import read_birthday
from ._functions import create_secure_pw
from ._functions import print_error
from ._functions import print_msg

# Internal debug only
init_debug = False

# Define some global variables
required_classes = []
existing_classes = []
all_groups       = []
all_users   = {}
import_list = {}
new_user_count  = 1
new_group_count = 1
lockfile = '/run/oss_import_user'

date = time.strftime("%Y-%m-%d.%H-%M-%S")
# read and set some default values
config    = ConfigObj("/opt/oss-java/conf/oss-api.properties")
passwd    = config['de.openschoolserver.dao.User.Register.Password']
domain    = os.popen('oss_api_text.sh GET system/configuration/DOMAIN').read()
home_base = os.popen('oss_api_text.sh GET system/configuration/HOME_BASE').read()
check_pw  = os.popen('oss_api_text.sh GET system/configuration/CHECK_PASSWORD_QUALITY').read().lower() == 'yes'
roles  = []
for role in os.popen('oss_api_text.sh GET groups/text/byType/primary').readlines():
  roles.append(role.strip())

def init(args):
    global output, input_file, role, password, identifier, full, test, debug, mustchange
    global reset_password, all_classes, clean_class_dirs, sleep
    global import_dir, required_classes, existing_classes, all_users, import_list
    import_dir = home_base + "/groups/SYSADMINS/userimports/" + date
    os.system('mkdir -pm 770 ' + import_dir + '/tmp' )
    #open the output file
    output     = open(import_dir + '/import.log','w')
    #create lock file
    with open(lockfile) as f:
        f.write(date)
    input_file = args.input
    role       = args.role
    password   = args.password
    identifier = args.identifier
    full       = args.full
    test       = args.test
    debug      = args.debug
    mustchange = args.mustchange
    reset_password   = args.reset_password
    all_classes      = args.all_classes
    clean_class_dirs = args.clean_class_dirs
    sleep       = args.sleep

    read_classes()
    read_groups()
    read_users()
    read_csv()

def read_classes():
    global existing_classes
    for group in os.popen('/usr/sbin/oss_api_text.sh GET groups/text/byType/class').readlines():
        existing_classes.append(group.strip())

def read_groups():
    global existing_classes
    for group in os.popen('/usr/sbin/oss_api_text.sh GET groups/text/byType/workgroups').readlines():
        all_groups.append(group.strip())

def read_users():
    global all_users
    for user in json.load(os.popen('/usr/sbin/oss_api.sh GET users/byRole/' + role )):
        user_id = ""
        user['birthDay'] = time.strftime("%Y-%m-%d",time.localtime(user['birthDay']/1000))
        if identifier == "sn-gn-bd":
            user_id = user['surName'].upper() + '-' + user['givenName'].upper() + '-' + user['birthDay']
        else:
            user_id = user[identifier]
            user_id = identifier.replace(' ','')
        all_users[user_id]={}
        for key in user:
            all_users[user_id][key] = user[key]
    if(debug):
        print("All existing user:")
        print(all_users)

def read_csv():
    global import_list
    #Copy the import file into the import directory
    if input_file != import_dir + '/userlist.txt':
        os.system('cp ' + input_file + ' ' + import_dir + '/userlist.txt')
    with open(input_file) as csvfile:
        #Detect the type of the csv file
        dialect = csv.Sniffer().sniff(csvfile.read(1024))
        csvfile.seek(0)
        #Create an array of dicts from it
        csv.register_dialect('oss',dialect)
        reader = csv.DictReader(csvfile,dialect='oss')
        if init_debug:
            print(reader.fieldnames)
        for row in reader:
            user = {}
            user_id = ''
            for key in row:
                if init_debug:
                    print(attr_ext_name[key] + " " + row[key])
                user[attr_ext_name[key]] = row[key]
            try:
                user['birthDay'] = read_birthday(user['birthDay'])
            except SyntaxError:
                user['birthDay'] = ''
            #uid must be in lower case
            if 'uid' in user:
                user['uid'] = user['uid'].lower()
            if identifier == "sn-gn-bd":
                user_id = user['surName'].upper() + '-' + user['givenName'].upper() + '-' + user['birthDay']
            else:
                if not identifier in user:
                    raise SyntaxError("Import file does not contains the identifier:" + identifier)
                user_id = user[identifier]
            user_id = user_id.replace(' ','')
            import_list[user_id] = user
    if(debug):
        print("All user in the list:")
        print(import_list)

def log_debug(text,obj):
    if debug:
        print(text)
        print(obj)


def close():
    if check_pw:
        os.system("oss_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/yes")
    else:
        os.system("oss_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/no")
    os.remove(lockfile)
    output.write(print_msg("Import finished","OK"))
    output.close()

def close_on_error(msg):
    if check_pw:
        os.system("oss_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/yes")
    else:
        os.system("oss_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/no")
    os.remove(lockfile)
    output.write(print_error(msg))
    output.close()

def log_error(msg):
    output.write(print_error(msg))

def log_msg(title,msg):
    output.write(print_msg(title,msg))

def add_group(name):
    global new_group_count
    group = {}
    group['name'] = name.upper()
    group['groupType'] = 'workgroup'
    group['description'] = name
    file_name = '{0}/tmp/group_add.{1}'.format(import_dir,new_group_count)
    with open(file_name, 'w') as fp:
        json.dump(group, fp, ensure_ascii=False)
    result = json.load(os.popen('oss_api_post_file.sh groups/add ' + file_name))
    new_group_count = new_group_count + 1
    if debug:
        print(add_group)
        print(result)
    if result['code'] == 'OK':
        return True
    else:
        log_error(result['value'])
        return False

def add_class(name):
    global new_group_count
    global existing_classes
    group = {}
    group['name'] = name.upper()
    group['groupType'] = 'class'
    #TODO translation
    group['description'] ='Klasse ' + name
    file_name = '{0}/tmp/group_add.{1}'.format(import_dir,new_group_count)
    with open(file_name, 'w') as fp:
        json.dump(group, fp, ensure_ascii=False)
    result = json.load(os.popen('oss_api_post_file.sh groups/add ' + file_name))
    existing_classes.append(name)
    new_group_count = new_group_count + 1
    if debug:
        print(result)
    if result['code'] == 'OK':
        return True
    else:
        log_error(result['value'])
        return False

def add_user(user,ident):
    global new_user_count
    global import_list
    if mustchange:
        user['mustChange'] = True
    if password != "":
        user['password'] = password
    if 'class' in user:
        user['classes'] = user['class']
        del user['class']
    file_name = '{0}/tmp/user_add.{1}'.format(import_dir,new_user_count)
    with open(file_name, 'w') as fp:
        json.dump(user, fp, ensure_ascii=False)
    result = json.load(os.popen('oss_api_post_file.sh users/insert ' + file_name))
    import_list[ident]['id']       = result['objectId']
    import_list[ident]['uid']      = result['parameters'][0]
    import_list[ident]['password'] = result['parameters'][3]
    new_user_count = new_user_count + 1
    if debug:
        print(result)
    if result['code'] == 'OK':
        return True
    else:
        log_error(result['value'])
        return False

def modify_user(user,ident):
    if identifier != 'sn-gn-bd':
        user['givenName'] = import_list[ident]['givenName']
        user['surName']   = import_list[ident]['surName']
        user['birthDay']  = import_list[ident]['birthDay']
    file_name = '{0}/tmp/user_modify.{1}'.format(import_dir,user['uid'])
    with open(file_name, 'w') as fp:
        json.dump(user, fp, ensure_ascii=False)
    result = json.load(os.popen('oss_api_post_file.sh users/{0} {1} '.format(user['id'],file_name)))
    if debug:
        print(result)
    if result['code'] == 'ERROR':
        log_error(result['value'])

def move_user(uid,old_classes,new_classes):
    for g in old_classes:
       if not g in new_classes:
           result = json.load(os.popen('/usr/sbin/oss_api_text.sh DELETE users/text/{0}/groups/{1}'.format(uid,g)))
           if debug:
               print(result)
           if result['code'] == 'ERROR':
               log_error(result['value'])
    for g in new_classes:
       if not g in old_classes:
           result = json.load(os.popen('/usr/sbin/oss_api_text.sh PUT users/text/{0}/groups/{1}'.format(uid,g)))
           if debug:
               print(result)
           if result['code'] == 'ERROR':
               log_error(result['value'])

def delete_user(uid):
    result = json.load(os.popen('/usr/sbin/oss_api_text.sh DELETE users/text/{0}'.format(uid)))
    if debug:
        print(result)
    if result['code'] == 'ERROR':
        log_error(result['value'])

def delete_class(group):
    result = json.load(os.popen('/usr/sbin/oss_api_text.sh DELETE groups/text/{0}'.format(group)))
    if debug:
        print(result)
    if result['code'] == 'ERROR':
        log_error(result['value'])