#!/usr/bin/env python3
"""Run the kiosk's dashboard list (src/.../Dashboards.java) against the cases the controls rely on.

Requires Python 3 and a JDK on PATH. No Android device, SDK or third-party packages.
This checks the stored list, not the dialogs or the WebView.
"""
from pathlib import Path
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parent / "src/com/wesbos/homehq/Dashboards.java"

HARNESS = r'''
package com.wesbos.homehq;

public class DashboardsHarness {
  static void check(String name, boolean ok) {
    if (!ok) throw new AssertionError(name);
    System.out.println("PASS " + name);
  }

  public static void main(String[] args) {
    String y = "https://yuvomi.example.com/";
    String b = "http://192.168.1.20:8000/";
    String g = "https://www.grafana.example.com/d/abc?kiosk&refresh=1m";

    check("no list, no saved URL: empty", Dashboards.parse(null, null).size() == 0);
    Dashboards legacy = Dashboards.parse(null, y);
    check("no list: the saved URL becomes the first dashboard",
        legacy.size() == 1 && legacy.get(0).url.equals(y) && legacy.get(0).name.equals("yuvomi.example.com"));
    check("no list: a non-web saved URL is dropped", Dashboards.parse(null, "javascript:alert(1)").size() == 0);
    check("empty list stays empty, saved URL ignored", Dashboards.parse("", y).size() == 0);

    Dashboards d = Dashboards.parse("", null);
    d.add("Yuvomi", y);
    d.add("", b);
    d.add("  Grafana\tkitchen\n", g);
    check("blank name uses the host, without the port", d.get(1).name.equals("192.168.1.20"));
    check("tabs and newlines in a name become spaces", d.get(2).name.equals("Grafana kitchen"));
    check("www. is left off the default name", Dashboards.defaultName(g).equals("grafana.example.com"));

    Dashboards round = Dashboards.parse(d.serialize(), null);
    check("round trip keeps order, names and URLs (query included)",
        round.size() == 3 && round.get(0).name.equals("Yuvomi") && round.get(2).url.equals(g)
            && round.get(2).name.equals("Grafana kitchen"));
    check("stored list wins over the saved URL", Dashboards.parse(d.serialize(), "https://other/").size() == 3);

    check("addIfMissing finds an existing URL", d.addIfMissing(b) == 1 && d.size() == 3);
    check("addIfMissing appends a new URL", d.addIfMissing("https://new.example/") == 3 && d.size() == 4);

    d.set(0, "Family", y + "overview");
    check("edit replaces name and URL in place", d.get(0).name.equals("Family") && d.indexOf(y + "overview") == 0);
    d.remove(3);
    check("delete removes only that entry", d.size() == 3 && d.indexOf("https://new.example/") < 0);

    check("http and https accepted", Dashboards.isWebUrl(b) && Dashboards.isWebUrl("HTTPS://x"));
    check("other schemes and bare prefixes refused",
        !Dashboards.isWebUrl("file:///sdcard/x") && !Dashboards.isWebUrl("content://x")
            && !Dashboards.isWebUrl("https://") && !Dashboards.isWebUrl(null)
            && !Dashboards.isWebUrl("https://a\tb"));
    check("bad stored lines are skipped",
        Dashboards.parse("no tab here\nX\tjavascript:1\nOK\thttps://ok/\n", null).size() == 1);
  }
}
'''

with tempfile.TemporaryDirectory(prefix="homehq-dashboards-") as directory:
    root = Path(directory)
    java = root / "DashboardsHarness.java"
    java.write_text(HARNESS, encoding="utf-8")
    subprocess.run(["javac", "--release", "8", "-d", str(root), str(SOURCE), str(java)],
                   check=True, timeout=30)
    subprocess.run(["java", "-cp", str(root), "com.wesbos.homehq.DashboardsHarness"],
                   check=True, timeout=30)
