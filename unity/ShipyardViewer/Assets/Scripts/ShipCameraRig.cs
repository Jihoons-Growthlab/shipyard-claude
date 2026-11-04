using UnityEngine;

// Orbit camera: left drag rotates, wheel zooms, right drag pans. All ranges are clamped so the camera
// stays outside the model and the model stays in reach.
[RequireComponent(typeof(Camera))]
public class ShipCameraRig : MonoBehaviour
{
    private const float MinPitch = 4f, MaxPitch = 88f;
    private const float MinDistance = 50f, MaxDistance = 260f;
    private const float DefaultYaw = -130f, DefaultPitch = 20f;
    private const float Damping = 12f;
    private static readonly Vector3 DefaultPivot = new Vector3(0f, 7f, 0f);
    private static readonly Vector3 PivotMin = new Vector3(-10f, 2f, -14f);
    private static readonly Vector3 PivotMax = new Vector3(10f, 14f, 14f);

    private float yaw, pitch, distance;
    private float targetYaw, targetPitch, targetDistance;
    private Vector3 pivot, targetPivot;
    private Vector3 lastMouse;
    private Camera cam;

    private void Awake() { cam = GetComponent<Camera>(); }

    public void ResetView(bool snap)
    {
        SetTarget(DefaultYaw, DefaultPitch, FitDistance(34f, 15f));
        if (snap)
        {
            yaw = targetYaw; pitch = targetPitch; distance = targetDistance; pivot = targetPivot;
            Place();
        }
    }

    public void ApplyView(string view)
    {
        switch (view)
        {
            case "front": SetTarget(180f, 6f, FitDistance(10f, 15f)); break;
            case "side": SetTarget(-90f, 6f, FitDistance(33f, 15f)); break;
            case "top": SetTarget(-90f, MaxPitch, FitDistance(33f, 10f)); break;
            case "reset": ResetView(false); break;
            default: Debug.LogWarning("Unknown view: " + view); break;
        }
    }

    private void SetTarget(float y, float p, float d)
    {
        targetYaw = yaw + Mathf.DeltaAngle(yaw, y); // take the short way round
        targetPitch = p;
        targetDistance = d;
        targetPivot = DefaultPivot;
    }

    private float FitDistance(float halfWidth, float halfHeight)
    {
        float t = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        float d = Mathf.Max(halfWidth / (t * cam.aspect), halfHeight / t) * 1.15f;
        return Mathf.Clamp(d, MinDistance, MaxDistance);
    }

    private void Update()
    {
        HandleInput();
        float k = 1f - Mathf.Exp(-Damping * Time.unscaledDeltaTime);
        yaw = Mathf.Lerp(yaw, targetYaw, k);
        pitch = Mathf.Lerp(pitch, targetPitch, k);
        distance = Mathf.Lerp(distance, targetDistance, k);
        pivot = Vector3.Lerp(pivot, targetPivot, k);
        Place();
    }

    private void HandleInput()
    {
        Vector3 mouse = Input.mousePosition;
        if (Input.GetMouseButtonDown(0) || Input.GetMouseButtonDown(1)) lastMouse = mouse;
        Vector3 delta = mouse - lastMouse;
        lastMouse = mouse;

        if (Input.GetMouseButton(0))
        {
            targetYaw += delta.x * 0.3f;
            targetPitch = Mathf.Clamp(targetPitch - delta.y * 0.25f, MinPitch, MaxPitch);
        }
        else if (Input.GetMouseButton(1))
        {
            float unitsPerPixel = 2f * distance * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) / Mathf.Max(1, Screen.height);
            Vector3 move = transform.right * -delta.x + transform.up * -delta.y;
            targetPivot = Clamp(targetPivot + move * unitsPerPixel);
        }

        float wheel = Mathf.Clamp(Input.mouseScrollDelta.y, -3f, 3f);
        if (wheel != 0f) targetDistance = Mathf.Clamp(targetDistance * Mathf.Exp(-wheel * 0.12f), MinDistance, MaxDistance);
    }

    private static Vector3 Clamp(Vector3 p)
    {
        return new Vector3(Mathf.Clamp(p.x, PivotMin.x, PivotMax.x), Mathf.Clamp(p.y, PivotMin.y, PivotMax.y), Mathf.Clamp(p.z, PivotMin.z, PivotMax.z));
    }

    private void Place()
    {
        Quaternion rotation = Quaternion.Euler(pitch, yaw, 0f);
        transform.SetPositionAndRotation(pivot + rotation * new Vector3(0f, 0f, -distance), rotation);
    }
}
