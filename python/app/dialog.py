# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import os
import sys
import threading
from datetime import datetime 

import pymel.core as pm

# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui
from .ui.dialog import Ui_Dialog


TIMESTAMP_FORMAT = "%Y-%m-%d"


def show_dialog(app_instance):
    """
    Shows the main dialog window.
    """
    # in order to handle UIs seamlessly, each toolkit engine has methods for launching
    # different types of windows. By using these methods, your windows will be correctly
    # decorated and handled in a consistent fashion by the system. 
    
    # we pass the dialog class to this method and leave the actual construction
    # to be carried out by toolkit.
    app_instance.engine.show_dialog("Submit For Review", app_instance, AppDialog)
    


class AppDialog(QtGui.QWidget):
    """
    Main application dialog window
    """
    
    def __init__(self):
        """
        Constructor
        """
        # first, call the base class and let it do its thing.
        QtGui.QWidget.__init__(self)
        
        # now load in the UI that was created in the UI designer
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)
        self.connectUi()
        # most of the useful accessors are available through the Application class instance
        # it is often handy to keep a reference to this. You can get it via the following method:
        self._app = sgtk.platform.current_bundle()
        
        # via the self._app handle we can for example access:
        # - The engine, via self._app.engine
        # - A Shotgun API instance, via self._app.shotgun
        # - A tk API instance, via self._app.tk 
        
        # lastly, set up our very basic UI
        self.ui.context.setText("Current Context: %s" % self._app.context)
    

    def connectUi(self):
        """
        """
        
        self.ui.pb_submit.clicked.connect(self.submitForReview)
        
        self.ui.pb_loadFiles.clicked.connect(self.loadFilesForReview)

        self.ui.pb_delFiles.clicked.connect(self.removeItemFromList)

    def loadFilesForReview(self):
        """
        """
        filter = "Images (*.jpg *.png *.exr)"
        file_name = QtGui.QFileDialog()
        file_name.setFileMode(QtGui.QFileDialog.ExistingFiles)
        names = file_name.getOpenFileNames(self, "Open files", "C:\\Temp", filter)[0]
        if names:
            for _file in names:
                #itm = QtGui.QListWidgetItem(_file)
                if not self.ui.lw_FileList.findItems(_file, QtCore.Qt.MatchExactly):
                    self.ui.lw_FileList.addItem(_file)

    def removeItemFromList(self):
        """

        :return:
        """
        if self.ui.lw_FileList.hasFocus:
            print 'Deleting item'
            for item in self.ui.lw_FileList.selectedItems():
                self.ui.lw_FileList.takeItem(self.ui.lw_FileList.row(item))


    def validateCurrentFile(self):

        """

        :return:
        """



        return True

    def submitForReview(self):
        """
        """        
        project = self._app.context.project
        entity = self._app.context.entity
        task = self._app.context.task
        step = self._app.context.step
        
        template_work = self._app.get_template("template_work")
        scenename = pm.sceneName()
        fields_work = template_work.get_fields(scenename)
        template_review_maya = self._app.get_template("template_review_maya")
        now = datetime.now().strftime(TIMESTAMP_FORMAT)
        
        #sg = self._app.sgtk.shotgun
        #result = sg.find_one("Step", [["id", "is", step['id']]], ["id", "code", "short_name"])
        #print result 
        
        
        fields = {'Asset': fields_work['Asset'],
              'Step': fields_work['Step'],
              'version': fields_work['version'],
              'year_month_day': datetime.now()
              }

        review_file = template_review_maya.apply_fields(fields)

        review_dir = os.path.dirname(review_file)
        
        data = { 'project': project,
         'code': os.path.basename(scenename).split('.ma')[0],
         'description': 'automatic generated by "Submit For Review" app',
         'sg_path_to_geometry': review_dir,
         'entity': entity,
         'sg_task': task,
        }
        
        print data
        version_exists = self._app.execute_hook("hook_post_submission", action="check_version", data=data)
        if version_exists:
            result = QtGui.QMessageBox.critical(None, u"Version Already Exists!",
                                                "%s was previously submitted for review "
                                                "\n Submit with next version" % data['code'],
                                                QtGui.QMessageBox.Abort)