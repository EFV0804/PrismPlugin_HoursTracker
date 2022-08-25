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


try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from distutils.file_util import write_file
from tracemalloc import start
from PrismUtils.Decorators import err_catcher_plugin as err_catcher
import PrismUtils.PluginManager as PM
import Prism_HoursTracker_Variables as prism_var
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
            "postPublish", self.postPublish, plugin=self)
        self.core.callbacks.registerCallback(
            "postExport", self.postExport, plugin=self)
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

        if not os.path.exists(self.user_data_html):
            src = 'R:/Prism/Plugins/{version}/HoursTracker/Sccripts/templates/hours.html'.format(version=version)
            dst = self.user_data_css
            shutil.copy(src, dst)

        self.current_project = self.core.projectName
        self.plugin_load()

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
        data['days'] = []
        day = self.initialise_day(date, start_time)
        data['days'].append(day)
        data['last_active_project'] = self.current_project

        return data

    def initialise_day(self, date, start_time):
        day = self.get_template_data('day')
        day['date'] = date
        day['sessions'][-1]['project'] = self.get_current_project()
        day['sessions'][-1]['project_sessions'][-1]['start_time'] = start_time
        day['sessions'][-1]['project_sessions'][-1]['last_action_time'] = start_time
        day['sessions'][-1]['project_sessions'][-1]['total_time'] = str(
            self.get_time_delta(start_time, start_time))

        return day

    def initialise_session(self, start_time):
        session = self.get_template_data('session')
        session['project'] = self.get_current_project()
        session['project_sessions'][-1]['start_time'] = start_time
        session['project_sessions'][-1]['last_action_time'] = start_time
        session['project_sessions'][-1]['total_time'] = str(
            self.get_time_delta(start_time, start_time))

        return session

    def initialise_project_session(self, start_time):
        project_session = self.get_template_data('project_session')
        project_session['start_time'] = start_time
        project_session['last_action_time'] = start_time
        project_session['total_time'] = str(
            self.get_time_delta(start_time, start_time))

        return project_session

    def get_total_session_time(self, data):
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
        return self.core.projectName

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
        log_message = '/n' + date + ", " + time + " : " + error_message
        with open(self.user_log, 'a') as logfile:
            logfile.write(log_message)

# LOGIC
    def plugin_load(self):
        """
        Runs a series of checks json data when the plugin is loaded. Changes on json are written to file.
            - Checks if it's a new week, and reset json data if it is.
            - Checks if json data is empty, and sets it if it is.
            - Checks if project has changed, and creates new project_session if it has
        """
        try:
            # Open user json data and laod it to data
            with open(self.user_data_json, 'r') as json_file:
                raw_data = json_file.read()
                data = json.loads(raw_data)

            # Get today's date , a the time of the plugin load
            date = datetime.now().strftime('%d/%m/%y')
            start_time = datetime.now().strftime('%H:%M:%S')

            # If data is empty, create list of days and append a day template to it, add the current project as last active.
            # Then fill the day template data with relevant information
            if data == {}:
                data = self.initialise_data(data, date, start_time)

            # # Check if current day exists and create data if necessary
            if date != data['days'][-1]['date']:
                self.core.popup("Today's date is not currently in data, adding it now")
                new_day = self.initialise_day(date, start_time)
                data['days'].append(new_day)

            # Check if it's a new week, archive and reset data if it is
            if self.is_new_week(data) is True:
                self.archive_data()
                data = {}
                self.reset_user_data()
                data = self.initialise_data(data, date, start_time)

            # If data is not empty check if the project has changed
            # If it has and more than one session already exists (more than 1 project has been worked on today), adds a project session
            # for the current project
            else:
                if self.current_project != data['last_active_project']:
                    data['last_active_project'] = self.current_project
                    today_sessions = data['days'][-1]['sessions']
                    if len(today_sessions) > 1:
                        for session in today_sessions:
                            if session['project'] == self.current_project:
                                project_session = self.initialise_project_session(start_time)
                                session['project_sessions'].append(project_session)
                    else:
                        project_session = self.initialise_project_session(start_time)
                        today_sessions[-1]['project_sessions'].append(project_session)

            # Write the changes to the json file
            json_obj = json.dumps(data)
            content = "var data = '{}'".format(json_obj)
            self.write_to_file(json_obj, self.user_data_json)
            self.write_to_file(content, self.user_data_js)
        except Exception as e:
            self.log(traceback.format_exc())

    def update_data(self):
        """
        Function that runs everytime a callback is called in Prism. The logic happens here.
        Retrieves user date from file
        Creates data relevant to the scene opening action: user, date, time
        Runs a series of checks on existing data to determine where to write the action's data
        Writes the action's data
        """
        try:
            # Get scene open action relevant data
            user = self.core.username
            date = datetime.now().strftime('%d/%m/%y')
            start_time = datetime.now().strftime('%H:%M:%S')

            # Get data from file
            with open(self.user_data_json, 'r') as json_file:
                raw_data = json_file.read()
                data = json.loads(raw_data)

            # Check if current day exists and create data if necessary
            if date != data['days'][-1]['date']:
                self.core.popup("Today's date is not currently in data, adding it now")
                new_day = self.initialise_day(date, start_time)
                data['days'].append(new_day)

            # Check if it's a new week, archive and reset data if it is
            if self.is_new_week(data) is True:
                self.archive_data()
                data = {}
                self.reset_user_data()
                data = self.initialise_data(data, date, start_time)

            # Get last day
            day = data['days'][-1]

            # Get current session
            current_session = None
            for session in day['sessions']:
                if self.core.projectName == session['project']:
                    current_session = session
            # Set last action time
            if current_session is not None:
                last_session = current_session['project_sessions'][-1]
                if 'last_action_time' in last_session:
                    self.core.popup('Checking how long since last session activity')
                    time_since_last = self.get_time_delta(start_time, last_session['last_action_time'])
                    if time_since_last > timedelta(hours=2):
                        self.core.popup('Time since last action is : ' + str(time_since_last))
                        new_session = self.initialise_project_session(start_time)
                        day['sessions'][-1]['project_sessions'].append(new_session)
                    else:
                        last_session['last_action_time'] = start_time
                        last_session['total_time'] = str(self.get_time_delta(last_session['last_action_time'], last_session['start_time']))
                else:
                    self.core.popup('No last action, writing one now')
                    last_session['last_action_time'] = start_time
                    last_session['total_time'] = str(self.get_time_delta(last_session['last_action_time'], last_session['start_time']))
            else:
                self.core.popup('Current Project not currently in data, adding it now')
                new_session = self.initialise_session(start_time)
                day['sessions'].append(new_session)

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
    def onSceneOpen(self, *args):
        self.update_data()

    def sceneSaved(self, *args):
        self.update_data()

    def onStateManagerShow(self, *args):
        self.update_data()

    def onStateManagerClose(self, *args):
        self.update_data()

    def onStateDeleted(self, *args, **kargs):
        self.update_data()

    def postPublish(self, *args):
        self.update_data()

    def postExport(self, *args):
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
