# time_entry_tools
Various utilities to aid in time entry tasks


# Installation
To use this toolset, download the dist folder located in time_entry_tools/dist.  This folder contains the windows executables for the time entry tools.

# Configuration
Each tool has its own configuration file that needs to be setup before the program will work.

Currently, these tools only support Clockify and as such require your Clockify workspace_id and api_key to be save in the configuration file.

An example configuration file can be found in the dist/{tool_name} folders called config.cfg_example.  After you have enter your personal configurations, rename the file to config.cfg for the application to use it.

# Running the Application
With the configuration file setup, just run the {tool_name}.exe file that is located in the dist/{tool_name} folder to run the application.
