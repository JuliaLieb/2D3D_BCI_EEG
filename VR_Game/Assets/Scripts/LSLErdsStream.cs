using UnityEngine;
using LSL;
using System;
using System.Collections;

/// <summary>
/// Receives and processes the LSL stream containing ERDS values.
/// </summary>
public class LSLErdsStream : MonoBehaviour
{
    string lslStreamName;
    liblsl.StreamInlet streamInlet;
    liblsl.StreamInfo[] streamInfos;
    float[] sample;
    int channelCount = 0;

    /// <summary>
    /// Reads the name of the LSL stream from the ScenarioController instance.
    /// Is called on the frame when a script is enabled just before any of the Update methods are called the first time.
    /// </summary>
    void Start()
    {
        lslStreamName = ScenarioController.instance.LSLStreamNameFbErds;
    }

    /// <summary>
    /// Resolves and opens the LSL stream.
    /// </summary>
    public bool Initialize()
    {
        bool initialized = false;

        if (streamInlet != null)
        {
            Debug.Log("INFO: ERDS stream is already resolved!");
            return initialized;
        }
        if (string.IsNullOrEmpty(lslStreamName))
		{
			Debug.Log("ERROR: No name for the LSL ERDS stream was provided!");
			return initialized;
		}
                
        try
        {
            streamInfos = liblsl.resolve_stream("name", lslStreamName, 1, 10.0f);
        }
        catch (TimeoutException)
        {
            Debug.Log("ERROR: Timeout resolving LSL ERDS stream!");
            return initialized;
        }

        if (streamInfos.Length == 0 || streamInfos[0] == null)
        {
            Debug.Log("ERROR: LSL ERDS stream could not be resolved!");
            return initialized;
        }

        streamInlet = new liblsl.StreamInlet(streamInfos[0]);
        channelCount = streamInlet.info().channel_count();
        streamInlet.open_stream();
        initialized = true;
        
        Debug.Log("Finish Initialize ERDS");

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
    /// Triggers an event to update the colour on the brain object.
    /// </summary>
    void Process(float[] newSample, double timeStamp)
    {
        EventManager.instance.OnTriggerUpdateSurface(newSample);
    }
}