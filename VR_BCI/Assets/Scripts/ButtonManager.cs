using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>
/// Loads the Neuron Sphere Scene
/// </summary>
public class ButtonManager : MonoBehaviour
{
	public void MoveToNeuronSphere()
	{
		SceneManager.LoadScene("NeuronSphere");
	}
	public void Quit()
	{
		Application.Quit();
	}
}

