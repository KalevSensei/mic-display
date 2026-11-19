using System;
using System.IO;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class SwShow
{
    static void Log(string s) { Console.WriteLine(s); }

    static SldWorks Attach()
    {
        object o = null;
        try { o = Marshal.GetActiveObject("SldWorks.Application"); } catch { }
        if (o == null) o = Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application"));
        var sw = (SldWorks)o;
        sw.Visible = true;
        sw.UserControl = true;
        return sw;
    }

    static double[] Rgb(string n)
    {
        string u = n.ToUpperInvariant();
        if (u.StartsWith("EINO_P03")) return new[] { 0.70, 0.72, 0.75 };
        if (u.StartsWith("EINO_P12") || u.StartsWith("EINO_P13")) return new[] { 0.36, 0.38, 0.41 };
        if (u.StartsWith("EINO_P10")) return new[] { 0.80, 0.74, 0.64 };
        if (u.StartsWith("EINO")) return new[] { 0.50, 0.52, 0.55 };
        if (u.StartsWith("A11")) return new[] { 0.16, 0.52, 0.93 };
        if (u.StartsWith("A10") || u.StartsWith("A12") || u.StartsWith("D03")) return new[] { 0.95, 0.50, 0.12 };
        if (u.StartsWith("M4") || u.StartsWith("M5")) return new[] { 0.20, 0.21, 0.23 };
        if (u.StartsWith("D01") || u.StartsWith("D02") || u.StartsWith("W00")) return new[] { 0.06, 0.06, 0.07 };
        return null;
    }

    static Component2[] Comps(AssemblyDoc asm)
    {
        var o = (object[])asm.GetComponents(true);
        var l = new List<Component2>();
        if (o != null) foreach (var c in o) l.Add((Component2)c);
        return l.ToArray();
    }

    static void Colour(AssemblyDoc asm)
    {
        foreach (var c in Comps(asm))
        {
            var rgb = Rgb(c.Name2);
            if (rgb == null) { Log("  no colour rule: " + c.Name2); continue; }
            string u = c.Name2.ToUpperInvariant();
            bool metal = u.StartsWith("M4") || u.StartsWith("M5") || u.StartsWith("EINO_P03") || u.StartsWith("EINO_P1");
            var mp = new double[] { rgb[0], rgb[1], rgb[2], 0.5, 0.9, metal ? 0.7 : 0.3, metal ? 0.6 : 0.2, 0.0, 0.0 };
            c.SetMaterialPropertyValues2(mp, (int)swInConfigurationOpts_e.swAllConfiguration, null);
        }
    }

    static ModelDoc2 Import(SldWorks sw, string step, string outPath)
    {
        var imp = sw.GetImportFileData(step);
        int err = 0;
        var doc = (ModelDoc2)sw.LoadFile4(step, "r", imp, ref err);
        Log("loaded " + Path.GetFileName(step) + " err=" + err + " ok=" + (doc != null));
        if (doc == null) return null;
        var asm = (AssemblyDoc)doc;
        var top = Comps(asm);
        if (top.Length == 1)
        {   // the STEP's root product came in as one wrapper subassembly: dissolve it so every part sits at the top
            doc.ClearSelection2(true);
            top[0].Select4(false, null, false);
            bool ok = asm.DissolveSubAssembly();
            Log("  dissolved wrapper " + top[0].Name2 + ": " + ok);
        }
        Colour(asm);
        doc.ForceRebuild3(false);
        int e = 0, w = 0;
        bool sok = doc.Extension.SaveAs3(outPath, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, null, ref e, ref w);
        Log("saved " + outPath + " ok=" + sok + " e=" + e + " w=" + w + " (" + Comps(asm).Length + " top-level components)");
        return doc;
    }


    public static string[] PNames; public static string[] PFiles; public static double[][] PM; public static double[][] PMx; public static double[][] PRgb; public static string[] PMat;

    static double[] SwXf(double[] m)   // 4x4 row-major (column-vector convention, mm) -> SolidWorks ArrayData
    {
        return new double[] { m[0], m[4], m[8], m[1], m[5], m[9], m[2], m[6], m[10], m[3] / 1000.0, m[7] / 1000.0, m[11] / 1000.0, 1.0, 0, 0, 0 };
    }

    static ModelDoc2 Build(SldWorks sw, string dir, string outPath, bool exploded)
    {
        string pdir = Path.Combine(dir, "parts");
        var opened = new Dictionary<string, string>();
        for (int i = 0; i < PFiles.Length; i++)
        {
            string f = PFiles[i];
            if (opened.ContainsKey(f)) continue;
            string prt = Path.Combine(pdir, f + ".SLDPRT");
            ModelDoc2 pd;
            int err = 0, wrn = 0;
            if (!File.Exists(prt))
            {
                var imp = sw.GetImportFileData(Path.Combine(pdir, f + ".step"));
                pd = (ModelDoc2)sw.LoadFile4(Path.Combine(pdir, f + ".step"), "r", imp, ref err);
                var rgb = PRgb[i];
                bool metal = PMat[i] == "steel" || PMat[i] == "alu" || PMat[i] == "spring";
                pd.MaterialPropertyValues = new double[] { rgb[0], rgb[1], rgb[2], 0.5, 0.9, metal ? 0.7 : 0.3, metal ? 0.6 : 0.2, 0.0, 0.0 };
                pd.Extension.SaveAs3(prt, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, null, ref err, ref wrn);
            }
            else pd = (ModelDoc2)sw.OpenDoc6(prt, (int)swDocumentTypes_e.swDocPART, (int)swOpenDocOptions_e.swOpenDocOptions_Silent, "", ref err, ref wrn);
            opened[f] = pd.GetTitle();
        }
        string tpl = sw.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplateAssembly);
        var ad = (ModelDoc2)sw.NewDocument(tpl, 0, 0, 0);
        var asm = (AssemblyDoc)ad;
        var names = new string[PFiles.Length];
        var xf = new List<double>();
        for (int i = 0; i < PFiles.Length; i++)
        {
            names[i] = Path.Combine(pdir, PFiles[i] + ".SLDPRT");
            xf.AddRange(SwXf(exploded ? PMx[i] : PM[i]));
        }
        var comps = (object[])asm.AddComponents3(names, xf.ToArray(), null);
        Log("added " + (comps == null ? 0 : comps.Length) + " components");
        foreach (Component2 c in comps) if (c.Name2.StartsWith("Eino_P10") || c.Name2.StartsWith("A10")) { var t = Rot(c); Log("  after add " + c.Name2 + " T=" + t[9].ToString("F3") + "," + t[10].ToString("F3") + "," + t[11].ToString("F3")); }
        // fix every component where it was placed (no mates; nothing should float away)
        ad.ClearSelection2(true);
        foreach (Component2 c in comps) c.Select4(true, null, false);
        asm.FixComponent();
        ad.ClearSelection2(true);
        foreach (Component2 c in comps) if (c.Name2.StartsWith("Eino_P10") || c.Name2.StartsWith("A10")) { var t = Rot(c); Log("  after fix " + c.Name2 + " T=" + t[9].ToString("F3") + "," + t[10].ToString("F3") + "," + t[11].ToString("F3")); }
        foreach (var t in opened.Values) sw.CloseDoc(t);
        int e = 0, w = 0;
        bool ok = ad.Extension.SaveAs3(outPath, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, null, ref e, ref w);
        Log("saved " + outPath + " ok=" + ok + " e=" + e);
        return ad;
    }

    // ---- exploded view
    static double[] Rot(Component2 c)
    {
        return (double[])((MathTransform)c.Transform2).ArrayData;
    }

    static Edge FindEdge(Component2 c, double[] want, out bool alongEdge)
    {
        alongEdge = true;
        object junk;
        var bodies = (object[])c.GetBodies3((int)swBodyType_e.swSolidBody, out junk);
        if (bodies == null) return null;
        var xd = Rot(c);
        Edge best = null; double bestDot = 0; double bestLen = -1;
        foreach (Body2 b in bodies)
        {
            foreach (Edge ed in (object[])b.GetEdges())
            {
                var cu = (Curve)ed.GetCurve();
                if (cu == null || !cu.IsLine()) continue;
                var lp = (double[])cu.LineParams;
                var d = new[] { lp[3], lp[4], lp[5] };
                var t = new[] { d[0]*xd[0] + d[1]*xd[3] + d[2]*xd[6], d[0]*xd[1] + d[1]*xd[4] + d[2]*xd[7], d[0]*xd[2] + d[1]*xd[5] + d[2]*xd[8] };
                double dot = t[0]*want[0] + t[1]*want[1] + t[2]*want[2];
                var vs = (Vertex)ed.GetStartVertex(); var ve = (Vertex)ed.GetEndVertex();
                double len = 0;
                if (vs != null && ve != null)
                {
                    var p0 = (double[])vs.GetPoint(); var p1 = (double[])ve.GetPoint();
                    len = Math.Sqrt(Math.Pow(p1[0]-p0[0],2) + Math.Pow(p1[1]-p0[1],2) + Math.Pow(p1[2]-p0[2],2));
                }
                if (Math.Abs(dot) > 0.9999 && len > bestLen) { best = ed; bestDot = dot; bestLen = len; }
            }
        }
        alongEdge = bestDot > 0;
        return best;
    }

    static double[] Pos(Component2 c) { var a = Rot(c); return new[] { a[9], a[10], a[11] }; }

    static void Step(ModelDoc2 doc, AssemblyDoc asm, string[] prefixes, Component2 dirComp, double[] dir, double dist, string label, bool flip)
    {
        double s = dist < 0 ? -1 : 1;
        var want = new[] { dir[0]*s, dir[1]*s, dir[2]*s };
        bool along;
        var ed = FindEdge(dirComp, want, out along);
        if (ed == null) { Log("  no edge for " + label); return; }
        doc.ClearSelection2(true);
        var sm = (SelectionMgr)doc.SelectionManager;
        var sd = (SelectData)sm.CreateSelectData();
        sd.Mark = 1;
        int n = 0;
        foreach (var c in Comps(asm))
            foreach (var p in prefixes)
                if (c.Name2.StartsWith(p)) { c.Select4(true, sd, false); n++; break; }
        var sd2 = (SelectData)sm.CreateSelectData();
        sd2.Mark = 2;
        ((Entity)ed).Select4(true, sd2);
        bool rev = flip ? along : !along;
        var cfg = (Configuration)doc.ConfigurationManager.ActiveConfiguration;
        var st = cfg.AddExplodeStep(Math.Abs(dist) / 1000.0, rev, false, false);
        Log("  step " + label + ": " + n + " comps, edge along=" + along + ", reverse=" + rev + ", ok=" + (st != null));
        doc.ClearSelection2(true);
    }

    static void Explode(ModelDoc2 doc, double[] barY, double[] barZ, double[] dispY, bool flip)
    {
        var asm = (AssemblyDoc)doc;
        Component2 a10 = null, a12 = null;
        foreach (var c in Comps(asm)) { if (c.Name2.StartsWith("A10")) a10 = c; if (c.Name2.StartsWith("A12")) a12 = c; }
        var cfg = (Configuration)doc.ConfigurationManager.ActiveConfiguration;
        Log("existing explode steps: " + cfg.GetNumberOfExplodeSteps());
        asm.CreateExplodedView();
        Step(doc, asm, new[] { "A11" }, a10, barY, 55, "pad A11 lifted out of the U", flip);
        Step(doc, asm, new[] { "M4_nut" }, a10, barY, 35, "M4 nuts lifted out of their slots", flip);
        Step(doc, asm, new[] { "M4x10" }, a10, barZ, 40, "set screws out of the far wall", flip);
        Step(doc, asm, new[] { "A12", "D01", "D02", "D03", "W00" }, a10, barZ, -35, "tilt block + display off the knuckle", flip);
        Step(doc, asm, new[] { "D01", "D02", "D03", "W00" }, a12, dispY, 45, "display slid up off the rail", flip);
        Step(doc, asm, new[] { "M5x25" }, a10, barZ, -75, "M5 bolt out", flip);
        Step(doc, asm, new[] { "M5_washer" }, a10, barZ, -65, "washer out", flip);
        Step(doc, asm, new[] { "M5_nyloc" }, a10, barZ, 30, "nyloc out", flip);
    }

    static void Close(ModelDoc2 d, AssemblyDoc asm)
    {
        d.ClearSelection2(true);
        foreach (var c in Comps(asm))
            if (c.Name2.StartsWith("A1") || c.Name2.StartsWith("W00") || c.Name2.StartsWith("D03") || c.Name2.StartsWith("D0") || c.Name2.StartsWith("M"))
                c.Select4(true, null, false);
        d.ViewZoomToSelection();
        d.ClearSelection2(true);
        d.GraphicsRedraw2();
        System.Threading.Thread.Sleep(2500);
    }

    static void Picture(ModelDoc2 doc, string path)
    {
        int e = 0, w = 0;
        bool ok = doc.Extension.SaveAs3(path, 0, (int)swSaveAsOptions_e.swSaveAsOptions_Silent | (int)swSaveAsOptions_e.swSaveAsOptions_Copy, null, null, ref e, ref w);
        Log("picture " + path + " ok=" + ok + " e=" + e);
    }

    public static void Run(string dir, string mode, double[] barY, double[] barZ, double[] dispY)
    {
        var sw = Attach();
        Log("SW " + sw.RevisionNumber() + " pid " + sw.GetProcessID());
        string main = Path.Combine(dir, "MD_showcase_on_Eino_arm.SLDASM");
        string exp = Path.Combine(dir, "MD_showcase_on_Eino_arm_exploded.SLDASM");
        string pics = Path.Combine(dir, "pictures");
        Directory.CreateDirectory(pics);
        bool buildOnly = mode == "build";
        if (buildOnly) mode = "all";
        if (mode == "all")
        {
            sw.CloseAllDocuments(true);
            foreach (var f in new[] { main, exp }) if (File.Exists(f)) File.Delete(f);
            var ex = Build(sw, dir, exp, true);
            ex.ShowNamedView2("*Isometric", 7); ex.ViewZoomtofit2(); int e1 = 0, w1 = 0; ex.Save3(1, ref e1, ref w1); sw.CloseDoc(ex.GetTitle());
            Build(sw, dir, main, false);
            mode = buildOnly ? "list" : "explode";
        }
        if (mode == "final")
        {
            int e0 = 0, w0 = 0;
            foreach (var f in new[] { exp, main })
            {
                var dd = sw.OpenDoc6(f, (int)swDocumentTypes_e.swDocASSEMBLY, 0, "", ref e0, ref w0);
                sw.ActivateDoc3(dd.GetTitle(), false, 0, ref e0);
                var aa = (AssemblyDoc)dd;
                foreach (var c in Comps(aa)) if (c.Name2.StartsWith("A11") || c.Name2.StartsWith("A10")) { var t = Rot(c); Log(Path.GetFileName(f) + " " + c.Name2 + " T=" + t[9].ToString("F4") + "," + t[10].ToString("F4") + "," + t[11].ToString("F4")); }
                dd.ShowNamedView2("*Isometric", 7); dd.ViewZoomtofit2(); dd.GraphicsRedraw2(); System.Threading.Thread.Sleep(3000);
                Picture(dd, Path.Combine(pics, Path.GetFileNameWithoutExtension(f) + "_whole.png"));
                Close(dd, aa);
                Picture(dd, Path.Combine(pics, Path.GetFileNameWithoutExtension(f) + "_clamp.png"));
                dd.ShowNamedView2("*Isometric", 7); dd.ViewZoomtofit2(); dd.GraphicsRedraw2();
                Log("open: " + dd.GetTitle() + " (" + Comps(aa).Length + " components)");
            }
            return;
        }
        var d = (ModelDoc2)sw.ActiveDoc;
        var asm = (AssemblyDoc)d;
        if (mode == "explode" || mode == "explode-flip")
        {
            Explode(d, barY, barZ, dispY, mode == "explode-flip");
            Component2 pad = null; foreach (var c in Comps(asm)) if (c.Name2.StartsWith("A11")) pad = c;
            var p0 = Pos(pad);
            asm.ShowExploded2(true, "");
            var p1 = Pos(pad);
            Log("pad moved (m): " + (p1[0]-p0[0]).ToString("F4") + " " + (p1[1]-p0[1]).ToString("F4") + " " + (p1[2]-p0[2]).ToString("F4")
                + "  expected along " + barY[0].ToString("F3") + " " + barY[1].ToString("F3") + " " + barY[2].ToString("F3"));
            d.ShowNamedView2("*Isometric", 7); Close(d, asm);
            Picture(d, Path.Combine(pics, "exploded_clamp.png"));
            asm.ShowExploded2(false, "");
            d.ShowNamedView2("*Isometric", 7); Close(d, asm);
            Picture(d, Path.Combine(pics, "assembled_clamp.png"));
            d.ShowNamedView2("*Isometric", 7); d.ViewZoomtofit2(); d.GraphicsRedraw2();
            Picture(d, Path.Combine(pics, "assembled_whole.png"));
            int e = 0, w = 0;
            d.Save3(1, ref e, ref w);
            Log("saved main e=" + e + " w=" + w);
        }
        if (mode == "pics")
        {
            asm.ShowExploded2(true, ""); d.ShowNamedView2("*Isometric", 7); Close(d, asm);
            Picture(d, Path.Combine(pics, "exploded_clamp.png"));
            asm.ShowExploded2(false, ""); d.ShowNamedView2("*Isometric", 7); Close(d, asm);
            Picture(d, Path.Combine(pics, "assembled_clamp.png"));
            mode = "show";
        }
        if (mode == "show")
        {
            d.ShowNamedView2("*Isometric", 7); d.ViewZoomtofit2(); d.GraphicsRedraw2(); System.Threading.Thread.Sleep(2500);
            Picture(d, Path.Combine(pics, "assembled_whole.png"));
            var mv = (ModelView)d.ActiveView;
            Log("view scale " + mv.Scale2 + " frame " + mv.FrameWidth + "x" + mv.FrameHeight);
        }
        if (mode == "probe")
        {
            string tpl = sw.GetUserPreferenceStringValue((int)swUserPreferenceStringValue_e.swDefaultTemplateAssembly);
            var ad = (ModelDoc2)sw.NewDocument(tpl, 0, 0, 0);
            var a2 = (AssemblyDoc)ad;
            string f1 = Path.Combine(dir, "parts", "Eino_P10_desk_helper.SLDPRT"), f2 = Path.Combine(dir, "parts", "A11_pressure_pad_PETG.SLDPRT");
            int e0 = 0, w0 = 0;
            var p1 = sw.OpenDoc6(f1, 1, 1, "", ref e0, ref w0); var p2 = sw.OpenDoc6(f2, 1, 1, "", ref e0, ref w0);
            var xf = new double[] { 1,0,0, 0,1,0, 0,0,1, 0,0,0, 1,0,0,0,  1,0,0, 0,1,0, 0,0,1, 0.1,0.2,0.3, 1,0,0,0 };
            var cs = (object[])a2.AddComponents3(new[] { f1, f2 }, xf, null);
            foreach (Component2 c in cs) { var t = Rot(c); Log("probe " + c.Name2 + " T=" + t[9] + "," + t[10] + "," + t[11]); }
            var c3 = a2.AddComponent5(f2, 0, "", false, "", 0.1, 0.2, 0.3);
            var t3 = Rot(c3); Log("probe AddComponent5 at 0.1,0.2,0.3 -> " + t3[9] + "," + t3[10] + "," + t3[11]);
            sw.CloseDoc(((ModelDoc2)p1).GetTitle()); sw.CloseDoc(((ModelDoc2)p2).GetTitle());
            sw.CloseDoc(ad.GetTitle());
            return;
        }
        if (mode == "list")
        {
            var bx = (double[])asm.GetBox(0);
            Log("asm box " + string.Join(",", Array.ConvertAll(bx, x => x.ToString("F3"))));
            foreach (var c in Comps(asm)) { var b = (double[])c.GetBox(false, false); var tt = Rot(c); Log("  " + c.Name2 + "  T=" + tt[9].ToString("F3") + "," + tt[10].ToString("F3") + "," + tt[11].ToString("F3") + "  R0=" + tt[0].ToString("F3") + "," + tt[1].ToString("F3") + "," + tt[2].ToString("F3") + "  box " + (b == null ? "-" : string.Join(",", Array.ConvertAll(b, x => x.ToString("F3"))))); }
            var mv = (ModelView)d.ActiveView;
            Log("frame " + mv.FrameWidth + "x" + mv.FrameHeight + " left " + mv.FrameLeft + " top " + mv.FrameTop + " state " + mv.FrameState);
        }
    }
}
