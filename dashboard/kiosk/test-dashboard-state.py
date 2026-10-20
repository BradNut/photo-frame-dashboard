#!/usr/bin/env python3
"""Run the kiosk's current-dashboard rules (src/.../DashboardState.java): which dashboard is
current, and which page loads, after each change the controls or adb make.

Requires Python 3 and a JDK on PATH. No Android device, SDK or third-party packages.
This checks the rules, not the dialogs, the WebView or SharedPreferences.
"""
from pathlib import Path
import subprocess
import tempfile


SRC = Path(__file__).resolve().parent / "src/com/wesbos/homehq"

HARNESS = r'''
package com.wesbos.homehq;

import java.util.Objects;

public class DashboardStateHarness {
  static final String DEF = "https://default.example/";
  static final String Y = "https://yuvomi.example.com/";
  static final String B = "http://192.168.1.20:8000/";
  static final String G = "https://grafana.example.com/d/abc?kiosk";

  static void check(String name, boolean ok) {
    if (!ok) throw new AssertionError(name);
    System.out.println("PASS " + name);
  }

  /** Yuvomi (current), Babybuddy, Grafana, as saved by an earlier kiosk run. */
  static DashboardState three() {
    return new DashboardState("Yuvomi\t" + Y + "\nBaby\t" + B + "\nGrafana\t" + G + "\n", Y, DEF);
  }

  public static void main(String[] args) {
    DashboardState updated = new DashboardState(null, Y, DEF);
    check("update: the saved URL is the current, only dashboard",
        updated.dashboards().size() == 1 && updated.isCurrent(0) && Y.equals(updated.savedUrl()));

    DashboardState s = three();
    check("switch: loads the picked dashboard and makes it current",
        B.equals(s.switchTo(1)) && s.isCurrent(1) && !s.isCurrent(0) && B.equals(s.savedUrl()));

    s = three();
    check("delete current: the first dashboard left loads and is current",
        B.equals(s.delete(0)) && s.dashboards().size() == 2 && s.isCurrent(0) && B.equals(s.savedUrl()));

    s = three();
    check("delete another: nothing reloads and the current one stays",
        s.delete(2) == null && s.dashboards().size() == 2 && s.isCurrent(0) && Y.equals(s.savedUrl()));

    s = new DashboardState(null, Y, DEF);
    check("delete the last one: the default page loads and no URL stays saved",
        DEF.equals(s.delete(0)) && s.dashboards().size() == 0 && s.savedUrl() == null);
    DashboardState rebooted = new DashboardState(s.storedList(), s.savedUrl(), DEF);
    check("an emptied list stays empty after a reboot", rebooted.dashboards().size() == 0);

    s = three();
    s.switchTo(2);
    s.delete(1);
    rebooted = new DashboardState(s.storedList(), s.savedUrl(), DEF);
    check("after a reboot: same dashboards, same current one",
        rebooted.dashboards().size() == 2 && "Grafana".equals(rebooted.dashboards().get(1).name)
            && rebooted.isCurrent(1));

    s = three();
    check("edit the current URL: the new URL loads and stays current",
        (Y + "overview").equals(s.edit(0, "Family", Y + "overview")) && s.isCurrent(0)
            && (Y + "overview").equals(s.savedUrl()) && "Family".equals(s.dashboards().get(0).name));

    s = three();
    check("edit another dashboard: nothing reloads and the current one stays",
        s.edit(1, "Baby Buddy", B + "timeline/") == null && s.isCurrent(0) && Y.equals(s.savedUrl())
            && (B + "timeline/").equals(s.dashboards().get(1).url));

    s = three();
    check("rename the current dashboard: nothing reloads",
        s.edit(0, "Family", Y) == null && s.isCurrent(0) && "Family".equals(s.dashboards().get(0).name));

    s = three();
    String n = "https://new.example/";
    check("add a typed URL: it goes last, loads and is current",
        n.equals(s.add("", n, Y)) && s.dashboards().size() == 4 && s.isCurrent(3) && n.equals(s.savedUrl()));

    s = three();
    String followed = "https://grafana.example.com/d/other";
    check("add the page on screen: nothing reloads, it is current",
        s.add("", followed, followed) == null && s.isCurrent(3) && followed.equals(s.savedUrl()));

    s = three();
    check("form: a URL already in the list is refused, naming the dashboard",
        "Already in the list as Baby".equals(s.problem(-1, B)));
    check("form: a new URL, or an edit keeping its own URL, can be saved",
        s.problem(-1, "https://new.example/") == null && s.problem(1, B) == null);
    check("form: a URL that isn't http or https is refused",
        "Start with http:// or https://".equals(s.problem(-1, "grafana.local"))
            && "Start with http:// or https://".equals(s.problem(0, "https://")));

    s = three();
    check("adb --es url with a new URL: added last, loads and is current",
        n.equals(s.saveFromAdb(n)) && s.dashboards().size() == 4 && s.isCurrent(3)
            && "new.example".equals(s.dashboards().get(3).name));
    check("adb --es url with a listed URL: no duplicate, it becomes current",
        G.equals(s.saveFromAdb(G)) && s.dashboards().size() == 4 && s.isCurrent(2));

    s = three();
    check("offline screen: a dashboard's URL is called by its name", "Baby".equals(s.nameFor(B)));
    check("offline screen: another page on the same site gets that dashboard's name",
        "Baby".equals(s.nameFor("http://192.168.1.20:8000/children/1/")));
    check("offline screen: a page on a site that isn't a dashboard has no name",
        s.nameFor("https://accounts.example.org/login") == null && s.nameFor("http://192.168.1.20:9000/") == null
            && s.nameFor(null) == null);
  }
}
'''

with tempfile.TemporaryDirectory(prefix="homehq-dashboard-state-") as directory:
    root = Path(directory)
    java = root / "DashboardStateHarness.java"
    java.write_text(HARNESS, encoding="utf-8")
    subprocess.run(["javac", "--release", "8", "-d", str(root), str(SRC / "Dashboards.java"),
                    str(SRC / "DashboardState.java"), str(java)], check=True, timeout=30)
    subprocess.run(["java", "-cp", str(root), "com.wesbos.homehq.DashboardStateHarness"],
                   check=True, timeout=30)
