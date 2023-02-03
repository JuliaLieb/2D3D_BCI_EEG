
using UnityEngine;

/// <summary>
/// Observer class. Controls the texture of the brain object.
/// </summary>
public class TextureController : MonoBehaviour
{
    public GameObject leftHemisphere;
    public GameObject rightHemisphere;

    public GameObject leftHemisphereGlow;
    public GameObject rightHemisphereGlow;

    Material materialLeftH;
    Material materialRightH;
    Material[] materialsGlow = new Material[2];

    public Color emissiveColorTrue;
    public Color emissiveColorFalse;
    public Color emmissivecolorNeutral;

    float[] lastERDSValues = new float[6];

    int updatedSamples = 0;

    /// <summary>
    /// Gets access to the material of the brain object.
    /// Is called when the script object is initialised (even if the script is not enabled).
    /// </summary>
    void Awake()
    {
        MeshRenderer leftHMeshRenderer = leftHemisphere.GetComponent<MeshRenderer>();
        MeshRenderer rightHMeshRenderer = rightHemisphere.GetComponent<MeshRenderer>();

        materialLeftH = leftHMeshRenderer.material;
        materialRightH = rightHMeshRenderer.material;

        materialsGlow[0] = leftHemisphereGlow.GetComponent<MeshRenderer>().material;
        materialsGlow[1] = rightHemisphereGlow.GetComponent<MeshRenderer>().material;
    }

    void Start()
    {
        EventManager.instance.ResetObjects += ResetTexture;
        EventManager.instance.TrialEnd += ResetTexture;
        EventManager.instance.UpdateOutline += GlowIntensity;
        EventManager.instance.UpdateSurface += UpdateERDSValues;

        ResetTexture();
    }

    /// <summary>
    /// Resets the materials to default values.
    /// </summary>
    public void ResetTexture()
    {
        foreach (var mat in materialsGlow)
            mat.SetColor("_colorGlow", emmissivecolorNeutral * 1);

        for (int i = 0; i<6; i++)
            lastERDSValues[i] = 0.0f;

        materialLeftH.SetFloat("_colorValueRoi1", lastERDSValues[0]);
        materialLeftH.SetFloat("_colorValueRoi3", lastERDSValues[2]);
        materialLeftH.SetFloat("_colorValueRoi5", lastERDSValues[4]);

        materialRightH.SetFloat("_colorValueRoi2", lastERDSValues[1]);
        materialRightH.SetFloat("_colorValueRoi4", lastERDSValues[3]);
        materialRightH.SetFloat("_colorValueRoi6", lastERDSValues[5]);

        updatedSamples = 0;
    }

    /// <summary>
    /// Sets the colour and and the intensity of the emission for the outline glow.
    /// </summary>
    public void GlowIntensity(float intensity, bool is_correct)
    {
        Color currentColor;
        
        if (is_correct)
        {
            intensity *= 1.5f;
            currentColor = emissiveColorTrue;
        } 
        else
            currentColor = emissiveColorFalse;

        foreach (var mat in materialsGlow)
            mat.SetColor("_colorGlow", currentColor * intensity);
    }

    /// <summary>
    /// Updates the colour for each region of interest if the threshold is exceeded.
    /// </summary>
    public void UpdateERDSValues(float[] values)
    {
        // Update rate is too fast: skip a few samples
        updatedSamples += 1;
        if (updatedSamples % 150 != 0)
            return;

        float threshold = 0.05f;

        if (Mathf.Abs(lastERDSValues[0] - values[0]) > threshold)
        {
            materialLeftH.SetFloat("_colorValueRoi1", values[0]);
            lastERDSValues[0] = values[0];
        }
        if (Mathf.Abs(lastERDSValues[1] - values[1]) > threshold)
        {
            materialRightH.SetFloat("_colorValueRoi2", values[1]);
            lastERDSValues[1] = values[1];
        }
        if (Mathf.Abs(lastERDSValues[2] - values[2]) > threshold)
        {
            materialLeftH.SetFloat("_colorValueRoi3", values[2]);
            lastERDSValues[2] = values[2];
        }
        if (Mathf.Abs(lastERDSValues[3] - values[3]) > threshold)
        {
            materialRightH.SetFloat("_colorValueRoi4", values[3]);
            lastERDSValues[3] = values[3];
        }
        if (Mathf.Abs(lastERDSValues[4] - values[4]) > threshold)
        {
            materialLeftH.SetFloat("_colorValueRoi5", values[4]);
            lastERDSValues[4] = values[4];
        }
        if (Mathf.Abs(lastERDSValues[5] - values[5]) > threshold)
        {
            materialRightH.SetFloat("_colorValueRoi6", values[5]);
            lastERDSValues[5] = values[5];
        }
    }
}
