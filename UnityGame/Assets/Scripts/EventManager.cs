using UnityEngine;
using System;

/// <summary>
/// The EventManager handles event actions.
/// </summary>
public class EventManager : MonoBehaviour
{
    public static EventManager instance;

    /// <summary>
    /// Makes the class a singleton.
    /// Is called when the script object is initialised (even if the script is not enabled).
    /// </summary>
    private void Awake()
    {
        if (instance == null)
            instance = this;
        else
            Destroy(this);
    }

    public event Action SessionStarted;
    public event Action SessionFinished;
    public event Action<string> TrialStart;
    public event Action Reference;
    public event Action<uint> Cue;
    public event Action<uint> Feedback;
    public event Action TrialEnd;
    public event Action ResetObjects;
    public event Action<float, bool> UpdateOutline;
    public event Action<float[]> UpdateSurface;


    public void OnTriggerSessionStarted()
    {
        SessionStarted?.Invoke();
    }
    public void OnTriggerSessionFinished()
    {
        SessionFinished?.Invoke();
    }
    public void OnTriggerTrialStarted(string condition)
    {
        TrialStart?.Invoke(condition);
    }
    public void OnTriggerReference()
    {
        Reference?.Invoke();
    }

    public void OnTriggerCue(uint condition)
    {
        Cue?.Invoke(condition);
    }

    public void OnTriggerFeedback(uint condition)
    {
        Feedback?.Invoke(condition);
    }

    public void OnTriggerTrialEnd()
    {
        TrialEnd?.Invoke();
    }

    public void OnTriggerResetObjects()
    {
        ResetObjects?.Invoke();
    }

    public void OnTriggerUpdateOutline(float distance, bool is_correct)
    {
        UpdateOutline?.Invoke(distance, is_correct);
    }

    public void OnTriggerUpdateSurface(float[] values)
    {
        UpdateSurface?.Invoke(values);
    }
}
