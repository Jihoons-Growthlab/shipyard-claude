using System.Collections.Generic;
using UnityEngine;

// Generic demo ship (Demo Ship 01). Proportions are invented: it does not represent any real hull.
// Bow points to +Z, the ground plane is y = 0.
public static class ShipModelBuilder
{
    private const float Length = 60f, Beam = 10f, Depth = 6f, Rake = 3f, Base = 0.8f;
    private const float Waterline = 2.6f;
    private static readonly float[] Heights = { 0f, 0.2f, 0.5f, 0.9f, 1.3f, 1.6f, 2.1f, Waterline, 3.2f, 4f, 5f, 5.6f, Depth };
    private const int Stations = 72;

    public static void Build(Transform parent, ShipMaterials m)
    {
        var lower = new MeshBuilder(smooth: true);
        var upper = new MeshBuilder(smooth: true);
        var deck = new MeshBuilder();
        var house = new MeshBuilder();
        var accent = new MeshBuilder();
        var glass = new MeshBuilder();
        var steel = new MeshBuilder();
        var ground = new MeshBuilder();

        var lowerTransom = new MeshBuilder();
        var upperTransom = new MeshBuilder();
        AddHull(lower, upper, deck, lowerTransom, upperTransom);
        AddSuperstructure(house, accent, glass, steel);
        AddCargoDeck(accent, steel);
        AddGround(ground, steel);

        lower.Commit("HullLower", parent, m.hullLower);
        upper.Commit("HullUpper", parent, m.hullUpper);
        lowerTransom.Commit("TransomLower", parent, m.hullLower);
        upperTransom.Commit("TransomUpper", parent, m.hullUpper);
        deck.Commit("Deck", parent, m.deck);
        house.Commit("Superstructure", parent, m.house);
        accent.Commit("Accent", parent, m.accent);
        glass.Commit("Glass", parent, m.glass);
        steel.Commit("Steel", parent, m.steel);
        ground.Commit("Ground", parent, m.ground);
    }

    private static float HalfWidth(float z, float h)
    {
        float section = 1f - 0.55f * Mathf.Pow(1f - Mathf.Clamp01(h / 1.6f), 3f);
        float zs = z - Rake * (h / Depth);
        float plan = 1f;
        const float bowStart = 12f, bowEnd = Length / 2f - Rake;
        if (zs > bowStart) plan = 1f - Mathf.Pow(Mathf.Clamp01((zs - bowStart) / (bowEnd - bowStart)), 2.2f);
        if (z < -18f)
        {
            float s = Mathf.Clamp01((-18f - z) / 12f);
            plan *= 1f - 0.28f * s * s;
            section *= Mathf.Pow(Mathf.Clamp01((h + 0.15f) / Depth), 0.7f * s);
        }
        return Beam * 0.5f * section * plan;
    }

    private static Vector3 Point(int station, int row, float side)
    {
        float z = Mathf.Lerp(-Length / 2f, Length / 2f, station / (float)Stations);
        float h = Heights[row];
        return new Vector3(side * HalfWidth(z, h), Base + h, z);
    }

    private static void AddHull(MeshBuilder lower, MeshBuilder upper, MeshBuilder deck, MeshBuilder lowerTransom, MeshBuilder upperTransom)
    {
        foreach (float side in new[] { 1f, -1f })
        {
            for (int i = 0; i < Stations; i++)
            {
                Vector3 keelA = Point(i, 0, 0f), keelB = Point(i + 1, 0, 0f);
                lower.Group = side > 0f ? 2 : 3; // bottom
                lower.Quad(keelA, keelB, Point(i + 1, 0, side), Point(i, 0, side), Vector3.down);
                lower.Group = upper.Group = side > 0f ? 0 : 1;
                for (int k = 0; k < Heights.Length - 1; k++)
                {
                    MeshBuilder target = Heights[k] < Waterline ? lower : upper;
                    target.Quad(Point(i, k, side), Point(i + 1, k, side), Point(i + 1, k + 1, side), Point(i, k + 1, side),
                        new Vector3(side, 0f, 0f));
                }
            }
        }
        for (int i = 0; i < Stations; i++)
        {
            int top = Heights.Length - 1;
            deck.Quad(Point(i, top, -1f), Point(i + 1, top, -1f), Point(i + 1, top, 1f), Point(i, top, 1f), Vector3.up);
        }
        for (int k = 0; k < Heights.Length - 1; k++) // transom
        {
            (Heights[k] < Waterline ? lowerTransom : upperTransom).Quad(Point(0, k, -1f), Point(0, k, 1f), Point(0, k + 1, 1f), Point(0, k + 1, -1f), Vector3.back);
        }
    }

    private static void AddSuperstructure(MeshBuilder house, MeshBuilder accent, MeshBuilder glass, MeshBuilder steel)
    {
        float deckY = Base + Depth;
        house.Box(new Vector3(0f, deckY + 1.5f, -20f), new Vector3(7.6f, 3f, 9f));
        house.Box(new Vector3(0f, deckY + 4f, -20.5f), new Vector3(7f, 2f, 7.4f));
        house.Box(new Vector3(0f, deckY + 6f, -20.5f), new Vector3(6.2f, 2f, 6.2f));
        house.Box(new Vector3(0f, deckY + 8f, -19.8f), new Vector3(9.4f, 2f, 3.6f)); // bridge with wings
        glass.Box(new Vector3(0f, deckY + 8.2f, -17.96f), new Vector3(9f, 0.9f, 0.1f));
        foreach (float y in new[] { 1.8f, 4.2f, 6.2f })
            glass.Box(new Vector3(0f, deckY + y, y < 2f ? -15.46f : y < 5f ? -16.76f : -17.36f), new Vector3(5.4f, 0.5f, 0.1f));
        house.Box(new Vector3(0f, deckY + 9.15f, -19.8f), new Vector3(9.8f, 0.3f, 4f));
        accent.Box(new Vector3(0f, deckY + 6.5f, -25f), new Vector3(2.4f, 7f, 3.2f)); // funnel
        steel.Box(new Vector3(0f, deckY + 10.2f, -25f), new Vector3(2.5f, 0.5f, 3.3f));
        steel.Box(new Vector3(0f, deckY + 11f, -19.8f), new Vector3(0.25f, 3.4f, 0.25f)); // mast
        steel.Box(new Vector3(0f, deckY + 11.6f, -19.8f), new Vector3(3f, 0.15f, 0.15f));
    }

    private static void AddCargoDeck(MeshBuilder accent, MeshBuilder steel)
    {
        float deckY = Base + Depth;
        for (int i = 0; i < 4; i++)
        {
            float z = -9.5f + i * 8.2f;
            accent.Box(new Vector3(0f, deckY + 0.45f, z), new Vector3(7.2f, 0.9f, 6.6f));
            steel.Box(new Vector3(0f, deckY + 0.95f, z), new Vector3(6.6f, 0.12f, 6f));
        }
        foreach (float z in new[] { -13.4f, 2.9f, 19.3f }) // cargo posts
        {
            steel.Box(new Vector3(0f, deckY + 2.5f, z), new Vector3(0.7f, 5f, 0.7f));
            steel.Box(new Vector3(0f, deckY + 5.2f, z + 2.8f), new Vector3(0.35f, 0.35f, 6f));
        }
    }

    private static void AddGround(MeshBuilder ground, MeshBuilder steel)
    {
        ground.Quad(new Vector3(-400f, 0f, -400f), new Vector3(400f, 0f, -400f), new Vector3(400f, 0f, 400f), new Vector3(-400f, 0f, 400f), Vector3.up);
        for (int i = 0; i < 9; i++) steel.Box(new Vector3(0f, Base / 2f, -22f + i * 5.5f), new Vector3(3f, Base, 1.4f)); // keel blocks
    }

    private class MeshBuilder
    {
        private readonly List<Vector3> vertices = new List<Vector3>();
        private readonly List<int> triangles = new List<int>();
        private readonly Dictionary<(Vector3, int), int> welded;

        // Vertices merge only inside a group. Port and starboard meet at x = 0 on the bow, where a shared
        // vertex would average opposite normals to zero, so each surface keeps its own group.
        public int Group { get; set; }

        public MeshBuilder(bool smooth = false)
        {
            if (smooth) welded = new Dictionary<(Vector3, int), int>();
        }

        private int Vertex(Vector3 p)
        {
            if (welded != null && welded.TryGetValue((p, Group), out int index)) return index;
            vertices.Add(p);
            if (welded != null) welded[(p, Group)] = vertices.Count - 1;
            return vertices.Count - 1;
        }

        // Winding is taken from the outward hint, so callers can list corners in either direction.
        public void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 outward)
        {
            Vector3 normal = Vector3.Cross(c - a, d - b);
            if (normal.sqrMagnitude < 1e-10f) return;
            bool flip = Vector3.Dot(Vector3.Cross(b - a, c - a) + Vector3.Cross(c - a, d - a), outward) < 0f;
            int ia = Vertex(a), ib = Vertex(b), ic = Vertex(c), id = Vertex(d);
            if (flip) triangles.AddRange(new[] { ia, ic, ib, ia, id, ic });
            else triangles.AddRange(new[] { ia, ib, ic, ia, ic, id });
        }

        public void Box(Vector3 center, Vector3 size)
        {
            Vector3 h = size * 0.5f;
            Vector3 P(float x, float y, float z) => center + new Vector3(x * h.x, y * h.y, z * h.z);
            Quad(P(-1, 1, -1), P(1, 1, -1), P(1, 1, 1), P(-1, 1, 1), Vector3.up);
            Quad(P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1), Vector3.down);
            Quad(P(1, -1, -1), P(1, 1, -1), P(1, 1, 1), P(1, -1, 1), Vector3.right);
            Quad(P(-1, -1, -1), P(-1, 1, -1), P(-1, 1, 1), P(-1, -1, 1), Vector3.left);
            Quad(P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1), Vector3.forward);
            Quad(P(-1, -1, -1), P(1, -1, -1), P(1, 1, -1), P(-1, 1, -1), Vector3.back);
        }

        public void Commit(string name, Transform parent, Material material)
        {
            var mesh = new Mesh { name = name, indexFormat = UnityEngine.Rendering.IndexFormat.UInt32 };
            mesh.SetVertices(vertices);
            mesh.SetTriangles(triangles, 0);
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            go.AddComponent<MeshRenderer>().sharedMaterial = material;
        }
    }
}
