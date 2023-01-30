using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using UnityEngine.SceneManagement;

/// <summary>
/// Controls the whole scenario: timing of the markers, triggering of the events.
/// </summary>
public class ScenarioController : MonoBehaviour
{
    public static ScenarioController instance;
	// const string PathConfig = "Assets/../../bci-config.json";
	// const string Path = "Assets/Resources/run_";
	const string PathConfig = "Assets/../../bci-config.json";
	const string Path = "Assets/../../SubjectData/current/run_";

	// public int numberRun = 1;
	public bool showFeedback = false;
	private bool startSession = true; // false;

	public enum AllConditions
	{
		LEFT_HAND=0,
		RIGHT_HAND
	};

	// ------------- private variables -------------
	
	int round = -1;
	uint condition;
	float[] timeBreak = new float[2];

	WaitForSecondsRealtime waitSecondsRef;
	WaitForSecondsRealtime waitSecondsCue;
	WaitForSecondsRealtime waitSecondsFb;
	private string lslStreamNameMarker;
	private string lslStreamIdMarker;
	private string lslStreamNameFbCl;
	private string lslStreamNameFbErds;
	System.Random random = new System.Random();

	Dictionary<string, uint> ConditionStrToInt = new Dictionary<string, uint> 
	{
		{ "l", (uint)AllConditions.LEFT_HAND },
		{ "r", (uint)AllConditions.RIGHT_HAND }
	};

	Dictionary<uint, string> ConditionIntToStr = new Dictionary<uint, string> 
	{
		{ (uint)AllConditions.LEFT_HAND, "l"},
		{ (uint)AllConditions.RIGHT_HAND, "r"}
	};

	// ------------- internal variables -------------
	internal List<string> blockSequence;
	internal LSLFeedbackStream feedbackStream;
	internal LSLErdsStream erdsStream;

	public string LSLStreamNameMarker{get{return lslStreamNameMarker;} set{lslStreamNameMarker = value;}}
	public string LSLStreamIdMarker{get{return lslStreamIdMarker;} set{lslStreamIdMarker = value;}}
	public string LSLStreamNameFbCl{get{return lslStreamNameFbCl;} set{lslStreamNameFbCl = value;}}
	public string LSLStreamNameFbErds{get{return lslStreamNameFbErds;} set{lslStreamNameFbErds = value;}}

    /// <summary>
    /// Makes the class a singleton and reads the configuration. 
    /// Is called when the script object is initialised (even if the script is not enabled).
    /// </summary>
	void Awake()
	{
		if (instance == null)
            instance = this;
        else
            Destroy(this);

        LoadConfiguration();
	}

    /// <summary>
    /// Reads the configuration file (timing, LSL names) and the order of the tasks.
    /// </summary>
	void LoadConfiguration()
	{
		try
		{
			string jsonString = File.ReadAllText(PathConfig);
			var obj = (JObject)JsonConvert.DeserializeObject(jsonString);

			int numberRun = obj["gui-input-settings"]["n-run"].Value<int>();
			string feedback = obj["gui-input-settings"]["fb-mode"].Value<string>();

			if (feedback == "on")
			{
				showFeedback = true;
			}
			else
            {
				showFeedback = false;

			}

			blockSequence = new List<String>(File.ReadAllLines(Path + numberRun + ".txt"));

			waitSecondsRef = new WaitForSecondsRealtime(obj["general-settings"]["timing"]["duration-ref"].Value<float>());
			waitSecondsCue = new WaitForSecondsRealtime(obj["general-settings"]["timing"]["duration-cue"].Value<float>());
			waitSecondsFb = new WaitForSecondsRealtime(obj["general-settings"]["timing"]["duration-task"].Value<float>());

			JArray timeB = obj["general-settings"]["timing"]["duration-break"].Value<JArray>();
			timeBreak[0] = timeB[0].Value<float>();
			timeBreak[1] = timeB[1].Value<float>();

			LSLStreamNameFbCl = obj["general-settings"]["lsl-streams"]["fb-lda"]["name"].Value<string>();
			LSLStreamNameMarker = obj["general-settings"]["lsl-streams"]["marker"]["name"].Value<string>();
			LSLStreamIdMarker = obj["general-settings"]["lsl-streams"]["marker"]["id"].Value<string>();
			LSLStreamNameFbErds = obj["general-settings"]["lsl-streams"]["fb-erds"]["name"].Value<string>();
		}
		catch(Exception ex)
        {
			Debug.LogError(ex);
        }
	}
	
	/// <summary>
    /// Waits until the session is started by the user.
    /// Is called on the frame when a script is enabled just before any of the Update methods are called the first time.
    /// </summary>
    IEnumerator Start()
    {
		Debug.Log("INFO: Wait until session is started by user...");

		yield return new WaitUntil(() => startSession == true);

		StartBlock();
	}

    /// <summary>
    /// Starts a session/block of trials. If feedback is enabled it initializes the feedback streams.
    /// </summary>
    public void StartBlock()
    {
		if (showFeedback)
		{
			feedbackStream = gameObject.GetComponent<LSLFeedbackStream>();
			erdsStream = gameObject.GetComponent<LSLErdsStream>();

			bool fb_initialized = feedbackStream.Initialize() && erdsStream.Initialize();

			if (!fb_initialized)
				QuitGame();
		} 

		round = 0;
		UpdateCondition();
		EventManager.instance.OnTriggerSessionStarted();
		StartCoroutine(StartTrial());
    }

    /// <summary>
    /// Starts a trial and times the trigger of events. 
    /// </summary>
	public IEnumerator StartTrial()
    {
		yield return new WaitForSecondsRealtime(NextFloat(timeBreak));

		EventManager.instance.OnTriggerTrialStarted(ConditionIntToStr[condition]);

        EventManager.instance.OnTriggerReference();
        yield return waitSecondsRef;

        EventManager.instance.OnTriggerCue(condition);
        yield return waitSecondsCue;

        EventManager.instance.OnTriggerFeedback(condition);
		yield return waitSecondsFb;

		EventManager.instance.OnTriggerTrialEnd();

		EndTrial();		
    }
	
	/// <summary>
    /// Ends a trial. If all tasks are completed it finishes the block. Otherwise the next trial is started. 
    /// </summary>
	void EndTrial()
    {		
        round = round + 1;
        if (round >= blockSequence.Count)
            BlockFinished();
        else
        {
            UpdateCondition();
			StartCoroutine(StartTrial());
        }        
    }

    /// <summary>
    /// Updates the current condition/task.
    /// </summary>
	void UpdateCondition()
	{
		condition = ConditionStrToInt[blockSequence[round]];
		if (showFeedback)
			feedbackStream.CurrentCondition = condition;
	}

    /// <summary>
    /// Returns a random value in the provided range.
    /// </summary>
	float NextFloat(float[] range)
	{
		double val = (random.NextDouble() * (range[1] - range[0]) + range[0]);
		return (float)val;
	}
	
	/// <summary>
    /// Triggers the "session finished" event.
    /// </summary>
	void BlockFinished() 
    {
		startSession = false;
		EventManager.instance.OnTriggerSessionFinished();
    }

    /// <summary>
    /// Quits the game.
    /// </summary>
	public void QuitGame()
    {
#if UNITY_EDITOR
			UnityEditor.EditorApplication.isPlaying = false;
#else
		SceneManager.LoadScene("MainMenu");

		// Application.Quit();
		#endif
    }

}
