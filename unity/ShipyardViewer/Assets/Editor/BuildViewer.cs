using System.IO;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

// Reproducible scene + Web build. Run: see contracts/unity-viewer.md.
public static class BuildViewer
{
    private const string ScenePath = "Assets/Scenes/ShipViewer.unity";
    private const string MaterialDir = "Assets/Materials";
    private const string DefaultOutput = "../../frontend/public/unity/ship-viewer";

    [System.Serializable]
    private class BuildManifest
    {
        public string loaderUrl, dataUrl, frameworkUrl, codeUrl, companyName, productName, productVersion;
    }

    [MenuItem("Shipyard/Create Scene")]
    public static void CreateScene()
    {
        Directory.CreateDirectory("Assets/Scenes");
        Directory.CreateDirectory(MaterialDir);
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.42f, 0.47f, 0.54f);
        RenderSettings.ambientEquatorColor = new Color(0.34f, 0.37f, 0.41f);
        RenderSettings.ambientGroundColor = new Color(0.24f, 0.26f, 0.29f);

        var camera = new GameObject("Main Camera") { tag = "MainCamera" };
        var cam = camera.AddComponent<Camera>();
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = new Color32(0xDD, 0xE4, 0xEE, 0xFF);
        cam.fieldOfView = 30f;
        cam.nearClipPlane = 1f;
        cam.farClipPlane = 1000f;
        var rig = camera.AddComponent<ShipCameraRig>();

        var sun = new GameObject("Sun").AddComponent<Light>();
        sun.type = LightType.Directional;
        sun.intensity = 0.95f;
        sun.shadows = LightShadows.Soft;
        sun.transform.rotation = Quaternion.Euler(52f, -35f, 0f);

        var controller = new GameObject("ShipViewer").AddComponent<ShipViewerController>();
        controller.rig = rig;
        controller.materials = new ShipMaterials
        {
            hullLower = Mat("HullLower", new Color32(0x9E, 0x2F, 0x2A, 0xFF), 0.3f),
            hullUpper = Mat("HullUpper", new Color32(0x1B, 0x3A, 0x66, 0xFF), 0.4f),
            deck = Mat("Deck", new Color32(0x6F, 0x8A, 0x7A, 0xFF), 0.2f),
            house = Mat("House", new Color32(0xE4, 0xE8, 0xEE, 0xFF), 0.3f),
            accent = Mat("Accent", new Color32(0xD9, 0x7F, 0x2A, 0xFF), 0.3f),
            glass = Mat("Glass", new Color32(0x20, 0x2C, 0x3C, 0xFF), 0.8f),
            steel = Mat("Steel", new Color32(0x5B, 0x65, 0x73, 0xFF), 0.3f),
            ground = Mat("Ground", new Color32(0xB4, 0xBD, 0xC9, 0xFF), 0.05f),
        };

        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
    }

    private static Material Mat(string name, Color color, float smoothness)
    {
        var material = new Material(Shader.Find("Standard")) { color = color };
        material.SetFloat("_Glossiness", smoothness);
        AssetDatabase.CreateAsset(material, $"{MaterialDir}/{name}.mat");
        return material;
    }

    [MenuItem("Shipyard/Build Web")]
    public static void Build()
    {
        CreateScene();

        PlayerSettings.companyName = "SWP";
        PlayerSettings.productName = "ShipyardViewer";
        PlayerSettings.colorSpace = ColorSpace.Linear;
        PlayerSettings.runInBackground = true;
        PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Disabled; // local validation; see contract for deployment
        PlayerSettings.WebGL.decompressionFallback = false;
        PlayerSettings.WebGL.nameFilesAsHashes = false;
        PlayerSettings.WebGL.dataCaching = false;
        PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.None;
        PlayerSettings.WebGL.template = "APPLICATION:Minimal";
        PlayerSettings.stripEngineCode = true;
        PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.WebGL, ManagedStrippingLevel.High);
        PlayerSettings.SetUseDefaultGraphicsAPIs(BuildTarget.WebGL, false);
        PlayerSettings.SetGraphicsAPIs(BuildTarget.WebGL, new[] { GraphicsDeviceType.OpenGLES3 });

        string output = Path.GetFullPath(DefaultOutput);
        if (Directory.Exists(output)) Directory.Delete(output, true);
        Directory.CreateDirectory(output);

        BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { ScenePath },
            locationPathName = output,
            target = BuildTarget.WebGL,
            options = BuildOptions.None,
        });
        Debug.Log($"Build result: {report.summary.result}, {report.summary.totalSize} bytes, errors {report.summary.totalErrors}");
        if (report.summary.result != BuildResult.Succeeded) { EditorApplication.Exit(1); return; }

        WriteManifest(output);
        File.Delete(Path.Combine(output, "index.html"));
        if (Directory.Exists(Path.Combine(output, "TemplateData"))) Directory.Delete(Path.Combine(output, "TemplateData"), true);
    }

    // The page reads this instead of guessing file names.
    private static void WriteManifest(string output)
    {
        string build = Path.Combine(output, "Build");
        string Find(string pattern)
        {
            string[] files = Directory.GetFiles(build, pattern);
            if (files.Length != 1) throw new BuildFailedException($"Expected one {pattern} in {build}, found {files.Length}");
            return Path.GetFileName(files[0]);
        }
        var manifest = new BuildManifest
        {
            loaderUrl = Find("*.loader.js"),
            dataUrl = Find("*.data*"),
            frameworkUrl = Find("*.framework.js*"),
            codeUrl = Find("*.wasm*"),
            companyName = PlayerSettings.companyName,
            productName = PlayerSettings.productName,
            productVersion = PlayerSettings.bundleVersion,
        };
        File.WriteAllText(Path.Combine(build, "build.json"), JsonUtility.ToJson(manifest, true));
    }
}
