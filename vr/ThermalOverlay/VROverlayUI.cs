using UnityEngine;
using UnityEngine.UI;

/// <summary>
/// Displays a 2D image as a persistent overlay fixed in front of the VR camera using a World Space Canvas.
/// Transparency will work correctly with UI rendering.
/// Attach this script anywhere; assign your Texture2D in the inspector.
/// </summary>
public class PersistentImageOverlay : MonoBehaviour
{
    [Header("Overlay Image Settings")]
    [Tooltip("The 2D texture to display as an overlay.")]
    [SerializeField] private Texture2D overlayTexture;
    [Tooltip("Distance in meters in front of the camera to position the overlay.")]
    [SerializeField] private float distance = 1.0f;
    [Tooltip("Size (in meters) of the overlay plane width and height.")]
    [SerializeField] private Vector2 size = new Vector2(1.0f, 1.0f);
    [Tooltip("Opacity of the overlay (0 transparent, 1 opaque).")]
    [Range(0f, 1f)]
    [SerializeField] private float opacity = 1.0f;

    private Transform cameraTransform;
    private Canvas worldCanvas;
    private RawImage rawImage;

    void Start()
    {
        if (overlayTexture == null)
        {
            Debug.LogError("PersistentImageOverlay: overlayTexture not assigned.");
            enabled = false;
            return;
        }

        // Find VR camera (center eye anchor or main)
        var rig = Object.FindFirstObjectByType<OVRCameraRig>();
        if (rig != null && rig.centerEyeAnchor != null)
            cameraTransform = rig.centerEyeAnchor;
        else if (Camera.main != null)
            cameraTransform = Camera.main.transform;
        else
        {
            Debug.LogError("PersistentImageOverlay: No camera transform found.");
            enabled = false;
            return;
        }

        // Create World Space Canvas
        GameObject canvasGO = new GameObject("PersistentOverlayCanvas");
        canvasGO.transform.SetParent(cameraTransform, false);
        worldCanvas = canvasGO.AddComponent<Canvas>();
        worldCanvas.renderMode = RenderMode.WorldSpace;
        worldCanvas.worldCamera = cameraTransform.GetComponentInParent<Camera>() ?? Camera.main;
        worldCanvas.planeDistance = distance;
        canvasGO.AddComponent<CanvasScaler>();
        canvasGO.AddComponent<GraphicRaycaster>();

        // Set Canvas size
        RectTransform canvasRT = worldCanvas.GetComponent<RectTransform>();
        canvasRT.sizeDelta = size;

        // Create RawImage child
        GameObject imgGO = new GameObject("OverlayImage");
        imgGO.transform.SetParent(canvasGO.transform, false);
        rawImage = imgGO.AddComponent<RawImage>();
        rawImage.texture = overlayTexture;
        rawImage.color = new Color(1f, 1f, 1f, opacity);

        // Stretch RawImage to fill Canvas
        RectTransform imgRT = rawImage.rectTransform;
        imgRT.anchorMin = new Vector2(0f, 0f);
        imgRT.anchorMax = new Vector2(1f, 1f);
        imgRT.offsetMin = Vector2.zero;
        imgRT.offsetMax = Vector2.zero;
    }

    void Update()
    {
        if (worldCanvas == null || cameraTransform == null)
            return;

        // Position canvas always in front of camera
        worldCanvas.transform.position = cameraTransform.position + cameraTransform.forward * distance;
        worldCanvas.transform.rotation = cameraTransform.rotation;

        // Update opacity
        if (rawImage != null)
        {
            Color c = rawImage.color;
            c.a = opacity;
            rawImage.color = c;
        }
    }

    /// <summary>
    /// Toggles overlay visibility.
    /// </summary>
    public void SetOverlayVisible(bool visible)
    {
        if (worldCanvas != null)
            worldCanvas.gameObject.SetActive(visible);
    }
}
