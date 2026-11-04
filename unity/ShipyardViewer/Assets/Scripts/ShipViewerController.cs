using System.Collections;
using System.Runtime.InteropServices;
using UnityEngine;

// Target of the browser's SendMessage calls; the GameObject must be named "ShipViewer" (contracts/unity-viewer.md).
public class ShipViewerController : MonoBehaviour
{
    public ShipCameraRig rig;
    public ShipMaterials materials;

#if UNITY_WEBGL && !UNITY_EDITOR
    [DllImport("__Internal")] private static extern void ShipViewer_NotifyReady();
#else
    private static void ShipViewer_NotifyReady() { }
#endif

    private void Awake()
    {
        QualitySettings.shadows = ShadowQuality.All;
        QualitySettings.shadowDistance = 400f; // the default stops short of the orbit distance
#if UNITY_WEBGL && !UNITY_EDITOR
        // Keep Esc and form keys with the host page.
        WebGLInput.captureAllKeyboardInput = false;
#endif
    }

    private IEnumerator Start()
    {
        ShipModelBuilder.Build(transform, materials);
        rig.ResetView(true);
        yield return new WaitForEndOfFrame(); // ready means the ship has been rendered once
        ShipViewer_NotifyReady();
    }

    // Called with "front" | "side" | "top" | "reset".
    public void SetView(string view)
    {
        rig.ApplyView(view);
    }
}
