package com.wesbos.homehq;

import java.net.URI;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * The dashboards the two-finger controls switch between, in the order they were added. Plain Java
 * (no Android classes) so test-dashboards.py can run it on a computer.
 *
 * Stored as one "name<TAB>url" line per dashboard. Web URLs can't hold a raw tab or newline, and
 * names have them replaced by spaces.
 */
final class Dashboards {
  static final class Entry {
    final String name, url;

    Entry(String name, String url) {
      this.name = name;
      this.url = url;
    }
  }

  private final List<Entry> entries = new ArrayList<>();

  /**
   * Reads the stored list. Before multiple dashboards existed (stored == null), the kiosk saved a
   * single URL; that becomes the first dashboard so an update changes nothing on screen.
   */
  static Dashboards parse(String stored, String legacyUrl) {
    Dashboards d = new Dashboards();
    if (stored == null) {
      if (isWebUrl(legacyUrl)) d.add("", legacyUrl);
      return d;
    }
    for (String line : stored.split("\n")) {
      int tab = line.indexOf('\t');
      if (tab < 0) continue;
      String url = line.substring(tab + 1);
      if (isWebUrl(url)) d.add(line.substring(0, tab), url);
    }
    return d;
  }

  String serialize() {
    StringBuilder out = new StringBuilder();
    for (Entry e : entries) out.append(e.name).append('\t').append(e.url).append('\n');
    return out.toString();
  }

  List<Entry> entries() {
    return Collections.unmodifiableList(entries);
  }

  int size() {
    return entries.size();
  }

  Entry get(int i) {
    return entries.get(i);
  }

  int indexOf(String url) {
    for (int i = 0; i < entries.size(); i++) {
      if (entries.get(i).url.equals(url)) return i;
    }
    return -1;
  }

  /** Adds a dashboard at the end; a blank name becomes the URL's host. Returns its index. */
  int add(String name, String url) {
    entries.add(new Entry(cleanName(name, url), url));
    return entries.size() - 1;
  }

  /** The index of the dashboard with this URL, adding it first if it isn't in the list. */
  int addIfMissing(String url) {
    int i = indexOf(url);
    return i >= 0 ? i : add("", url);
  }

  void set(int i, String name, String url) {
    entries.set(i, new Entry(cleanName(name, url), url));
  }

  void remove(int i) {
    entries.remove(i);
  }

  /** Only http and https: the activity is exported, so never file:, content: or javascript:. */
  static boolean isWebUrl(String url) {
    if (url == null || url.indexOf('\t') >= 0 || url.indexOf('\n') >= 0 || url.indexOf('\r') >= 0) return false;
    String lower = url.toLowerCase(Locale.ROOT);
    return (lower.startsWith("http://") || lower.startsWith("https://")) && url.length() > lower.indexOf("//") + 2;
  }

  /** The host without "www.", e.g. "yuvomi.example.com"; the whole URL if it has no host. */
  static String defaultName(String url) {
    try {
      String host = new URI(url).getHost();
      if (host == null || host.isEmpty()) return url;
      return host.startsWith("www.") ? host.substring(4) : host;
    } catch (Exception e) {
      return url;
    }
  }

  /** Scheme, host and port, e.g. "http://192.168.1.20:8000"; null if url has no host. */
  static String site(String url) {
    try {
      URI u = new URI(url);
      if (u.getHost() == null) return null;
      return u.getScheme().toLowerCase(Locale.ROOT) + "://" + u.getHost().toLowerCase(Locale.ROOT) + ":" + u.getPort();
    } catch (Exception e) {
      return null;
    }
  }

  private static String cleanName(String name, String url) {
    String n = name == null ? "" : name.replace('\t', ' ').replace('\n', ' ').replace('\r', ' ').trim();
    return n.isEmpty() ? defaultName(url) : n;
  }
}
