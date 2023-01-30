# README

## Content of the repository
```FeedbackModel```:
This folder contains the Python scripts for the feedback model.

```VRFeedback```:
This folder contains the unity project.

```bci-config.json```:
Contains all necessary settings for the feedback model and the VR environment:
- general-settings: lsl streams, timing of the experiment
- feedback-model-settings: bandpass, erds
- eeg-settings: sample rate, channels

## Workflow

### EEG
For testing purposes an eeg signal can be simulated by executing the script ``FeedbackModel/eeg_simulation.py``. Settings for the simulated signal (sample rate, channels etc.) can be changed in ``FeedbackModel/signalserver/configs/eegsim.xml``.

### Feedback Model
The dependencies for the feedback model can be installed with ``pip install requirements.txt``. 

The feedback model is started by executing ``FeedbackModel/feedback_model.py``.
The script requires following input files:
- ``bci-config.json`` (make sure all settings are correct before starting the script)
- ``FeedbackModel/data/CSP_LDA/csp.mat`` (common spatial pattern weights)
- ``FeedbackModel/data/CSP_LDA/lda.mat`` (linear discriminant analysis coefficients)

For computing these *.mat files the following steps are necessary:
- Run the game (see [VR Environment](#vr-environment)) once without feedback and record the eeg and marker LSL streams (written to a .xdf file).
- Execute ``FeedbackModel/xdf_to_mat.py``. It reads the xdf file and creates a ``messung.mat`` file.
- Run ``FeedbackModel/compute_csp_lda.py``. It takes ``messung.mat`` as input and computes the CSP and LDA coefficients.

### VR Environment
Open the project ``VRFeedback`` in Unity. Make sure the VR headset (HTC Vive) is connected and that you are logged into SteamVR.

In case the scene ``NeuronSphere`` is not visible it must be opened: ``File->Open Scene`` (the path of the scene is ``VRFeedback/Assets/Scenes/NeuronSphere.unity``).
In the Inspector tab of the ``ScenarioController`` there are 2 important variables which must be set before the "game" is started:
- Number Run: the number of the text file with a random order of the tasks (``VRFeedback/Assets/Resources/run_x.txt``, created by ``FeedbackModel/sequence_generator.py``)
- Show Feedback: if checked, the game feedback will be shown to the user (run ``FeedbackModel/feedback_model.py`` before starting the game)

After starting the game (click on the play button) the VR environment can be seen in the VR headset and in the Game view. 

Now it is important to check that all LSL streams are available in the Lab Recorder (the names should be the same as in ``bci-config.json``). If the participant is ready start recording all LSL streams via the Lab Recorder. Then the session can be started by checking ``Start Session`` in the Inspector tab of the ``ScenarioController`` in Unity.

