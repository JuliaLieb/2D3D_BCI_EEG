"""
User Interface
Creates user interface window and functions for interaction with feedback model and unity paradigm
"""

import re
import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets
import subprocess

from FeedbackModel import sequence_generator, bci_config


class UiUserInterface(object):
    """ -----------------------
    Button Events (Click)
    ------------------------"""

    def update_button_click(self):

        print("Check input settings...")
        subject_id = 'S' + str(self.input_id.value())
        # total_runs = self.input_total_runs.value()
        tasks_per_run = self.input_tasks.value()
        n_run = self.input_run.value()
        n_session = self.input_session.value()
        if self.radio_mi.isChecked():
            motor_mode = "MI"
        else:
            motor_mode = "ME"
        #if self.radio_fb_on.isChecked():
        if n_run == 1: #calibration run
            fb_mode = "off"
        else:
            fb_mode = "on"
        """if self.radio_erds_average.isChecked():
            erds_mode = "average"
        else:
            erds_mode = "single" """
        erds_mode = "average"
        if self.radio_3d.isChecked():
            dimension_mode = "3D"
        else:
            dimension_mode = "2D"

        bci_config.update_bci_config(subject_id, tasks_per_run, n_run, n_session, motor_mode, fb_mode,
                                     erds_mode, dimension_mode)
        print("... bci-config.json is updated with input settings.")

        tasks_per_run = int(self.input_tasks.value())
        sequence_generator.sequence_generator(subject_id, tasks_per_run, n_run, n_session, motor_mode, dimension_mode)
        print("Sequence was generated.")

    def eeg_sim_button_click(self):
        print("EEG simulation is started...")
        cwd = os.getcwd()
        subprocess.Popen("python " + cwd + "/FeedbackModel/eeg_simulation.py")
        print("eeg_simulation is open.")


    def stream_viewer_button_click(self):
        print("Open stream viewer...")
        subprocess.Popen("lsl_viewer.exe")
        print("Stream viewer is open.")


    def train_button_click(self):
        print("Button for calculation of CSP & LDA clicked.")
        cwd = os.getcwd()
        subprocess.Popen("python " + cwd + "/FeedbackModel/compute_csp_lda.py")

    def open_button_click(self):
        print("Button for opening Unity clicked.")
        cwd = os.getcwd()
        subprocess.Popen(cwd + "\\UnityGame\\BCI-game\\BCI-game.exe", cwd = cwd + "\\UnityGame")
        print("Unity is open.")

    def lsl_recorder_button_click(self):
        print("Button for opening LSL Recorder clicked.")
        cwd = os.getcwd()
        lsl_rec_file = cwd + '/LabRecorder/LabRecorder.exe'
        subprocess.Popen(lsl_rec_file)
        print("LSL Recorder is open.")

    def start_fb_button_click(self):
        print("Start feedback model button clicked.")
        cwd = os.getcwd()
        path = cwd + "/SubjectData/current/csp.mat"
        if not os.path.isfile(path):
            print("CSP and LDA not found!")
            return None
        subprocess.Popen("python " + cwd + "./FeedbackModel/feedback_model.py")


    def close_button_click(self):
        print("Close button clicked.")
        MainWindow.close()

    def calc_results_button_click(self):
        print("Results could be calculated here.")

    """ -----------------------
    User Interface Setup
    ------------------------"""

    def setup_ui(self, main_window, current_config):
        main_window.setObjectName("main_window")
        main_window.resize(900, 600)

        """Title"""
        self.l_title = QtWidgets.QLabel(main_window)
        self.l_title.setGeometry(QtCore.QRect(20, 20, 801, 51))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.l_title.setFont(font)
        self.l_title.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
        self.l_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.l_title.setObjectName("l_title")

        """--------------Label Input--------------"""
        self.l_input = QtWidgets.QLabel(main_window)
        self.l_input.setGeometry(QtCore.QRect(160, 100, 71, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.l_input.setFont(font)
        self.l_input.setObjectName("l_input")

        """Subject ID"""
        current_subject_id = current_config['gui-input-settings']['subject-id']
        current_subject_id = re.sub(r'.', '', current_subject_id, count=1)
        self.input_id = QtWidgets.QSpinBox(main_window)
        self.input_id.setGeometry(QtCore.QRect(270, 160, 131, 31))
        self.input_id.setPrefix("S")
        self.input_id.setProperty("value", current_subject_id)
        self.input_id.setObjectName("input_ID")
        self.label_id = QtWidgets.QLabel(main_window)
        self.label_id.setGeometry(QtCore.QRect(60, 160, 171, 18))
        self.label_id.setObjectName("label_ID")

        """Total runs"""
        """
        current_total_runs = current_config['gui-input-settings']['total-runs']
        self.label_total_runs = QtWidgets.QLabel(main_window)
        self.label_total_runs.setGeometry(QtCore.QRect(60, 210, 261, 18))
        self.label_total_runs.setObjectName("label_total_runs")
        self.input_total_runs = QtWidgets.QSpinBox(main_window)
        self.input_total_runs.setGeometry(QtCore.QRect(340, 210, 60, 24))
        self.input_total_runs.setMinimum(2)
        self.input_total_runs.setProperty("value", current_total_runs)
        self.input_total_runs.setObjectName("input_total_runs")
        """

        """Trials per task"""
        current_tasks = current_config['gui-input-settings']['n-per-task']
        self.label_task = QtWidgets.QLabel(main_window)
        self.label_task.setGeometry(QtCore.QRect(60, 250, 261, 18))
        self.label_task.setObjectName("label_task")
        self.input_tasks = QtWidgets.QSpinBox(main_window)
        self.input_tasks.setGeometry(QtCore.QRect(340, 250, 60, 24))
        self.input_tasks.setMinimum(1)
        self.input_tasks.setProperty("value", current_tasks)
        self.input_tasks.setObjectName("input_tasks")

        """Session"""
        current_session = current_config['gui-input-settings']['n-session']
        self.label_session = QtWidgets.QLabel(main_window)
        self.label_session.setGeometry(QtCore.QRect(60, 290, 261, 18))
        self.label_session.setObjectName("label_session")
        self.input_session = QtWidgets.QSpinBox(main_window)
        self.input_session.setGeometry(QtCore.QRect(340, 290, 60, 24))
        self.input_session.setMinimum(1)
        self.input_session.setProperty("value", current_session)
        self.input_session.setObjectName("input_session")

        """Run"""
        current_run = current_config['gui-input-settings']['n-run']
        self.label_run = QtWidgets.QLabel(main_window)
        self.label_run.setGeometry(QtCore.QRect(60, 330, 261, 18))
        self.label_run.setObjectName("label_run")
        self.input_run = QtWidgets.QSpinBox(main_window)
        self.input_run.setGeometry(QtCore.QRect(340, 330, 60, 24))
        self.input_run.setMinimum(1)
        self.input_run.setProperty("value", current_run)
        self.input_run.setObjectName("input_run")

        """Radio Button: MI or ME"""
        current_motor_mode = current_config['gui-input-settings']['motor-mode']
        self.radio_mi = QtWidgets.QRadioButton(main_window)
        self.radio_mi.setGeometry(QtCore.QRect(60, 410, 200, 22))
        self.radio_mi.setObjectName("radio_MI")
        self.goup_me_mi = QtWidgets.QButtonGroup(main_window)
        self.goup_me_mi.setObjectName("goup_ME_MI")
        self.goup_me_mi.addButton(self.radio_mi)
        self.radio_me = QtWidgets.QRadioButton(main_window)
        self.radio_me.setGeometry(QtCore.QRect(60, 440, 200, 22))
        self.radio_me.setObjectName("radio_ME")
        self.goup_me_mi.addButton(self.radio_me)
        if current_motor_mode == "MI":
            self.radio_mi.setChecked(True)
        else:
            self.radio_me.setChecked(True)

        """Radio Button: Feedback on or off"""
        """
        current_fb_mode = current_config['gui-input-settings']['fb-mode']
        self.radio_fb_on = QtWidgets.QRadioButton(main_window)
        self.radio_fb_on.setGeometry(QtCore.QRect(60, 490, 200, 22))
        self.radio_fb_on.setObjectName("radio_FB_on")
        self.group_fb = QtWidgets.QButtonGroup(main_window)
        self.group_fb.setObjectName("group_FB")
        self.group_fb.addButton(self.radio_fb_on)
        self.radio_fb_off = QtWidgets.QRadioButton(main_window)
        self.radio_fb_off.setGeometry(QtCore.QRect(60, 520, 200, 22))
        self.radio_fb_off.setObjectName("radio_FB_off")
        self.group_fb.addButton(self.radio_fb_off)
        if current_fb_mode == "on":
            self.radio_fb_on.setChecked(True)
        else:
            self.radio_fb_off.setChecked(True)
        """


        """Radio Button: ERDS single or average"""
        """
        current_erds_mode = current_config['feedback-model-settings']['erds']['mode']
        self.radio_erds_single = QtWidgets.QRadioButton(main_window)
        self.radio_erds_single.setGeometry(QtCore.QRect(60, 570, 200, 22))
        self.radio_erds_single.setObjectName("radio_ERDS_single")
        self.group_erds = QtWidgets.QButtonGroup(main_window)
        self.group_erds.setObjectName("group_ERDS")
        self.group_erds.addButton(self.radio_erds_single)
        self.radio_erds_average = QtWidgets.QRadioButton(main_window)
        self.radio_erds_average.setGeometry(QtCore.QRect(60, 600, 200, 22))
        self.radio_erds_average.setChecked(True)
        self.radio_erds_average.setObjectName("radio_ERDS_average")
        self.group_erds.addButton(self.radio_erds_average)
        if current_erds_mode == "average":
            self.radio_erds_average.setChecked(True)
        else:
            self.radio_erds_single.setChecked(True)
        """

        """Radio Button: 2D or 3D"""
        current_dimension_mode = current_config['gui-input-settings']['dimension-mode']
        self.radio_2d = QtWidgets.QRadioButton(main_window)
        self.radio_2d.setGeometry(QtCore.QRect(280, 410, 200, 22))
        self.radio_2d.setChecked(True)
        self.radio_2d.setObjectName("radio_2D")
        self.group_2d_3d = QtWidgets.QButtonGroup(main_window)
        self.group_2d_3d.setObjectName("group_2D_3D")
        self.group_2d_3d.addButton(self.radio_2d)
        self.radio_3d = QtWidgets.QRadioButton(main_window)
        self.radio_3d.setGeometry(QtCore.QRect(280, 440, 200, 22))
        self.radio_3d.setObjectName("radio_3D")
        self.group_2d_3d.addButton(self.radio_3d)
        if current_dimension_mode == "2D":
            self.radio_2d.setChecked(True)
        else:
            self.radio_3d.setChecked(True)

        """Update settings button"""
        self.button_update_settings = QtWidgets.QPushButton(main_window)
        self.button_update_settings.setGeometry(QtCore.QRect(270, 530, 130, 32))
        self.button_update_settings.setObjectName("button_update_settings")
        self.button_update_settings.clicked.connect(self.update_button_click)  # button event

        """Separation line"""
        self.line = QtWidgets.QFrame(main_window)
        self.line.setGeometry(QtCore.QRect(430, 100, 20, 621))
        self.line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")

        """--------------Label Actions--------------"""
        self.l_actions = QtWidgets.QLabel(main_window)
        self.l_actions.setGeometry(QtCore.QRect(610, 90, 81, 21))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self.l_actions.setFont(font)
        self.l_actions.setObjectName("l_actions")

        """Close button"""
        self.button_close = QtWidgets.QPushButton(main_window)
        self.button_close.setGeometry(QtCore.QRect(680, 530, 104, 32))
        self.button_close.setObjectName("button_close")
        self.button_close.clicked.connect(self.close_button_click)  # button event

        """EEG simulation button"""
        self.button_eeg_sim = QtWidgets.QPushButton(main_window)
        self.button_eeg_sim.setGeometry(QtCore.QRect(570, 150, 160, 32))
        self.button_eeg_sim.setObjectName("button_EEG_sim")
        self.button_eeg_sim.clicked.connect(self.eeg_sim_button_click)  # button event

        """Opem stream viewer button"""
        self.button_stream_viewer = QtWidgets.QPushButton(main_window)
        self.button_stream_viewer.setGeometry(QtCore.QRect(570, 200, 160, 32))
        self.button_stream_viewer.setObjectName("button_LSL_check")
        self.button_stream_viewer.clicked.connect(self.stream_viewer_button_click)  # button event

        """Start LSL recorder button"""
        self.button_lsl_recorder = QtWidgets.QPushButton(main_window)
        self.button_lsl_recorder.setGeometry(QtCore.QRect(570, 250, 160, 32))
        self.button_lsl_recorder.setObjectName("button_LSL_recorder")
        self.button_lsl_recorder.clicked.connect(self.lsl_recorder_button_click)  # button event

        """Open BCI button"""
        self.button_open_bci = QtWidgets.QPushButton(main_window)
        self.button_open_bci.setGeometry(QtCore.QRect(570, 350, 160, 32))
        self.button_open_bci.setObjectName("button_open_BCI")
        self.button_open_bci.clicked.connect(self.open_button_click)  # button event

        """Start feedback button"""
        self.button_start_fb = QtWidgets.QPushButton(main_window)
        self.button_start_fb.setGeometry(QtCore.QRect(570, 300, 160, 32))
        self.button_start_fb.setObjectName("button_start_FB")
        self.button_start_fb.clicked.connect(self.start_fb_button_click)  # button event

        """Train classifier button"""
        self.button_train_classifier = QtWidgets.QPushButton(main_window)
        self.button_train_classifier.setGeometry(QtCore.QRect(570, 400, 160, 32))
        self.button_train_classifier.setObjectName("button_train_classifier")
        self.button_train_classifier.clicked.connect(self.train_button_click)  # button event

        """Calculate results button"""
        self.button_calc_results = QtWidgets.QPushButton(main_window)
        self.button_calc_results.setGeometry(QtCore.QRect(570, 450, 160, 32))
        self.button_calc_results.setObjectName("button_train_classifier")
        self.button_calc_results.clicked.connect(self.calc_results_button_click)  # button event

        self.retranslate_ui(main_window)
        QtCore.QMetaObject.connectSlotsByName(main_window)

    def retranslate_ui(self, main_window):
        _translate = QtCore.QCoreApplication.translate
        main_window.setWindowTitle(_translate("main_window", "BCI User Interface"))
        self.l_title.setText(_translate("main_window", "2D & 3D Visualization of EEG-Based BCI"))
        self.label_id.setText(_translate("main_window", "Subject ID:"))
        # self.label_total_runs.setText(_translate("main_window", "Number of runs (total):"))
        self.label_task.setText(_translate("main_window", "Number of tasks per run (total):"))
        self.label_session.setText(_translate("main_window", "Current session number:"))
        self.label_run.setText(_translate("main_window", "Current run number:"))
        self.radio_mi.setText(_translate("main_window", "Motor imagery"))
        self.radio_me.setText(_translate("main_window", "Motor execution"))
        # self.radio_fb_on.setText(_translate("main_window", "Feedback ON"))
        # self.radio_fb_off.setText(_translate("main_window", "Feedback OFF"))
        # self.radio_erds_single.setText(_translate("main_window", "ERDS: single channel"))
        # self.radio_erds_average.setText(_translate("main_window", "ERDS: average channels"))
        self.l_input.setText(_translate("main_window", "Input"))
        self.l_actions.setText(_translate("main_window", "Actions"))
        self.button_close.setText(_translate("main_window", "Close"))
        self.button_eeg_sim.setText(_translate("main_window", "EEG Simulation"))
        self.button_stream_viewer.setText(_translate("main_window", "Open Stream Viewer"))
        self.button_open_bci.setText(_translate("main_window", "Open Unity Game"))
        self.button_lsl_recorder.setText(_translate("main_window", "Open Lab Recorder"))
        self.button_train_classifier.setText(_translate("main_window", "Train Classifier"))
        self.button_calc_results.setText(_translate("main_window", "Calculate Results"))
        self.button_start_fb.setText(_translate("main_window", "Start Feedback Model"))
        self.radio_2d.setText(_translate("main_window", "2D"))
        self.radio_3d.setText(_translate("main_window", "3D"))
        self.button_update_settings.setText(_translate("main_window", "Update Settings"))


if __name__ == "__main__":
    current_config = bci_config.read_bci_config()
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QDialog()
    ui = UiUserInterface()
    ui.setup_ui(MainWindow, current_config)
    MainWindow.show()
    sys.exit(app.exec_())
    