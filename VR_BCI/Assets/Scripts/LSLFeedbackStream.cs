using UnityEngine;
using LSL;
using System;
using System.Collections;

/// <summary>
/// Receives and processes the LSL stream containing the computed class labels and the distance.
/// </summary>
public class LSLFeedbackStream : MonoBehaviour
{
    string lslStreamName;
    liblsl.StreamInfo[] streamInfos;
    liblsl.StreamInlet streamInlet;
    float[] sample;
    int channelCount = 0;

    private uint currentCondition;	
	public uint CurrentCondition{get{return currentCondition;} set{currentCondition = value;}}

    /// <summary>
    /// Reads the name of the LSL stream from the ScenarioController instance.
    /// Is called on the frame when a script is enabled just before any of the Update methods are called the first time.
    /// </summary>
    void Start()
    {
        lslStreamName = ScenarioController.instance.LSLStreamNameFbCl;
    }

    /// <summary>
    /// Resolves and opens the LSL stream.
    /// </summary>
    public bool Initialize()
    {
        Debug.Log("Initialize Feedback");
        bool initialized = false;

        if (streamInlet != null)
        {
            Debug.Log("INFO: Feedback stream is already resolved!");
            return initialized;
        }
        if (string.IsNullOrEmpty(lslStreamName))
		{
			Debug.Log("ERROR: No name for the LSL feedback stream was provided!");
			return initialized;
		}
        
        try
        {
            streamInfos = liblsl.resolve_stream("name", lslStreamName, 1, 10.0f);
        }
        catch (TimeoutException)
        {
            Debug.Log("ERROR: Timeout resolving LSL feedback stream!");
            return initialized;
        }

        if (streamInfos.Length == 0 || streamInfos[0] == null)
        {
            Debug.Log("ERROR: LSL feedback stream could not be resolved!");
            return initialized;
        }

        streamInlet = new liblsl.StreamInlet(streamInfos[0]);
        channelCount = streamInlet.info().channel_count();
        streamInlet.open_stream();
        initialized = true;

        Debug.Log("Finish Initialize Feedback");

        return initialized;
    }

    /// <summary>
    /// Pulls a sample from the LSL stream.
    /// Is called every frame, if the MonoBehaviour is enabled. 
    /// </summary>
    void Update()
    {
        if (streamInlet == null)
            return;

        sample = new float[channelCount];
        double lastTimeStamp = streamInlet.pull_sample(sample, 0.0f);
        if (lastTimeStamp != 0.0)
        {
            Process(sample, lastTimeStamp);
            while ((lastTimeStamp = streamInlet.pull_sample(sample, 0.0f)) != 0)
            {
                Process(sample, lastTimeStamp);
            }
        } 
    }

    /// <summary>
    /// Triggers an event to update the colour and instensity of the outline glow of the brain object.
    /// </summary>
    void Process(float[] newSample, double timeStamp)
    {  
        bool is_classifier_correctly = (uint) newSample[0] == currentCondition;
        
        EventManager.instance.OnTriggerUpdateOutline(newSample[1], is_classifier_correctly);
    }

}