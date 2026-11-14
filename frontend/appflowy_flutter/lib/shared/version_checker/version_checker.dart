import 'package:appflowy/startup/tasks/device_info_task.dart';
import 'package:appflowy_backend/log.dart';
import 'package:auto_updater/auto_updater.dart';
import 'package:collection/collection.dart';
import 'package:http/http.dart' as http;
import 'package:universal_platform/universal_platform.dart';
import 'package:xml/xml.dart' as xml;

final versionChecker = VersionChecker();

/// Version checker class to handle update checks using appcast XML feeds
class VersionChecker {
  factory VersionChecker() => _instance;

  VersionChecker._internal();
  String? _feedUrl;

  static final VersionChecker _instance = VersionChecker._internal();

  bool get hasConfiguredUpdateFeed => _feedUrl != null;

  /// Sets the appcast XML feed URL
  void setFeedUrl(String url) {
    _feedUrl = url;

    if (UniversalPlatform.isWindows || UniversalPlatform.isMacOS) {
      autoUpdater.setFeedURL(url);
      // disable the auto update check
      autoUpdater.setScheduledCheckInterval(0);
    }
  }

  /// Checks for updates by fetching and parsing the appcast XML
  /// Returns a list of [AppcastItem] or throws an exception if the feed URL is not set
  Future<AppcastItem?> checkForUpdateInformation() async {
    if (_feedUrl == null) {
      Log.error('Feed URL is not set');
      return null;
    }

    try {
      final response = await http.get(Uri.parse(_feedUrl!));
      if (response.statusCode != 200) {
        Log.info('Failed to fetch appcast XML: ${response.statusCode}');
        return null;
      }

      // Parse XML content
      final document = xml.XmlDocument.parse(response.body);
      final items = document.findAllElements('item');

      // Convert XML items to AppcastItem objects
      return items
          .map(_parseAppcastItem)
          .nonNulls
          .firstWhereOrNull((e) => e.os == ApplicationInfo.os);
    } catch (e) {
      Log.info('Failed to check for updates: $e');
    }

    return null;
  }

  /// Check only a configured update channel. Linux downloads remain disabled
  /// until a verified GoreeCloud release destination is approved.

  Future<void> checkForUpdate() async {
    if (!hasConfiguredUpdateFeed) {
      Log.info('GoreeCloud update feed is not configured');
      return;
    }
    if (UniversalPlatform.isLinux) {
      // Linux downloads require a separately approved GoreeCloud release URL.
      Log.info('GoreeCloud Linux update destination is not configured');
      return;
    }
    await autoUpdater.checkForUpdates();
  }

  AppcastItem? _parseAppcastItem(xml.XmlElement item) {
    final enclosure = item.findElements('enclosure').firstOrNull;
    return AppcastItem.fromJson({
      'title': item.findElements('title').firstOrNull?.innerText,
      'versionString': item
          .findElements('sparkle:shortVersionString')
          .firstOrNull
          ?.innerText,
      'displayVersionString': item
          .findElements('sparkle:shortVersionString')
          .firstOrNull
          ?.innerText,
      'releaseNotesUrl':
          item.findElements('releaseNotesLink').firstOrNull?.innerText,
      'pubDate': item.findElements('pubDate').firstOrNull?.innerText,
      'fileURL': enclosure?.getAttribute('url') ?? '',
      'os': enclosure?.getAttribute('sparkle:os') ?? '',
      'criticalUpdate':
          enclosure?.getAttribute('sparkle:criticalUpdate') ?? false,
    });
  }
}
