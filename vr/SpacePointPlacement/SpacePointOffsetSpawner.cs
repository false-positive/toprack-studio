using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;

/// <summary>
/// Spawns filtered modules when display == "vr" and SpacePointPlacement is locked,
/// lets the user drag them, PATCH‑updates positions, and draws pretty tube links.
/// </summary>
public class ActiveModuleSpawner : MonoBehaviour
{
    /* ────────── Inspector ────────── */
    [Header("References")]
    [SerializeField] private OVRCameraRig cameraRig;
    [SerializeField] private SpacePointPlacement pointPlacement;        // must exist & expose Locked
    [SerializeField] private GameObject modulePrefab;
    [SerializeField] private GameObject dotPrefab;

    [Header("Backend")]
    [Tooltip("Wildcard filter e.g.  server_rack_*  (leave empty = keep all)")]
    [SerializeField] private string nameFilterPattern = "server_rack_*";
    [SerializeField] private string modulesUrl = "http://127.0.0.1:8000/api/active-modules/";
    [SerializeField] private string displayUrl = "http://127.0.0.1:8000/api/display-control/";

    [Header("Placement")]
    [SerializeField] private Vector2 spawnOffset = Vector2.zero;

    [Header("VR Interaction")]
    [SerializeField] private OVRInput.Controller hand = OVRInput.Controller.RTouch;
    [SerializeField] private float maxDistance = 15f;
    [SerializeField] private float hoverScale = 1.2f;
    [SerializeField] private float dragScale = 1.4f;

    [Header("Tube Style")]
    [SerializeField] private float tubeRadius = 0.05f;             // 5 cm radius
    [SerializeField] private Material tubeMaterial;
    [SerializeField] private Color tubeColor = Color.cyan;

    /* ────────── runtime ────────── */
    private readonly List<GameObject> modules = new List<GameObject>();
    private readonly List<GameObject> dots = new List<GameObject>();
    private readonly List<GameObject> tubes = new List<GameObject>();
    private readonly Dictionary<GameObject, int> ids = new Dictionary<GameObject, int>();
    private readonly Dictionary<GameObject, Vector3> baseScale = new Dictionary<GameObject, Vector3>();

    private Transform spawnParent;
    private Plane floorPlane;
    private float floorY;

    private GameObject hovered, dragging;
    private bool locked = true;          // starts locked

    private Coroutine pollCR;

    /* ────────── unity setup ────────── */
    void Awake()
    {
        cameraRig ??= FindObjectOfType<OVRCameraRig>();
        pointPlacement ??= FindObjectOfType<SpacePointPlacement>();
        if (!cameraRig || !pointPlacement)
        { Debug.LogError("ActiveModuleSpawner: missing references."); enabled = false; return; }

        spawnParent = new GameObject("SpawnedModules").transform;
        spawnParent.SetParent(cameraRig.trackingSpace, false);

        // floor plane from boundary
        var b = OVRManager.boundary;
        floorY = (b != null && b.GetConfigured() && b.GetGeometry(OVRBoundary.BoundaryType.PlayArea).Length > 0)
                 ? b.GetGeometry(OVRBoundary.BoundaryType.PlayArea)[0].y : 0f;
        floorPlane = new Plane(Vector3.up, new Vector3(0, floorY, 0));

        pollCR = StartCoroutine(PollDisplayLoop());
    }
    void OnDisable() { if (pollCR != null) StopCoroutine(pollCR); }

    /* ────────── update ────────── */
    void Update()
    {
        if (locked || modules.Count == 0) return;

        var ts = cameraRig.trackingSpace;
        Vector3 origin = ts.TransformPoint(OVRInput.GetLocalControllerPosition(hand));
        Vector3 dir = ts.rotation * OVRInput.GetLocalControllerRotation(hand) * Vector3.forward;
        Ray ray = new Ray(origin, dir);

        if (dragging == null) HandleHover(ray);
        else HandleDrag(ray, ts);

        RefreshTubeTransforms();
    }

    /* ────────── hover / drag ────────── */
    void HandleHover(Ray ray)
    {
        if (Physics.Raycast(ray, out RaycastHit hit, maxDistance) && modules.Contains(hit.collider.gameObject))
            SetHover(hit.collider.gameObject);
        else
            SetHover(null);

        if (hovered && OVRInput.GetDown(OVRInput.Button.PrimaryIndexTrigger, hand))
        {
            dragging = hovered;
            dragging.transform.localScale = baseScale[dragging] * dragScale;
            SetHover(null);
        }
    }
    void HandleDrag(Ray ray, Transform ts)
    {
        if (floorPlane.Raycast(ray, out float d) && d <= maxDistance)
        {
            Vector3 hit = ray.GetPoint(d); hit.y = floorY;
            Vector3 local = ts.InverseTransformPoint(hit);
            local.x += spawnOffset.x; local.z += spawnOffset.y;
            dragging.transform.position = ts.TransformPoint(local);
        }
        if (OVRInput.GetUp(OVRInput.Button.PrimaryIndexTrigger, hand))
        {
            dragging.transform.localScale = baseScale[dragging];
            StartCoroutine(PatchModule(ids[dragging], dragging.transform.position));
            dragging = null;
        }
    }
    void SetHover(GameObject g)
    {
        if (hovered == g) return;
        if (hovered) hovered.transform.localScale = baseScale[hovered];
        hovered = g;
        if (hovered) hovered.transform.localScale = baseScale[hovered] * hoverScale;
    }

    /* ────────── display gating ────────── */
    IEnumerator PollDisplayLoop()
    {
        while (true)
        {
            bool vr = false;
            using (var r = UnityWebRequest.Get(displayUrl))
            {
                yield return r.SendWebRequest();
                if (r.result == UnityWebRequest.Result.Success)
                {
                    var dr = JsonUtility.FromJson<DisplayResp>(r.downloadHandler.text);
                    vr = dr.data != null && dr.data.current_display == "vr";
                }
            }

            if (vr && pointPlacement.Locked && locked)
                yield return StartCoroutine(UnlockAndSpawn());
            else if ((!vr || !pointPlacement.Locked) && !locked)
                LockInteraction();

            yield return new WaitForSeconds(2f);
        }
    }

    /* ────────── spawn / despawn ────────── */
    IEnumerator UnlockAndSpawn()
    {
        ClearAll();
        using var r = UnityWebRequest.Get(modulesUrl);
        yield return r.SendWebRequest();
        if (r.result != UnityWebRequest.Result.Success) yield break;

        var resp = JsonUtility.FromJson<Response>(r.downloadHandler.text);
        foreach (var m in resp.data ?? new Module[0])
        {
            if (!PassesFilter(m.module_details?.name)) continue;

            Vector3 local = new Vector3((m.x / 100f) + spawnOffset.x, floorY,
                                        (m.y / 100f) + spawnOffset.y);
            Vector3 world = cameraRig.trackingSpace.TransformPoint(local);

            GameObject go = Instantiate(modulePrefab, world, Quaternion.identity, spawnParent);
            if (!go.TryGetComponent<Collider>(out _)) go.AddComponent<BoxCollider>();
            modules.Add(go); ids[go] = m.id; baseScale[go] = go.transform.localScale;

            // Dot
            if (dotPrefab != null)
            {
                GameObject dot = Instantiate(dotPrefab, world, Quaternion.identity, go.transform);
                dot.name = "CenterDot";
                dots.Add(dot);
            }
        }
        RebuildTubes();
        locked = false;
    }
    void ClearAll()
    {
        foreach (Transform c in spawnParent) Destroy(c.gameObject);
        modules.Clear(); ids.Clear(); baseScale.Clear(); dots.Clear();
        foreach (var t in tubes) Destroy(t);
        tubes.Clear();
    }
    void LockInteraction()
    {
        if (hovered) hovered.transform.localScale = baseScale[hovered];
        if (dragging) { dragging.transform.localScale = baseScale[dragging]; dragging = null; }
        hovered = null; locked = true;
    }

    /* ────────── tubes ────────── */
    void RebuildTubes()
    {
        foreach (var t in tubes) Destroy(t);
        tubes.Clear();
        if (modules.Count < 2) return;

        for (int i = 0; i < modules.Count - 1; i++)
        {
            Vector3 p0 = modules[i].transform.position;
            Vector3 p1 = modules[i + 1].transform.position;
            tubes.Add(BuildTube(p0, p1));
        }
    }
    void RefreshTubeTransforms()
    {
        if (tubes.Count == 0) return;
        for (int i = 0; i < tubes.Count; i++)
        {
            Vector3 p0 = modules[i].transform.position;
            Vector3 p1 = modules[i + 1].transform.position;

            GameObject tube = tubes[i];
            float len = Vector3.Distance(p0, p1); if (len < 0.001f) len = 0.001f;

            tube.transform.position = (p0 + p1) * 0.5f;
            tube.transform.up = (p1 - p0).normalized;
            tube.transform.localScale = new Vector3(tubeRadius * 2, len * 0.5f, tubeRadius * 2);
        }
    }
    GameObject BuildTube(Vector3 a, Vector3 b)
    {
        float len = Vector3.Distance(a, b); if (len < 0.001f) len = 0.001f;
        GameObject cyl = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        cyl.name = "ModuleTube";
        cyl.transform.SetParent(spawnParent, false);
        cyl.transform.position = (a + b) * 0.5f;
        cyl.transform.up = (b - a).normalized;
        cyl.transform.localScale = new Vector3(tubeRadius * 2, len * 0.5f, tubeRadius * 2);

        Destroy(cyl.GetComponent<Collider>());
        MeshRenderer mr = cyl.GetComponent<MeshRenderer>();
        mr.material = tubeMaterial != null ? tubeMaterial : new Material(Shader.Find("Standard"));
        mr.material.color = tubeColor;
        return cyl;
    }

    /* ────────── network helpers ────────── */
    IEnumerator PatchModule(int id, Vector3 world)
    {
        Vector3 local = cameraRig.trackingSpace.InverseTransformPoint(world);
        var p = new ModulePos
        {
            x = Mathf.RoundToInt((local.x - spawnOffset.x) * 100),
            y = Mathf.RoundToInt((local.z - spawnOffset.y) * 100)
        };
        string json = JsonUtility.ToJson(p);
        using var req = new UnityWebRequest(modulesUrl + id + "/", "PATCH")
        {
            uploadHandler = new UploadHandlerRaw(System.Text.Encoding.UTF8.GetBytes(json)),
            downloadHandler = new DownloadHandlerBuffer()
        };
        req.SetRequestHeader("Content-Type", "application/json");
        yield return req.SendWebRequest();
        if (req.result != UnityWebRequest.Result.Success)
            Debug.LogError($"PATCH {id} failed: {req.error}");
    }

    /* ────────── utilities ────────── */
    bool PassesFilter(string name)
    {
        if (string.IsNullOrEmpty(nameFilterPattern) || string.IsNullOrEmpty(name)) return true;
        if (!nameFilterPattern.Contains("*")) return name.Equals(nameFilterPattern);
        string prefix = nameFilterPattern.TrimEnd('*');
        return name.StartsWith(prefix);
    }

    /* ────────── DTOs ────────── */
    [System.Serializable] class DisplayResp { public Disp data; [System.Serializable] public class Disp { public string current_display; } }
    [System.Serializable] class Response { public Module[] data; }
    [System.Serializable] class Module { public int id; public Detail module_details; public float x, y; }
    [System.Serializable] class Detail { public string name; }
    [System.Serializable] class ModulePos { public int x, y; }
}
