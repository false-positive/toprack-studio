using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Lets the user place control points on the floor with a VR controller.
/// When the backend display switches to "website" (polled via /api/display-control/),
/// editing is locked and all points are batch‑posted to
/// /api/datacenters/{dataCenterId}/update_points/ in centimetres.
/// </summary>
[RequireComponent(typeof(LineRenderer))]
public class SpacePointPlacement : MonoBehaviour
{
    [Header("References")]
    [SerializeField] private OVRCameraRig cameraRig;

    [Header("Prefabs & Materials")]
    [SerializeField] private GameObject visualPrefab;
    [SerializeField] private GameObject previewPrefab;
    [SerializeField] private Material lineMaterial;

    [Header("Ray & Floor")]
    [SerializeField] private float maxDistance = 10f;

    [Header("Interaction Settings")]
    [SerializeField] private OVRInput.Controller controller = OVRInput.Controller.RTouch;
    [SerializeField] private float selectThreshold = 0.2f;
    [SerializeField] private float hoverScale = 1.1f;
    [SerializeField] private float dragScale = 1.3f;

    [Header("Backend Settings")]
    [SerializeField] private int dataCenterId = 1;
    private const string DISPLAY_URL = "http://127.0.0.1:8000/api/display-control/";

    private LineRenderer line;
    private GameObject preview;
    private Transform parent;
    private Plane floorPlane;

    private readonly List<GameObject> points = new();
    private readonly Dictionary<GameObject, Vector3> baseScale = new();

    private GameObject hovered;
    private GameObject dragging;

    public bool Locked { get; private set; }

    private void Awake()
    {
        cameraRig ??= FindObjectOfType<OVRCameraRig>();
        if (!cameraRig) { Debug.LogError("SpacePointPlacement: OVRCameraRig missing"); enabled = false; return; }

        parent = new GameObject("ControlPoints").transform;
        parent.SetParent(transform);

        // floor from boundary
        float floorY = 0;
        var b = OVRManager.boundary;
        if (b != null && b.GetConfigured())
        {
            var pts = b.GetGeometry(OVRBoundary.BoundaryType.PlayArea);
            if (pts?.Length > 0) floorY = pts[0].y;
        }
        floorPlane = new Plane(Vector3.up, new Vector3(0, floorY, 0));

        // line renderer
        line = GetComponent<LineRenderer>();
        line.positionCount = 2; line.material = lineMaterial; line.widthMultiplier = 0.005f;

        // preview marker
        if (previewPrefab) { preview = Instantiate(previewPrefab, parent); preview.SetActive(false); }

        // start polling display state
        StartCoroutine(PollDisplayState());
    }

    private void Update()
    {
        if (Locked)
        {
            preview.SetActive(false);
            return;
        }
        // controller world ray
        var ts = cameraRig.trackingSpace;
        Vector3 origin = ts.TransformPoint(OVRInput.GetLocalControllerPosition(controller));
        Vector3 dir = ts.rotation * OVRInput.GetLocalControllerRotation(controller) * Vector3.forward;
        Ray ray = new(origin, dir);

        bool hitFloor = floorPlane.Raycast(ray, out float enter) && enter <= maxDistance;
        Vector3 hitPoint = hitFloor ? ray.GetPoint(enter) : Vector3.zero;

        // hover detection
        GameObject target = null;
        if (!dragging && hitFloor)
        {
            foreach (var p in points)
                if (Vector3.Distance(p.transform.position, hitPoint) <= selectThreshold) { target = p; break; }
        }
        UpdateHover(target);

        // preview marker
        if (preview)
            preview.SetActive(hitFloor && !dragging && hovered == null && !Locked);
        if (preview && preview.activeSelf) preview.transform.position = hitPoint;

        // line
        line.enabled = hitFloor;
        if (hitFloor) { line.SetPosition(0, origin); line.SetPosition(1, hitPoint); }

        // input logic
        if (!Locked)
        {
            if (dragging == null)
            {
                if (hovered && OVRInput.GetDown(OVRInput.Button.PrimaryIndexTrigger, controller))
                {
                    dragging = hovered;
                    dragging.transform.localScale = baseScale[dragging] * dragScale;
                }
                else if (hovered == null && hitFloor && OVRInput.GetDown(OVRInput.Button.PrimaryIndexTrigger, controller))
                {
                    SpawnPoint(hitPoint);
                }
            }
            else // dragging
            {
                if (hitFloor) dragging.transform.position = hitPoint;
                if (OVRInput.GetUp(OVRInput.Button.PrimaryIndexTrigger, controller))
                {
                    dragging.transform.localScale = baseScale[dragging];
                    dragging = null;
                }
            }
        }
    }

    private void SpawnPoint(Vector3 pos)
    {
        var go = visualPrefab ? Instantiate(visualPrefab, pos, Quaternion.identity, parent) : GameObject.CreatePrimitive(PrimitiveType.Sphere);
        if (!visualPrefab)
        {
            go.transform.SetParent(parent);
            go.transform.localScale = Vector3.one * 0.1f;
        }
        points.Add(go);
        baseScale[go] = go.transform.localScale;
    }

    private void UpdateHover(GameObject tgt)
    {
        if (hovered == tgt) return;
        if (hovered) hovered.transform.localScale = baseScale[hovered];
        hovered = tgt;
        if (hovered) hovered.transform.localScale = baseScale[hovered] * hoverScale;
    }

    private IEnumerator PollDisplayState()
    {
        while (true)
        {
            using var req = UnityWebRequest.Get(DISPLAY_URL);
            yield return req.SendWebRequest();
            if (req.result == UnityWebRequest.Result.Success)
            {
                var resp = JsonUtility.FromJson<DisplayResp>(req.downloadHandler.text);
                bool shouldLock = resp.data?.current_display == "website";
                if (shouldLock && !Locked)
                {
                    Locked = true;
                    yield return StartCoroutine(SendAllPoints());
                }
            }
            // poll every 2 seconds
            yield return new WaitForSeconds(2f);
        }
    }

    private IEnumerator SendAllPoints()
    {
        // Build JSON payload
        List<PointJson> list = new();
        foreach (var p in points)
        {
            Vector3 pos = p.transform.position;
            list.Add(new PointJson
            {
                x = Mathf.RoundToInt(pos.x * 100),
                y = Mathf.RoundToInt(pos.z * 100)
            });
        }
        string json = JsonUtility.ToJson(new PointsPayload { points = list.ToArray() });
        private string UpdatePointsEndpoint => $"http://127.0.0.1:8000/api/datacenters/{dataCenterId}/";


        Debug.Log($"Sending {list.Count} points to {UpdatePointsEndpoint}:\n{json}"
            + "\n\nNote: This is a one-time operation. The points will be deleted after sending.");

        using var req = new UnityWebRequest(UpdatePointsEndpoint, "PATCH")
        {
            uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(json)),
            downloadHandler = new DownloadHandlerBuffer()
        };
        req.SetRequestHeader("Content-Type", "application/json");
        yield return req.SendWebRequest();

        if (req.result != UnityWebRequest.Result.Success)
        {
            Debug.LogError(req.error);
            yield break;
        }

        // Small delay to ensure backend processed data, then delete local points
        yield return new WaitForSeconds(0.25f);
        foreach (var p in points)
            Destroy(p);
        points.Clear();
        baseScale.Clear();
    }

    #region DTOs
    [System.Serializable] private class PointJson { public int x; public int y; }
    [System.Serializable] private class PointsPayload { public PointJson[] points; }

    [System.Serializable]
    private class DisplayResp
    {
        public DisplayData data;
        [System.Serializable] public class DisplayData { public string current_display; }
    }
    #endregion
}
