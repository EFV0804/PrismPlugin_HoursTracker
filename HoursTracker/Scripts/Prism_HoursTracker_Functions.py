# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2021 Richard Frangenberg
#
# Licensed under GNU LGPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

# Author: Elise Vidal
# Contact :  evidal@artfx.fr


try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from datetime import datetime, timedelta
import json
import os
import shutil
import traceback


class Prism_HoursTracker_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin
        version = self.core.version.split('.', 3)[-1]

# Register callback functions
        self.core.callbacks.registerCallback(
            "onSceneOpen", self.onSceneOpen, plugin=self)
        self.core.callbacks.registerCallback(
            "sceneSaved", self.sceneSaved, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateManagerShow", self.onStateManagerShow, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateManagerClose", self.onStateManagerClose, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateDeleted", self.onStateDeleted, plugin=self)
        self.core.callbacks.registerCallback(
            "onStateCreated", self.onStateCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onPublish", self.onPublish, plugin=self)
        self.core.callbacks.registerCallback(
            "postPublish", self.postPublish, plugin=self)
        self.core.callbacks.registerCallback(
            "onProductCreated", self.onProductCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onAssetCreated", self.onAssetCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onShotCreated", self.onShotCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onDepartmentCreated", self.onDepartmentCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "onTaskCreated", self.onTaskCreated, plugin=self)
        self.core.callbacks.registerCallback(
            "postExport", self.postExport, plugin=self)

# Check if exists/create on disk data files
        self.user_data_dir = 'U:/mesDocuments/HoursTracker/'
        self.user_data_json = self.user_data_dir + 'hours.json'
        self.user_data_js = self.user_data_dir + 'hours.js'
        self.user_data_html = self.user_data_dir + 'hours.html'
        self.user_data_css = self.user_data_dir + 'style.css'
        self.user_data_backup = self.user_data_dir + '/backup/'
        self.user_log = self.user_data_dir + 'log.txt'

        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

        if not os.path.exists(self.user_data_backup):
            os.makedirs(self.user_data_backup)

        if not os.path.exists(self.user_data_json):
            with open(self.user_data_json, 'a') as json_file:
                json_file.write('{}')

        if not os.path.exists(self.user_data_js):
            open(self.user_data_js, 'a').close()

        if not os.path.exists(self.user_log):
            open(self.user_log, 'a').close()

        if not os.path.exists(self.user_data_html):
            src = 'R:/Prism/Plugins/{version}/HoursTracker/Scripts/templates/hours.html'.format(version=version)
            dst = self.user_data_html
            shutil.copy(src, dst)

        if not os.path.exists(self.user_data_css):
            src = 'R:/Prism/Plugins/{version}/HoursTracker/Scripts/templates/style.css'.format(version=version)
            dst = self.user_data_css
            shutil.copy(src, dst)

    # if returns true, the plugin will be loaded by Prism
    @err_catcher(name=__name__)
    def isActive(self):
        return True

# UTILITY FUNCTIONS
    def get_template_data(self, template):
        """Returns the template data matching the template name that was
        passed as arg.
        possible args are : 'day', 'session', 'project_session'
        """

        template_dict = {
                          'day': {
                            'date': '',
                            'sessions': [
                              {
                                'project': '',
                                'project_sessions': [
                                  {
                                    'start_time': '',
                                    'last_action_time': '',
                                    'total_time': ''
                                  }
                                ]
                              }
                            ]
                          },
                          'session': {
                            'project': '',
                            'project_sessions': [
                              {
                                'start_time': '',
                                'last_action_time': '',
                                'total_time': ''
                              }
                            ]
                          },
                          'project_session': {
                            'start_time': '',
                            'last_action_time': '',
                            'total_time': ''
                          }
                        }

        return template_dict[template]

    def reset_user_data(self):
        """
        Resets the json file containing the user's data
        """
        with open(self.user_data_json, 'a') as json_file:
                json_file.write('{}')

    def get_date_delta(self, newest_date, oldest_date):
        """
            Returns a timedelta object of two giving dates.
            Checks and converts if necessarey to datetime format before
            calculating delta

            newest_date: str or datetime
            oldest_date: str or datetime
        """
        try:
            return newest_date - oldest_date
        except TypeError:
            try:
                newest_date = self.get_date_as_datetime_obj(newest_date)
            except TypeError:
                pass
            try:
                oldest_date = self.get_date_as_datetime_obj(oldest_date)
            except TypeError:
                pass
            return newest_date - oldest_date

    def is_new_week(self, data):
        """
        Checks if if today's date sets off a new work week, by retrieving the
        last date present in the user's data, and deltaing it with today's date

        Returns True if it has more than 3 days since last entry
        """
        last_day = data['days'][-1]['date']
        last_day = self.get_date_as_datetime_obj(last_day)
        today = datetime.now().strftime('%d/%m/%y')
        delta = self.get_date_delta(today, last_day)
        if delta.days >= 3:
            return True
        else:
            False

    def archive_data(self):
        """
        Copies the user's json data to a backup location
        """
        src = self.user_data_json
        today = datetime.now().strftime('%d_%m_%y')
        dst = self.user_data_backup + today + '_hours.json'
        shutil.copy(src, dst)

    def initialise_data(self, data, date, start_time):
        '''
        Returns dict with user data. Initialises the data with a new day of hours tracked.
        '''
        data['days'] = []
        day = self.initialise_day(date, start_time)
        data['days'].append(day)
        data['last_active_project'] = self.current_project

        return data

    def initialise_day(self, date, start_time):
        '''
        Returns a dict with the initial data of the current day.
        Called when no previous data exists for the day.
        '''
        day = self.get_template_data('day')
        day['date'] = date
        day['sessions'][-1]['project'] = self.get_current_project()
        day['sessions'][-1]['project_sessions'][-1]['start_time'] = start_time
        day['sessions'][-1]['project_sessions'][-1]['last_action_time'] = start_time
        day['sessions'][-1]['project_sessions'][-1]['total_time'] = str(
            self.get_time_delta(start_time, start_time))

        return day

    def initialise_session(self, start_time):
        '''
        Returns a dict of session data.
        Sessions are group all work done on a project
        '''
        session = self.get_template_data('session')
        session['project'] = self.get_current_project()
        session['project_sessions'][-1]['start_time'] = start_time
        session['project_sessions'][-1]['last_action_time'] = start_time
        session['project_sessions'][-1]['total_time'] = str(
            self.get_time_delta(start_time, start_time))

        return session

    def initialise_project_session(self, start_time):
        '''
        Returns data for a project session.
        A project session is work session on a project.
        '''
        project_session = self.get_template_data('project_session')
        project_session['start_time'] = start_time
        project_session['last_action_time'] = start_time
        project_session['total_time'] = str(
            self.get_time_delta(start_time, start_time))
        return project_session

    def get_total_session_time(self, data):
        '''
        Returns a dict of user data, with the total time of each session added.
        '''
        for session in data['days'][-1]['sessions']:
            total_time = timedelta(seconds=0)
            for project_session in session['project_sessions']:
                if 'total_time' in project_session:
                    time = self.get_time_as_datetime(project_session['total_time'])
                    delta = timedelta(hours=time.hour, minutes=time.minute, seconds=time.second)
                    total_time += delta
                    session['total_time'] = str(total_time)

        return data

    def file_exists(self, filepath):
        '''
        Checks if file exists on disk
        Return True or False
        '''
        return os.path.exists(filepath)

    def is_file_empty(self, filepath):
        '''
        Check if file is empty
        Returns True or False
        '''
        return os.stat(filepath).st_size == 0

    def get_current_project(self):
        '''
        Returns the project's name
        '''
        try:
            project_name = self.core.projectName
        except:
            project_path = self.core.getConfig("globals", "current project")
            project_name = os.path.basename(os.path.dirname(os.path.dirname(project_path)))

        return project_name

    def write_to_file(self, content, filename):
        '''
        Writes given content to the given filename.
        '''
        output_file = open(filename, 'w')
        output_file.write(content)
        output_file.close()

    def get_date_as_string(self, datetime_obj):
        '''
        Converts datetime object to string format %d/%m/%y.
        Returns: string
        '''
        date_string = datetime_obj.strftime('%d/%m/%y')
        return date_string

    def get_date_as_datetime_obj(self, date_string):
        '''
        Converts a string object representing a date, like this %d/%m/%y, to a datetime object
        returns: datetime
        '''
        datetime_obj = datetime.strptime(date_string, '%d/%m/%y')
        return datetime_obj

    def get_time_as_string(self, datetime_obj):
        '''
        Converts a datetime.time object as string, in this format %H:%M:%S
        returns: string
        '''
        return datetime_obj.strftime('%H:%M:%S')

    def get_time_as_datetime(self, time):
        '''
        Converts string reprensenting time like this %H:%M:%S to a datetime.time object
        returns: datetime.time
        '''
        return datetime.strptime(time, '%H:%M:%S')

    def get_time_delta(self, newest_time, oldest_time):
        try:
            return newest_time - oldest_time
        except TypeError:
            try:
                newest_time = self.get_time_as_datetime(newest_time)
            except TypeError:
                pass
            try:
                oldest_time = self.get_time_as_datetime(oldest_time)
            except TypeError:
                pass
            return newest_time - oldest_time

    def log(self, error_message):
        date = datetime.now().strftime('%d/%m/%y')
        time = datetime.now().strftime('%H:%M:%S')
        log_message = '\n' + date + ", " + time + " : " + error_message
        with open(self.user_log, 'a') as logfile:
            logfile.write(log_message)

    def get_username(self):
        try:
            return self.core.getConfig("globals", "username")
        except:
            return self.core.username

    def is_project_in_sessions(self, data, project):
        found = False
        for session in data['days'][-1]['sessions']:
            if session['project'] == project:
                found = True
                break
            else:
                pass

        return found

    def is_last_active_project(self, data, project):
        if project == data['last_active_project']:
            return True
        else:
            return False

    def get_last_project_session(self, data):
        today = data['days'][-1]
        for session in today['sessions']:
            if session['project'] == self.get_current_project():
                today_session = session
        project_session = today_session['project_sessions'][-1]

        return project_session

    def get_current_session(self, data):
        today = data['days'][-1]
        for session in today['sessions']:
            if session['project'] == self.get_current_project():
                return session
# LOGIC
    def update_data(self):
        """
        Function that runs everytime a callback is called in Prism. The logic happens here.
        Retrieves user date from file
        Creates data relevant to the scene opening action: user, date, time
        Runs a series of checks on existing data to determine where to write the action's data
        Writes the action's data
        """
        if 'noUI' not in self.core.prismArgs:
            try:
                # Get scene open action relevant data
                user = self.get_username()
                date = datetime.now().strftime('%d/%m/%y')
                start_time = datetime.now().strftime('%H:%M:%S')

                # Get data from file
                try:
                    # Open user json data and laod it to data
                    with open(self.user_data_json, 'r') as json_file:
                        raw_data = json_file.read()
                        data = json.loads(raw_data)
                except:
                    # If json file empty return empty dict/json object
                    data = {}

                # If data is empty initialise it
                if data == {}:
                    data = self.initialise_data(data, date, start_time)

                # Check if it's a new week, archive and reset data if it is
                elif self.is_new_week(data) is True:
                    self.archive_data()
                    data = {}
                    self.reset_user_data()
                    data = self.initialise_data(data, date, start_time)

                # Check if current day exists and create data if necessary
                elif date != data['days'][-1]['date']:
                    new_day = self.initialise_day(date, start_time)
                    data['days'].append(new_day)
                    data['last_active_project'] = self.get_current_project()

                # Does the current project have a session if not initialise it
                elif self.is_project_in_sessions(data, self.get_current_project()) == False:
                    session = self.initialise_session(start_time)
                    data['days'][-1]['sessions'].append(session)
                    data['last_active_project'] = self.get_current_project()

                #  Is the current project the last active project, if not start new project session
                elif self.is_last_active_project(data, self.get_current_project()) == False:
                    project_session  = self.initialise_project_session(start_time)
                    for session in data['days'][-1]['sessions']:
                        if session['project'] == self.get_current_project():
                            session['project_sessions'].append(project_session)

                    data['last_active_project'] = self.get_current_project()
                # If current project is last active project, update action time
                else:
                    for index, session in enumerate(data['days'][-1]['sessions']):
                        if session['project'] == self.get_current_project():
                            data['days'][-1]['sessions'][index]['project_sessions'][-1]['last_action_time'] = start_time
                            start = data['days'][-1]['sessions'][index]['project_sessions'][-1]['start_time']
                            last = data['days'][-1]['sessions'][index]['project_sessions'][-1]['last_action_time']
                            data['days'][-1]['sessions'][index]['project_sessions'][-1]['total_time'] = str(
                                self.get_time_delta(last, start))


                # Set total time for all sessions
                data = self.get_total_session_time(data)

                # Set user id data
                data['user_id'] = user

                # Write data to file
                json_obj = json.dumps(data)
                content = "var data = '{}'".format(json_obj)
                self.write_to_file(json_obj, self.user_data_json)
                self.write_to_file(content, self.user_data_js)
            except Exception as e:
                self.log(traceback.format_exc())

# CALLBACKS
    '''
    To add new callbacks:
    1. Register the callback in the init() function
    2. Add a definition for the  callback function below, make sure it call self.update_data()
    3. Check in the Prism source code if the callback accepts *args and/or **kwargs (to avoid Prism Errors that can't be caught)
    '''
    def onSceneOpen(self, *args):
        self.update_data()

    def sceneSaved(self, *args):
        self.update_data()

    def onStateManagerShow(self, *args):
        self.update_data()

    def onStateManagerClose(self, *args):
        self.update_data()

    def onStateDeleted(self, *args):
        self.update_data()

    def onStateCreated(self, *args, **kwargs):
        self.update_data()

    def onPublish(self, *args):
        self.update_data()

    def postPublish(self, *args, **kargs):
        self.update_data()

    def onProductCreated(self, *args):
        self.update_data()

    def onAssetCreated(self, *args):
        self.update_data()

    def onShotCreated(self, *args):
        self.update_data()

    def onDepartmentCreated(self, *args):
        self.update_data()

    def onTaskCreated(self, *args):
        self.update_data()

    def postExport(self, **kwargs):
        self.update_data()
