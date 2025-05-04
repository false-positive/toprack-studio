using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;

/// <summary>
/// Displays a simple static UI panel in front of the user with a single button to toggle placement mode.
/// The panel follows the camera by being parented directly to it.
/// </summary>
public class VRPlacementInterface : MonoBehaviour
{
    [Header("References")]
    [Tooltip("SpacePointPlacement script to enable or disable placement mode.")]
    [SerializeField] private SpacePointPlacement placementScript;

    [Header("UI Settings")]
    [Tooltip("Distance in meters in front of the camera where the panel appears.")]
    [SerializeField] private float panelDistance = 1.2f;

    [Tooltip("Size of the panel in meters (width, height).")]
    [SerializeField] private Vector2 panelSize = new Vector2(0.6f, 0.4f);

    [Tooltip("Size of the toggle button within the panel (width, height).")]
    [SerializeField] private Vector2 buttonSize = new Vector2(0.3f, 0.15f);

    private Canvas _canvas;
    private Button _toggleButton;
    private Text _buttonLabel;

    void Awake()
    {
        if (placementScript == null)
        {
            Debug.LogError("VRPlacementInterface: Please assign a SpacePointPlacement reference.");
            enabled = false;
            return;
        }

        EnsureEventSystem();
        CreatePanelUI();
        UpdateButtonVisual();
    }

    private void CreatePanelUI()
    {
        // Find or get the main camera transform
        Transform cam = Camera.main ? Camera.main.transform : null;
        if (cam == null)
        {
            var rig = FindObjectOfType<OVRCameraRig>();
            cam = rig ? rig.centerEyeAnchor : null;
        }
        if (cam == null) return;

        // Create world-space canvas
        GameObject canvasGO = new GameObject("VRPlacementPanel");
        canvasGO.transform.SetParent(cam, false);
        canvasGO.transform.localPosition = Vector3.forward * panelDistance;
        canvasGO.transform.localRotation = Quaternion.identity;
        canvasGO.transform.localScale = Vector3.one;

        _canvas = canvasGO.AddComponent<Canvas>();
        _canvas.renderMode = RenderMode.WorldSpace;
        _canvas.worldCamera = cam.GetComponentInParent<Camera>();
        canvasGO.AddComponent<GraphicRaycaster>();
        var scaler = canvasGO.AddComponent<CanvasScaler>();
        scaler.dynamicPixelsPerUnit = 100;

        // Size of the panel
        var crt = canvasGO.GetComponent<RectTransform>();
        crt.sizeDelta = panelSize;

        // Background Image
        GameObject bgGO = new GameObject("Background");
        bgGO.transform.SetParent(canvasGO.transform, false);
        var bgImage = bgGO.AddComponent<Image>();
        bgImage.color = new Color(0f, 0f, 0f, 0.75f);
        var bgRT = bgGO.GetComponent<RectTransform>();
        bgRT.anchorMin = new Vector2(0f, 0f);
        bgRT.anchorMax = new Vector2(1f, 1f);
        bgRT.offsetMin = bgRT.offsetMax = Vector2.zero;

        // Toggle Button
        GameObject btnGO = new GameObject("PlacementToggleButton");
        btnGO.transform.SetParent(canvasGO.transform, false);
        var btnRT = btnGO.AddComponent<RectTransform>();
        btnRT.sizeDelta = buttonSize;
        btnRT.anchoredPosition = Vector2.zero; // center of panel

        _toggleButton = btnGO.AddComponent<Button>();
        _toggleButton.transition = Selectable.Transition.ColorTint;
        var colors = _toggleButton.colors;
        colors.normalColor = Color.white;
        colors.highlightedColor = new Color(0.8f, 0.8f, 1f);
        colors.pressedColor = Color.gray;
        _toggleButton.colors = colors;
        _toggleButton.onClick.AddListener(OnToggleClicked);

        _buttonLabel = new GameObject("Label").AddComponent<Text>();
        _buttonLabel.transform.SetParent(btnGO.transform, false);
        _buttonLabel.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        _buttonLabel.alignment = TextAnchor.MiddleCenter;
        _buttonLabel.color = Color.black;
        _buttonLabel.fontSize = 48;
        var lblRT = _buttonLabel.GetComponent<RectTransform>();
        lblRT.anchorMin = new Vector2(0f, 0f);
        lblRT.anchorMax = new Vector2(1f, 1f);
        lblRT.offsetMin = lblRT.offsetMax = Vector2.zero;
    }

    private void OnToggleClicked()
    {
        placementScript.enabled = !placementScript.enabled;
        UpdateButtonVisual();
    }

    private void UpdateButtonVisual()
    {
        _buttonLabel.text = placementScript.enabled ? "Disable" : "Enable";
    }

    private static void EnsureEventSystem()
    {
        if (FindObjectOfType<EventSystem>() == null)
        {
            var esGO = new GameObject("EventSystem");
            esGO.AddComponent<EventSystem>();
            esGO.AddComponent<InputSystemUIInputModule>();
        }
    }
}
