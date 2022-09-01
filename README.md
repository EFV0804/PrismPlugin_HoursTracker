# PrismPlugin_HoursTracker
## Description
A plugin for Prism pipeline to track hours spent working on different projects. The plugin uses a set of callback functions to detect activity on the current active project and store the date and duration of this activity. 

## How To
  The Prism user doesn't have anything to do to use this tracker, as long as it is load on Prism launch it will keep a record of the time spent working on a project. A HTML file can be used to display the data in a more readable format. A shortcut to that HTML file can be created in the Prism Launcher for quicker acces
  
  The hours tracked are approximations and are only a way to help artists keep track.
## Install
  To install this plugin copy the  'HoursTracker' folder into your Prims plugin location, and restart Prism.
  
  Works for Prism v2.0.0.beta11.4, v2.0.0.beta11.5, v2.0.0.beta11.6, v2.0.0.beta11.7, v2.0.0.beta11.8
  
## Dev
The plugin uses Prism built in callbacks to detect activity. Everytime a callback is used, the time of the activity is stored in a json file. The data is available to artist through a html file that can be opened in their browser.

### Plugin architecture

![plugin_structur](https://user-images.githubusercontent.com/72398192/187925654-556100de-de06-4e43-ac6e-f86f159b2e0b.PNG)


### Data exemple
      {
          "days": [
              {
                  "date": "30/08/22",
                  "sessions": [
                      {
                          "project": "project_01",
                          "project_sessions": [
                              {
                                  "start_time": "12:51:50",
                                  "last_action_time": "12:52:20",
                                  "total_time": "0:00:30"
                              }
                          ],
                          "total_time": "0:00:30"
                      }
                  ]
              },
              {
                  "date": "31/08/22",
                  "sessions": [
                      {
                          "project": "project_02",
                          "project_sessions": [
                              {
                                  "start_time": "08:31:33",
                                  "last_action_time": "08:32:30",
                                  "total_time": "0:00:57"
                              },
                              {
                                  "start_time": "08:58:34",
                                  "last_action_time": "08:59:51",
                                  "total_time": "0:01:17"
                              }
                          ],
                          "total_time": "1:10:59"
                      }
                  ]
              }
          ],
          "last_active_project": "project_02",
          "user_id": "evidal"
      }

### Data Logic
This is a flow chart of the logic that dictates how the data will be sorted.
![logic](https://user-images.githubusercontent.com/72398192/187926101-9fee5d68-3db2-43fd-b4c1-56c0f51eca19.PNG)


## Credits
- [MenhirFX](www.menhirfx.com)
