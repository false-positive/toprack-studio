using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

/// <summary>
/// Visualizes a persistent selection ray from the right-hand controller using a LineRenderer.
/// Attach this script to any GameObject; it will create and update a LineRenderer each frame.
/// </summary>
[RequireComponent(typeof(LineRenderer))]
public class ControllerRayVisualizer : MonoBehaviour
{
    [Tooltip("Which controller to track (default: Right Touch).")]
    [SerializeField] private OVRInput.Controller controller = OVRInput.Controller.RTouch;
    [Tooltip("Maximum ray distance in meters.")]
    [SerializeField] private float maxDistance = 10f;
    [Tooltip("Layer mask for raycast hits (optional).")]
    [SerializeField] private LayerMask layerMask = ~0;

    private LineRenderer lineRenderer;

    void Awake()
    {
        lineRenderer = GetComponent<LineRenderer>();
        lineRenderer.positionCount = 2;
        lineRenderer.widthMultiplier = 0.005f;
        // Use a simple white material
        lineRenderer.material = new Material(Shader.Find("Unlit/Color")) { color = Color.green };
    }

    void Update()
    {
        // Get controller pose
        Vector3 origin = OVRInput.GetLocalControllerPosition(controller);
        Quaternion rot = OVRInput.GetLocalControllerRotation(controller);
        Vector3 dir = rot * Vector3.forward;

        // Perform raycast
        if (Physics.Raycast(origin, dir, out RaycastHit hit, maxDistance, layerMask))
        {
            lineRenderer.SetPosition(0, origin);
            lineRenderer.SetPosition(1, hit.point);
        }
        else
        {
            // No hit: draw full length
            lineRenderer.SetPosition(0, origin);
            lineRenderer.SetPosition(1, origin + dir * maxDistance);
        }
    }
}
