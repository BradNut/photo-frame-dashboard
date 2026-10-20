package com.wesbos.homehq;

/**
 * Which dashboard is current, and which page to load after each change the controls or adb make.
 * MainActivity stores storedList() and savedUrl() and loads what each change returns. Plain Java
 * (no Android classes) so test-dashboard-state.py can run it on a computer.
 */
final class DashboardState {
  private final Dashboards dashboards;
  private String saved; // null: no dashboard chosen, the kiosk shows its default page
  private final String defaultUrl;

  DashboardState(String storedList, String savedUrl, String defaultUrl) {
    dashboards = Dashboards.parse(storedList, savedUrl);
    saved = savedUrl;
    this.defaultUrl = defaultUrl;
  }

  Dashboards dashboards() {
    return dashboards;
  }

  /** The list to keep in the "dashboards" pref. */
  String storedList() {
    return dashboards.serialize();
  }

  /** The URL to keep in the "url" pref, or null to remove it. */
  String savedUrl() {
    return saved;
  }

  boolean isCurrent(int i) {
    return dashboards.get(i).url.equals(saved);
  }

  /** Returns the URL to load. */
  String switchTo(int i) {
    saved = dashboards.get(i).url;
    return saved;
  }

  /** The name of the dashboard a page belongs to, for the offline screen; null if none. */
  String nameFor(String url) {
    int i = dashboards.indexOf(url);
    if (i >= 0) return dashboards.get(i).name;
    String site = Dashboards.site(url);
    for (Dashboards.Entry e : dashboards.entries()) {
      if (site != null && site.equals(Dashboards.site(e.url))) return e.name;
    }
    return null;
  }

  /** Why the add (index -1) or edit form can't save url, or null if it can. */
  String problem(int index, String url) {
    if (!Dashboards.isWebUrl(url)) return "Start with http:// or https://";
    int existing = dashboards.indexOf(url);
    if (existing < 0 || existing == index) return null;
    return "Already in the list as " + dashboards.get(existing).name;
  }

  /**
   * Adds a dashboard and makes it current. showing is the page on screen. Returns the URL to load,
   * or null when that page is the one added.
   */
  String add(String name, String url, String showing) {
    switchTo(dashboards.add(name, url));
    return url.equals(showing) ? null : url;
  }

  /** The "url" extra: adds url if it isn't a dashboard yet and makes it current. Returns it to load. */
  String saveFromAdb(String url) {
    return switchTo(dashboards.addIfMissing(url));
  }

  /** Returns the URL to load if the current dashboard's URL changed, else null. */
  String edit(int i, String name, String url) {
    boolean reload = isCurrent(i) && !url.equals(saved);
    dashboards.set(i, name, url);
    return reload ? switchTo(i) : null;
  }

  /**
   * Returns the URL to load: the first dashboard left (or the default page, if none is) when the
   * current one was deleted. Null when the page on screen stays.
   */
  String delete(int i) {
    boolean wasCurrent = isCurrent(i);
    dashboards.remove(i);
    if (!wasCurrent) return null;
    if (dashboards.size() > 0) return switchTo(0);
    saved = null;
    return defaultUrl;
  }
}
