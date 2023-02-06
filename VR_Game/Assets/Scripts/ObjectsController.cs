using UnityEngine;

/// <summary>
/// Observer class. Handles objects based on events.
/// </summary>
public class ObjectsController : MonoBehaviour
{
    public GameObject fixationCross;
    public GameObject arrowLeft;
	public GameObject arrowRight;
	public GameObject brain;
    public GameObject glow;

    /// <summary>
    /// Called once at start of game and subscribes methods to the events.
    /// </summary>
    void Start()
    {
        // Subscribe methods to events
        EventManager.instance.Reference += OnReference;
        EventManager.instance.Cue += OnCue;
        EventManager.instance.Feedback += OnFeedback;
        EventManager.instance.TrialEnd += OnResetObjects;
        EventManager.instance.ResetObjects += OnResetObjects;

        OnResetObjects();
    }

    /// <summary>
    /// Handles what happens on reference time of each trial.
    /// </summary>
    void OnReference()
    {
        fixationCross.SetActive(true);
    }

    /// <summary>
    /// Handles what happens on cue time of each trial.
    /// </summary>
    void OnCue(uint condition)
    {
        if (condition == (uint)ScenarioController.AllConditions.LEFT_HAND)
            arrowLeft.SetActive(true);
        else if (condition == (uint)ScenarioController.AllConditions.RIGHT_HAND)
            arrowRight.SetActive(true);
    }

    /// <summary>
    /// Handles what happens on feedback time of each trial.
    /// </summary>
    void OnFeedback(uint condition)
    {
        if (!ScenarioController.instance.showFeedback)
            return;

        fixationCross.SetActive(false);
        brain.SetActive(true);
        glow.SetActive(true);
    }

    /// <summary>
    /// Hides all objects.
    /// </summary>
    public void OnResetObjects()
	{
        fixationCross.SetActive(false);
		arrowLeft.SetActive(false);
		arrowRight.SetActive(false);
		brain.SetActive(false);
        glow.SetActive(false);	
	}
}
